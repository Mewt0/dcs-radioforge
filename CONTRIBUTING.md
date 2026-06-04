# Contributing

Thanks for helping improve DCS RadioForge.

## Good First Contributions

- Better radio presets for specific aircraft, coalitions, or eras.
- More useful mission-line examples in `lines.csv`.
- UI copy improvements in Russian or English.
- Mission Editor usage notes from real DCS scenarios.
- Small bug fixes with a clear reproduction path.

## Local Setup

```powershell
.\setup.ps1
.\start_gui.ps1
```

Run a quick source check:

```powershell
python -m py_compile server.py voicekit.py
```

## Pull Request Checklist

- Keep generated audio, screenshots, and temporary files out of commits.
- Update `README.md` and `README_RU.md` when changing user-facing behavior.
- Update `CHANGELOG.md` for release-worthy changes.
- Verify that the GUI loads at `http://127.0.0.1:8765`.
- Test at least one generated OGG file in DCS Mission Editor when touching audio processing.
