# DCS RadioForge — one-command launch of the web studio with the optional
# local GPU TTS (XTTS via the external worker). Falls back to Edge-only if the
# XTTS pieces are not found, so the script never blocks a normal run.
#
# Usage:
#   .\start_gpu.ps1                              # start with XTTS (if configured)
#   .\start_gpu.ps1 -SpeakerWav D:\v\ref.wav      # explicit reference voice
#   .\start_gpu.ps1 -Port 9000 -NoOpen
#
# Expected layout (recommended: everything next to this script, in the repo root):
#   .venv-xtts\Scripts\python.exe            # Python 3.11 + coqui-tts
#   ffmpeg-shared\...\bin\                   # FFmpeg shared build (torchcodec)
#   ..\outputs\youtube_voice_reference_2\*.wav # reference voices (or -SpeakerWav)
# Full setup: docs/LOCAL_GPU_TTS_RU.md.

param(
    [string]$Address = "127.0.0.1",
    [int]$Port = 8765,
    [string]$SpeakerWav = "",
    [string]$XtVenv = "",
    [switch]$NoOpen
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Parent = Split-Path -Parent $Root

function Find-Path {
    param([string[]]$Candidates)
    foreach ($c in $Candidates) {
        if ($c -and (Test-Path -LiteralPath $c)) { return $c }
    }
    return $null
}

$MainPy = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $MainPy)) {
    Write-Host "ERROR: main venv not found: $MainPy (run setup.ps1 first)" -ForegroundColor Red
    exit 1
}

# --- optional local GPU TTS (XTTS) wiring --------------------------------------
$enabled = $false

$xtVenv = if ($XtVenv) { $XtVenv } else { Find-Path @((Join-Path $Root ".venv-xtts"), (Join-Path $Parent ".venv-xtts")) }
$xtPy = if ($xtVenv) { Join-Path $xtVenv "Scripts\python.exe" } else { $null }
$worker = Join-Path $Root "examples\external_tts\xtts_worker.py"
if ($xtPy -and (Test-Path -LiteralPath $xtPy) -and (Test-Path -LiteralPath $worker)) {
    $enabled = $true
} else {
    Write-Host "WARN: .venv-xtts not found - XTTS disabled (Edge only). See docs/LOCAL_GPU_TTS_RU.md." -ForegroundColor Yellow
}

$ffmpegDir = $null
if ($enabled) {
    $ffmpegDir = Find-Path @(
        (Join-Path $Root "ffmpeg-shared\ffmpeg-master-latest-win64-gpl-shared\bin"),
        (Join-Path $Parent "ffmpeg-shared\ffmpeg-master-latest-win64-gpl-shared\bin"),
        (Join-Path $Root "ffmpeg-shared\bin"),
        (Join-Path $Parent "ffmpeg-shared\bin")
    )
    if (-not $ffmpegDir) {
        Write-Host "WARN: ffmpeg-shared not found - torchcodec may fail on Windows. See docs/LOCAL_GPU_TTS_RU.md." -ForegroundColor Yellow
    }
}

$speaker = if ($SpeakerWav) { $SpeakerWav } else { Join-Path $Parent "outputs\youtube_voice_reference_2\yt2_ref_90s_intro_24k_mono.wav" }
if ($enabled -and -not (Test-Path -LiteralPath $speaker)) {
    Write-Host "WARN: reference voice not found: $speaker - pass -SpeakerWav to enable XTTS." -ForegroundColor Yellow
    $enabled = $false
}

if ($enabled) {
    if ($ffmpegDir) { $env:PATH = "$ffmpegDir;$env:PATH" }
    if (-not $env:COQUI_TOS_AGREED) { $env:COQUI_TOS_AGREED = "1" }
    if (-not $env:RF_EXTERNAL_TTS_ENABLED) { $env:RF_EXTERNAL_TTS_ENABLED = "1" }
    if (-not $env:RF_EXTERNAL_TTS_COMMAND) { $env:RF_EXTERNAL_TTS_COMMAND = '"' + $xtPy + '" "' + $worker + '"' }
    if (-not $env:RF_EXTERNAL_TTS_TIMEOUT) { $env:RF_EXTERNAL_TTS_TIMEOUT = "300" }
    if (-not $env:RF_EXTERNAL_TTS_VOICE_LABEL) { $env:RF_EXTERNAL_TTS_VOICE_LABEL = "XTTS GPU" }
    if (-not $env:RF_XTTS_SPEAKER_WAV) { $env:RF_XTTS_SPEAKER_WAV = $speaker }
    if (-not $env:RF_XTTS_DEVICE) { $env:RF_XTTS_DEVICE = "auto" }
    Write-Host "XTTS enabled: voice = $speaker" -ForegroundColor Green
} else {
    Write-Host "Starting without XTTS (Edge TTS available)." -ForegroundColor Yellow
}

# --- launch -------------------------------------------------------------------
$args = @("--host", $Address, "--port", "$Port")
if (-not $NoOpen) { $args += "--open" }
& $MainPy "server.py" @args
exit $LASTEXITCODE
