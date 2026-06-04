from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"
STAMP = VENV / ".radioforge-requirements.sha256"


def venv_python() -> Path:
    if os.name == "nt":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def requirements_hash() -> str:
    return hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest()


def run(command: list[str]) -> None:
    print("+ " + " ".join(command))
    subprocess.check_call(command, cwd=ROOT)


def ensure_venv() -> Path:
    python = venv_python()
    if not python.exists():
        run([sys.executable, "-m", "venv", str(VENV)])

    expected = requirements_hash()
    current = STAMP.read_text(encoding="utf-8").strip() if STAMP.exists() else ""
    if current != expected:
        run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
        run([str(python), "-m", "pip", "install", "-r", str(REQUIREMENTS)])
        STAMP.write_text(expected, encoding="utf-8")
    return python


def main() -> int:
    parser = argparse.ArgumentParser(description="Lazy launcher for DCS RadioForge.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", help="Open the browser after the server starts.")
    parser.add_argument("--in-venv", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if not args.in_venv:
        python = ensure_venv()
        command = [
            str(python),
            str(Path(__file__).resolve()),
            "--in-venv",
            "--host",
            args.host,
            "--port",
            str(args.port),
        ]
        if args.open:
            command.append("--open")
        return subprocess.call(command, cwd=ROOT)

    import server

    server_args = ["--host", args.host, "--port", str(args.port)]
    if args.open:
        server_args.append("--open")
    return server.main(server_args)


if __name__ == "__main__":
    raise SystemExit(main())
