@echo off
setlocal
rem Core build script for the songbook (Windows).
rem Usage: build.bat ^<a4^|a5^|all^|clean^> [--preview] [--no-index] [--custom-sort] [--indexes-only]

set "SCRIPT_DIR=%~dp0"
set "SRC_DIR=%SCRIPT_DIR%..\src"
set "RELEASE_DIR=%SCRIPT_DIR%..\release"

set "FORMAT="
set "PREVIEW=0"
set "INDEX=1"
set "CUSTOM_SORT=0"
set "INDEXES_ONLY=0"

:parse
if "%~1"=="" goto parsed
set "ARG=%~1"
if /i "%ARG%"=="a4" (
    set "FORMAT=a4"
) else if /i "%ARG%"=="a5" (
    set "FORMAT=a5"
) else if /i "%ARG%"=="all" (
    set "FORMAT=all"
) else if /i "%ARG%"=="clean" (
    set "FORMAT=clean"
) else if /i "%ARG%"=="--preview" (
    set "PREVIEW=1"
) else if /i "%ARG%"=="--no-index" (
    set "INDEX=0"
) else if /i "%ARG%"=="--custom-sort" (
    set "CUSTOM_SORT=1"
) else if /i "%ARG%"=="--indexes-only" (
    set "INDEXES_ONLY=1"
) else (
    echo Unknown argument: %ARG%
    goto usage
)
shift
goto parse

:parsed
if "%FORMAT%"=="" goto usage
if /i "%FORMAT%"=="clean" goto clean

rem Prefer the Python launcher, fall back to python on PATH.
where py >nul 2>nul && (set "PYTHON=py") || (set "PYTHON=python")

if not exist "%RELEASE_DIR%" mkdir "%RELEASE_DIR%"

if /i "%FORMAT%"=="a5" call :build songbook || goto failed
if /i "%FORMAT%"=="a4" call :build songbook_A4 || goto failed
if /i "%FORMAT%"=="all" (
    call :build songbook || goto failed
    call :build songbook_A4 || goto failed
)
echo.
echo Done.
exit /b 0

:failed
echo.
echo Build failed.
exit /b 1

:build
rem %1 = LaTeX job name (songbook = A5, songbook_A4 = A4)
set "JOB=%~1"
pushd "%SRC_DIR%"
echo.
echo === %JOB%: LuaLaTeX pass 1 ===
lualatex -interaction=nonstopmode "%JOB%.tex" || (popd & exit /b 1)
if "%INDEX%"=="1" (
    echo === %JOB%: generating song index ===
    songidx -l cs_CZ mainsongsindex.sxd mainsongsindex.sbx || (popd & exit /b 1)
    if "%CUSTOM_SORT%"=="1" (
        echo === %JOB%: applying custom Czech sort ===
        %PYTHON% "%SCRIPT_DIR%sort_index.py" || (popd & exit /b 1)
    )
) else (
    rem Without indexing a single pass is enough; keep the PDF from pass 1.
    goto finish
)
if "%INDEXES_ONLY%"=="1" (popd & exit /b 0)
echo === %JOB%: LuaLaTeX pass 2 ===
lualatex -interaction=nonstopmode "%JOB%.tex" || (popd & exit /b 1)
:finish
move /y "%JOB%.pdf" "%RELEASE_DIR%\%JOB%.pdf" >nul || (popd & exit /b 1)
popd
echo === %JOB%: PDF written to release\%JOB%.pdf ===
if "%PREVIEW%"=="1" start "" "%RELEASE_DIR%\%JOB%.pdf"
exit /b 0

:clean
del /q "%SRC_DIR%\*.aux" "%SRC_DIR%\*.log" "%SRC_DIR%\*.out" "%SRC_DIR%\*.sxc" "%SRC_DIR%\*.sbx" "%SRC_DIR%\*.sxd" 2>nul
echo Cleaned auxiliary files in src\.
exit /b 0

:usage
echo Usage: build.bat ^<a4^|a5^|all^|clean^> [options]
echo.
echo Formats:
echo   a4              build the A4 songbook (songbook_A4.pdf)
echo   a5              build the A5 songbook (songbook.pdf)
echo   all             build both formats
echo   clean           remove auxiliary build files from src\
echo.
echo Options:
echo   --preview       open the resulting PDF(s) after the build
echo   --no-index      single LuaLaTeX pass, skip index generation
echo   --custom-sort   post-process the index with sort_index.py (Czech sorting)
echo   --indexes-only  stop after generating the index (no final PDF)
exit /b 2
