# DCS RadioForge 0.1.2

This release adds optional ElevenLabs support for unique mission voices.

## Highlights

- ElevenLabs provider for RU/EN text-to-speech.
- Voice Lab panel for creating synthetic voice previews from descriptions.
- Save selected Voice Design previews into your ElevenLabs account.
- `Set_ElevenLabs_Key.bat` for local API key setup.
- `.env.example` for manual setup.
- Windows portable EXE package still works without Python.

## Release Assets

- `DCS-RadioForge-v0.1.2-windows-portable.zip` - recommended Windows package.
- `dcs-radioforge-v0.1.2-source.zip` - source package with Python launchers.
- `dcs-radioforge-v0.1.2-demo-audio.zip` - optional generated audio examples.

## Notes

- Edge TTS remains the free default provider.
- ElevenLabs is optional and requires `ELEVENLABS_API_KEY`.
- If an API key was shared publicly, revoke it and create a new one before using the app.
- Windows may show a SmartScreen warning because the EXE is unsigned.
