# DCS RadioForge 0.1.4

This release adds ElevenLabs balance and generation cost visibility.

## Highlights

- Shows ElevenLabs subscription balance from `GET /v1/user/subscription`.
- Shows estimated character/credit cost for the selected line and all ElevenLabs lines.
- Captures actual `x-character-count` returned by ElevenLabs after TTS generation.
- Loads model cost multipliers from `GET /v1/models`.
- Windows portable EXE package still works without Python installed.

## Release Assets

- `DCS-RadioForge-v0.1.4-windows-portable.zip` - recommended Windows package.
- `dcs-radioforge-v0.1.4-source.zip` - source package with Python launchers.
- `dcs-radioforge-v0.1.4-demo-audio.zip` - optional generated audio examples.

## Notes

- Edge TTS remains the free default provider.
- ElevenLabs is optional and requires `ELEVENLABS_API_KEY`.
- API keys are used only by the local backend and are not exposed to browser code.
- If an API key was shared publicly, revoke it and create a new one before using the app.
- Windows may show a SmartScreen warning because the EXE is unsigned.
