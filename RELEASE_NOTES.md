# DCS RadioForge 0.1.1

This release adds the "lazy user" launch path and a ready-to-use Windows portable EXE package.

## Highlights

- Download-and-run Windows portable package with `DCS-RadioForge.exe`.
- Lazy Python launcher: `python run.py --open`.
- Double-click launcher for source installs: `Start_RadioForge.bat`.
- Local EXE build script: `build_windows_exe.ps1`.
- GitHub Actions workflow for future Windows EXE builds.
- EXE-safe output handling: generated files are written beside the executable into `build/dcs-ready`.

## Release Assets

- `DCS-RadioForge-v0.1.1-windows-portable.zip` - recommended for Windows users who do not want to set up Python.
- `dcs-radioforge-v0.1.1-source.zip` - source package with Python launchers.
- `dcs-radioforge-v0.1.1-demo-audio.zip` - optional generated audio examples.

## Notes

- Voice synthesis still requires internet access because `edge-tts` uses online Microsoft Edge voices.
- Windows may show a SmartScreen warning because the EXE is unsigned.
- DCS RadioForge is independent from DCS-SimpleRadio Standalone and does not include SRS code.
