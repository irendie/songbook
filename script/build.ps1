# Core build script for the songbook (Windows).
# Usage: build.ps1 <a4|a5|all|clean> [-Preview] [-NoIndex] [-NoCustomSort] [-IndexesOnly]
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("a4", "a5", "all", "clean")]
    [string]$Format,
    [switch]$Preview,      # open the resulting PDF(s) after the build
    [switch]$NoIndex,      # single LuaLaTeX pass, skip index generation
    [switch]$NoCustomSort, # skip sort_index.py post-processing (Czech sorting), enabled by default
    [switch]$IndexesOnly   # stop after generating the index (no final PDF)
)
$ErrorActionPreference = "Stop"

$SrcDir = Join-Path $PSScriptRoot "..\src"
$ReleaseDir = Join-Path $PSScriptRoot "..\release"

if (-not $Format) {
    Write-Host @"
Usage: build.ps1 <a4|a5|all|clean> [options]

Formats:
  a4              build the A4 songbook (songbook_A4.pdf)
  a5              build the A5 songbook (songbook.pdf)
  all             build both formats
  clean           remove auxiliary build files from src\

Options:
  -Preview        open the resulting PDF(s) after the build
  -NoIndex        single LuaLaTeX pass, skip index generation
  -NoCustomSort   skip sort_index.py post-processing (Czech sorting, on by default)
  -IndexesOnly    stop after generating the index (no final PDF)
"@
    exit 2
}

if ($Format -eq "clean") {
    Remove-Item -Path (Join-Path $SrcDir "*") `
        -Include *.aux, *.log, *.out, *.sxc, *.sbx, *.sxd -ErrorAction SilentlyContinue
    Write-Host "Cleaned auxiliary files in src\."
    exit 0
}

# Prefer the Python launcher, fall back to python on PATH.
$Python = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python" }

New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null

function Invoke-Build {
    param([string]$Job) # LaTeX job name (songbook = A5, songbook_A4 = A4)
    Push-Location $SrcDir
    try {
        Write-Host "`n=== ${Job}: LuaLaTeX pass 1 ==="
        lualatex -interaction=nonstopmode "$Job.tex"
        if ($LASTEXITCODE -ne 0) { throw "LuaLaTeX pass 1 failed for $Job" }

        if (-not $NoIndex) {
            Write-Host "=== ${Job}: generating song index ==="
            texlua (Join-Path $PSScriptRoot "songidx\songidx.lua") -l cs_CZ mainsongsindex.sxd mainsongsindex.sbx
            if ($LASTEXITCODE -ne 0) { throw "songidx failed for $Job" }

            if (-not $NoCustomSort) {
                Write-Host "=== ${Job}: applying custom Czech sort ==="
                & $Python (Join-Path $PSScriptRoot "sort_index.py")
                if ($LASTEXITCODE -ne 0) { throw "sort_index.py failed for $Job" }
            }
            if ($IndexesOnly) { return }

            Write-Host "=== ${Job}: LuaLaTeX pass 2 ==="
            lualatex -interaction=nonstopmode "$Job.tex"
            if ($LASTEXITCODE -ne 0) { throw "LuaLaTeX pass 2 failed for $Job" }
        }
        # Without indexing a single pass is enough; keep the PDF from pass 1.

        $pdf = Join-Path $ReleaseDir "$Job.pdf"
        Move-Item -Force "$Job.pdf" $pdf
        Write-Host "=== ${Job}: PDF written to release\$Job.pdf ==="
        if ($Preview) { Start-Process $pdf }
    }
    finally {
        Pop-Location
    }
}

try {
    switch ($Format) {
        "a5"  { Invoke-Build songbook }
        "a4"  { Invoke-Build songbook_A4 }
        "all" { Invoke-Build songbook; Invoke-Build songbook_A4 }
    }
}
catch {
    Write-Host "`nBuild failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`nDone."
