# Project Map

DCS RadioForge is intentionally small: a Python backend, a static browser UI, and a DCS-ready output folder generated at runtime.

```text
dcs-radioforge/
├─ web/
│  ├─ index.html       # Browser UI shell
│  ├─ app.js           # UI state, language strings, API calls
│  └─ styles.css       # DCS-inspired dark cockpit styling
├─ server.py           # Local HTTP API, voice generation, radio processing
├─ voicekit.py         # CSV batch generator
├─ lines.csv           # Example batch input
├─ setup.ps1           # Creates local virtual environment and installs deps
├─ start_gui.ps1       # Starts the local web studio
├─ generate.ps1        # Runs CSV batch generation
├─ requirements.txt    # Runtime dependencies
├─ README.md           # English GitHub front page
├─ README_RU.md        # Russian GitHub front page
├─ CHANGELOG.md        # Release history
├─ RELEASE_NOTES.md    # Notes for the current release
├─ docs/               # Guides and release checklist
└─ build/              # Generated locally, ignored by git
```

## Runtime Flow

```text
UI line editor
  -> POST /api/generate
  -> edge-tts MP3 synthesis
  -> ffmpeg radio processing
  -> OGG/WAV output in build/dcs-ready
  -> DCS Mission Editor trigger action
```

## Main Boundaries

- `server.py` owns the GUI API and SRS-like radio pack.
- `web/app.js` owns browser state, localization, role presets, and generation requests.
- `voicekit.py` is the simpler CSV workflow for batch generation.
- `build/` is disposable generated output and should not be committed.
