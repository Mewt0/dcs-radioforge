@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3 run.py --open
) else (
    python run.py --open
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo DCS RadioForge failed to start.
    pause
)
