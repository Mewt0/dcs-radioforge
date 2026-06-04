$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$BuildVenv = Join-Path $Root ".venv-build"
$BuildPython = Join-Path $BuildVenv "Scripts\python.exe"
$ReleaseDir = Join-Path $Root "release"
$PyInstallerWork = Join-Path $Root "build\pyinstaller"
$ExePath = Join-Path $ReleaseDir "DCS-RadioForge.exe"
$PortableZip = Join-Path $ReleaseDir "DCS-RadioForge-v0.1.1-windows-portable.zip"
$WebData = "$(Join-Path $Root "web");web"

function Remove-ProjectPath {
    param([string]$PathToRemove, [switch]$Recurse)

    $resolvedRoot = [System.IO.Path]::GetFullPath($Root)
    $resolvedTarget = [System.IO.Path]::GetFullPath($PathToRemove)
    if (-not $resolvedTarget.StartsWith($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove path outside project: $resolvedTarget"
    }
    if (Test-Path -LiteralPath $resolvedTarget) {
        if ($Recurse) {
            Remove-Item -LiteralPath $resolvedTarget -Recurse -Force
        } else {
            Remove-Item -LiteralPath $resolvedTarget -Force
        }
    }
}

if (-not (Test-Path -LiteralPath $BuildPython)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -3.11 -m venv $BuildVenv
    } else {
        python -m venv $BuildVenv
    }
}

& $BuildPython -m pip install --upgrade pip
& $BuildPython -m pip install -r (Join-Path $Root "requirements.txt")
& $BuildPython -m pip install -r (Join-Path $Root "requirements-build.txt")

New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null
New-Item -ItemType Directory -Force -Path $PyInstallerWork | Out-Null

& $BuildPython -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --console `
    --name "DCS-RadioForge" `
    --distpath $ReleaseDir `
    --workpath $PyInstallerWork `
    --specpath $PyInstallerWork `
    --add-data $WebData `
    --collect-binaries "imageio_ffmpeg" `
    --collect-data "edge_tts" `
    (Join-Path $Root "radioforge_launcher.py")

if (-not (Test-Path -LiteralPath $ExePath)) {
    throw "Build failed: $ExePath was not created"
}

Remove-ProjectPath -PathToRemove $PortableZip

$PortableRoot = Join-Path $ReleaseDir "DCS-RadioForge-v0.1.1-windows-portable"
Remove-ProjectPath -PathToRemove $PortableRoot -Recurse
New-Item -ItemType Directory -Force -Path $PortableRoot | Out-Null

Copy-Item -LiteralPath $ExePath -Destination (Join-Path $PortableRoot "DCS-RadioForge.exe")
Copy-Item -LiteralPath (Join-Path $Root "README.md") -Destination (Join-Path $PortableRoot "README.md")
Copy-Item -LiteralPath (Join-Path $Root "README_RU.md") -Destination (Join-Path $PortableRoot "README_RU.md")
Copy-Item -LiteralPath (Join-Path $Root "LICENSE") -Destination (Join-Path $PortableRoot "LICENSE")

Compress-Archive -Path $PortableRoot -DestinationPath $PortableZip

Write-Host "Built: $ExePath"
Write-Host "Portable package: $PortableZip"
