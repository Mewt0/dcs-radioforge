$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python)) {
    & (Join-Path $Root "setup.ps1")
}

& $Python (Join-Path $Root "server.py") --host 127.0.0.1 --port 8765
