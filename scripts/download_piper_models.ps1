# Downloads Piper voices (ONNX + json config) for DCS RadioForge.
# Not run automatically - execute manually when you want the local Piper provider.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\download_piper_models.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\download_piper_models.ps1 -ModelDir D:\piper\models
#
# Source: https://huggingface.co/rhasspy/piper-voices (main branch)

param(
    [string]$ModelDir = "piper-models"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
if ([System.IO.Path]::IsPathRooted($ModelDir)) {
    $Dest = $ModelDir
} else {
    $Dest = Join-Path $ProjectRoot $ModelDir
}
New-Item -ItemType Directory -Force -Path $Dest | Out-Null

$BaseUrl = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
$Voices = @(
    @{ Name = "ru_RU-denis-medium";  SubPath = "ru/ru_RU/denis/medium" },
    @{ Name = "ru_RU-irina-medium";  SubPath = "ru/ru_RU/irina/medium" },
    @{ Name = "en_US-ryan-medium";   SubPath = "en/en_US/ryan/medium" },
    @{ Name = "en_US-lessac-medium"; SubPath = "en/en_US/lessac/medium" }
)

foreach ($Voice in $Voices) {
    foreach ($Ext in ".onnx", ".onnx.json") {
        $Out = Join-Path $Dest ($Voice.Name + $Ext)
        if (Test-Path $Out) {
            Write-Host "skip: $Out"
            continue
        }
        $Url = "$BaseUrl/$($Voice.SubPath)/$($Voice.Name)$Ext"
        Write-Host "download: $Out"
        Invoke-WebRequest -Uri $Url -OutFile $Out
    }
}

Write-Host ""
Write-Host "Piper models are ready in: $Dest"
Write-Host "Point RF_PIPER_MODEL_DIR at this folder and set RF_PIPER_ENABLED=1 in .env"
