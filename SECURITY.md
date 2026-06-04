# Security Policy

DCS RadioForge is a local desktop helper for mission builders. It starts a local HTTP server bound to `127.0.0.1` by default and writes generated audio into the local `build/` directory.

## Reporting

Please open a private security advisory on GitHub if the repository is public, or create an issue without sensitive details and ask for a maintainer contact.

## Notes

- Do not expose the local server to the internet.
- Do not run scripts from untrusted forks without reviewing them.
- Voice synthesis uses the online Edge TTS service through `edge-tts`, so generated text is sent to that service during synthesis.
