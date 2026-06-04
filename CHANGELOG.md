# Changelog

All notable changes to DCS RadioForge are documented here.

## 0.1.1 - 2026-06-04

### Added

- Lazy Windows launcher: `Start_RadioForge.bat`.
- Lazy Python launcher: `python run.py --open`.
- PyInstaller entry point for a one-file Windows executable.
- Local build script: `build_windows_exe.ps1`.
- GitHub Actions workflow for Windows EXE artifacts.
- Frozen-app path handling so generated DCS audio is written beside the EXE instead of inside a temporary bundle.

## 0.1.0 - 2026-06-04

### Added

- Local Russian and English browser UI.
- Edge TTS voice generation for Russian and English mission lines.
- DCS-ready OGG and WAV export.
- SRS-like radio preset pack:
  - Clean studio
  - SRS VHF AM
  - SRS UHF AM
  - SRS FM
  - SRS cockpit mic
  - SRS AWACS
  - SRS bad reception
  - Old Soviet radio
- Signal quality control for weak reception, added noise, and dirtier tails.
- Optional mic clicks and transmission tail processing.
- GUI manifest output for generated lines.
- Batch CSV workflow through `lines.csv` and `generate.ps1`.
- Russian and English documentation.
- GitHub issue templates, pull request template, and smoke-test workflow.
