$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python)) {
    & (Join-Path $Root "setup.ps1")
}

& $Python (Join-Path $Root "voicekit.py") generate `
    --input (Join-Path $Root "lines.csv") `
    --out (Join-Path $Root "build") `
    --format both `
    --sample-rate 22050
