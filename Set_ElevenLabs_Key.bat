@echo off
setlocal
cd /d "%~dp0"

echo Paste your ElevenLabs API key. It will be saved to .env next to this file.
echo Do not commit .env to GitHub.
set /p RF_ELEVEN_KEY=ElevenLabs API key: 

if "%RF_ELEVEN_KEY%"=="" (
    echo No key entered.
    pause
    exit /b 1
)

> ".env" echo ELEVENLABS_API_KEY=%RF_ELEVEN_KEY%
echo.
echo Saved .env. Restart DCS RadioForge if it is already running.
pause
