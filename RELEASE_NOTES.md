# DCS RadioForge 0.1.0

First public release of DCS RadioForge: a local tool for building DCS World mission voiceovers with SRS-like radio processing.

## Highlights

- Russian and English UI.
- Russian and English tactical voices through Edge TTS.
- DCS-ready `.ogg` and `.wav` export.
- SRS-like presets for VHF, UHF, FM, cockpit, AWACS, bad reception, and old Soviet radio.
- Signal quality slider, mic clicks, and transmission tails.
- Batch CSV mode for mission creators who prefer spreadsheet-style line lists.

## Recommended Release Assets

Attach these files to a GitHub release:

- `dcs-radioforge-v0.1.0-source.zip` - clean source package.
- Optional example audio pack generated locally, if you want to demonstrate the sound.

Do not upload `build/` as repository source. Generated files should stay as release/demo artifacts only.

## Known Notes

- Voice synthesis requires internet access because `edge-tts` talks to Microsoft Edge online voices.
- DCS RadioForge is independent from DCS-SimpleRadio Standalone and does not include SRS code.
- OGG is recommended for missions because it keeps `.miz` size smaller.
