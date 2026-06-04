# DCS RadioForge

[![Smoke Test](https://github.com/Mewt0/dcs-radioforge/actions/workflows/smoke.yml/badge.svg)](https://github.com/Mewt0/dcs-radioforge/actions/workflows/smoke.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![DCS](https://img.shields.io/badge/DCS-Mission%20Editor-orange)
![License](https://img.shields.io/badge/license-MIT-green)

**DCS RadioForge** is a local radio voiceover generator for DCS World mission builders. Write mission lines in Russian or English, pick a tactical voice, add SRS-like radio processing, and export DCS-ready `.ogg` / `.wav` files for the Mission Editor.

> Russian documentation: [README_RU.md](README_RU.md)

The current audio pack is **SRS-like**: it does not use SRS code and is not an SRS mod. It recreates the feel of practical DCS comms with narrowband filtering, compression, signal noise, mic clicks, and squelch tails.

## Flight Deck

- Russian and English browser UI.
- Russian voices: `ru-RU-DmitryNeural`, `ru-RU-SvetlanaNeural`.
- English tactical voices for AWACS, JTAC, flight lead, FAC, briefing, and coalition ops.
- SRS-like presets: clean, VHF AM, UHF AM, FM, cockpit mic, AWACS, bad reception, old Soviet radio.
- Signal quality slider for controlled noise, weak reception, and dirty transmission tails.
- Optional mic clicks for push-to-talk flavor.
- DCS-ready `.ogg` and `.wav` export into `build/dcs-ready`.
- No paid API key required. Uses `edge-tts` and the ffmpeg binary bundled with `imageio-ffmpeg`.

## Quick Start

```powershell
.\setup.ps1
.\start_gui.ps1
```

Open the local studio:

```text
http://127.0.0.1:8765
```

Switch language:

```text
http://127.0.0.1:8765/?lang=en
http://127.0.0.1:8765/?lang=ru
```

## DCS Mission Editor

1. Generate `.ogg` or `.wav` lines in the UI.
2. Open your mission in DCS Mission Editor.
3. Add a trigger action: `SOUND TO ALL`, `SOUND TO GROUP`, or `RADIO TRANSMISSION`.
4. Select the generated file from `build/dcs-ready`.
5. Add `MESSAGE TO ALL/GROUP` on the same trigger if you want subtitles.

Use OGG for normal mission packs because it keeps `.miz` files smaller.

## Radio Presets

| Preset | Best for |
| --- | --- |
| Clean studio | Clean source for later editing |
| SRS VHF AM | JTAC, FAC, low altitude package comms |
| SRS UHF AM | Fighter package radio |
| SRS FM | Ground forces, helicopters, low-level work |
| SRS cockpit mic | Helmet mic / flight member calls |
| SRS AWACS | Command voice, GCI, picture calls |
| SRS bad reception | Weak, masked, distant transmissions |
| Old Soviet radio | Russian GCI, older ground units |

Lower the signal quality slider for weaker reception, more hiss, and a dirtier tail. Keep mic clicks enabled when the line should feel like a real push-to-talk transmission.

## Batch Mode

The GUI is the main workflow. Batch generation is also available through `lines.csv`:

```powershell
.\generate.ps1
```

## Project Map

- [Project map](docs/PROJECT_MAP.md)
- [DCS usage guide](docs/DCS_MISSION_EDITOR.md)
- [Audio preset guide](docs/RADIO_PRESETS.md)
- [Release checklist](docs/RELEASE_CHECKLIST.md)
- [GitHub release guide](docs/GITHUB_RELEASE.md)
- [Changelog](CHANGELOG.md)
- [Release notes](RELEASE_NOTES.md)

## Disclaimer

DCS World is a trademark of Eagle Dynamics SA. SRS / DCS-SimpleRadio Standalone belongs to its respective authors. DCS RadioForge is an independent helper tool and is not affiliated with Eagle Dynamics or SRS.
