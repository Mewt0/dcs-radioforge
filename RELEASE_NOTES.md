# DCS RadioForge 0.1.3

This release updates the ElevenLabs integration against the current official API reference.

## Highlights

- Voice list loading now uses `GET /v2/voices`.
- Voice list pagination is supported for larger ElevenLabs accounts.
- Text to Speech remains on `POST /v1/text-to-speech/:voice_id`.
- Voice Design remains on `POST /v1/text-to-voice/design`.
- Saving generated voices remains on `POST /v1/text-to-voice`.
- Windows portable EXE package still works without Python installed.

## Release Assets

- `DCS-RadioForge-v0.1.3-windows-portable.zip` - recommended Windows package.
- `dcs-radioforge-v0.1.3-source.zip` - source package with Python launchers.
- `dcs-radioforge-v0.1.3-demo-audio.zip` - optional generated audio examples.

## Notes

- Edge TTS remains the free default provider.
- ElevenLabs is optional and requires `ELEVENLABS_API_KEY`.
- API keys are used only by the local backend and are not exposed to browser code.
- If an API key was shared publicly, revoke it and create a new one before using the app.
- Windows may show a SmartScreen warning because the EXE is unsigned.
