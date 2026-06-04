# Release Checklist

Use this before publishing a GitHub release.

## Source

- [ ] `README.md` and `README_RU.md` describe the current UI.
- [ ] `CHANGELOG.md` has the release entry.
- [ ] `RELEASE_NOTES.md` matches the tag version.
- [ ] `build/`, `.venv/`, `__pycache__/`, and generated audio are not committed.
- [ ] `requirements.txt` matches `pyproject.toml`.

## Smoke Test

```powershell
python -m py_compile server.py voicekit.py
```

```powershell
.\setup.ps1
.\start_gui.ps1
```

Open:

```text
http://127.0.0.1:8765/?lang=ru
http://127.0.0.1:8765/?lang=en
```

Generate at least one OGG with:

- Russian voice.
- English voice.
- One clean preset.
- One dirty SRS-like preset.

## GitHub Release

- [ ] Tag: `v0.1.0`
- [ ] Title: `DCS RadioForge 0.1.0`
- [ ] Attach clean source archive.
- [ ] Optional: attach a small demo audio pack.
- [ ] Mention that voice generation requires internet access.
