# Sets up a NixOS WSL distro (NixOS-WSL) ready to build the songbook.
# Run from an elevated or normal PowerShell:  .\script\setup_nixos_wsl.ps1
# Prerequisite (one-time, admin + reboot):    wsl --install --no-distribution
$ErrorActionPreference = "Stop"

$DistroName = "NixOS"
$InstallDir = Join-Path $env:LOCALAPPDATA "WSL\NixOS"
$ReleaseUrl = "https://github.com/nix-community/NixOS-WSL/releases/latest/download/nixos.wsl"

# 1. Verify WSL itself is installed
wsl.exe --status *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "WSL is not installed. Run this once from an elevated PowerShell, then reboot:" -ForegroundColor Yellow
    Write-Host "    wsl --install --no-distribution" -ForegroundColor Yellow
    exit 1
}

# 2. Skip import if the distro already exists
$existing = (wsl.exe --list --quiet) -replace "`0", "" | Where-Object { $_ -eq $DistroName }
if ($existing) {
    Write-Host "Distro '$DistroName' is already registered, skipping import."
} else {
    $tarball = Join-Path $env:TEMP "nixos.wsl"
    Write-Host "Downloading NixOS-WSL image..."
    Invoke-WebRequest -Uri $ReleaseUrl -OutFile $tarball

    Write-Host "Importing '$DistroName' into $InstallDir ..."
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    wsl.exe --import $DistroName $InstallDir $tarball --version 2
    if ($LASTEXITCODE -ne 0) { throw "wsl --import failed." }
    Remove-Item $tarball -ErrorAction SilentlyContinue
}

# 3. First boot + sanity check
Write-Host "Checking Nix inside the distro..."
wsl.exe -d $DistroName -- nix-shell --version
if ($LASTEXITCODE -ne 0) { throw "NixOS distro did not start correctly." }

Write-Host ""
Write-Host "Done. Build the songbook with:" -ForegroundColor Green
Write-Host "    wsl -d $DistroName"
Write-Host "    cd /mnt/c/Repos/songbook   # or wherever the repo lives"
Write-Host "    nix-shell --run './script/build.sh all --custom-sort'"
