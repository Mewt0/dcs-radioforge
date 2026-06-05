# GitHub Release Guide

This project is ready to publish as `dcs-radioforge`.

## Manual Git Flow

```powershell
git init
git add .
git commit -m "Release DCS RadioForge 0.1.2"
git branch -M main
git remote add origin https://github.com/YOUR_USER/dcs-radioforge.git
git push -u origin main
git tag v0.1.2
git push origin v0.1.2
```

Then create a GitHub release:

```powershell
gh release create v0.1.2 ..\dcs-radioforge-v0.1.2-source.zip ..\DCS-RadioForge-v0.1.2-windows-portable.zip --title "DCS RadioForge 0.1.2" --notes-file RELEASE_NOTES.md
```

## GitHub CLI One-Shot

If `gh` is installed and logged in:

```powershell
gh repo create dcs-radioforge --public --source . --remote origin --push
git tag v0.1.2
git push origin v0.1.2
gh release create v0.1.2 ..\dcs-radioforge-v0.1.2-source.zip ..\DCS-RadioForge-v0.1.2-windows-portable.zip --title "DCS RadioForge 0.1.2" --notes-file RELEASE_NOTES.md
```

Use `--private` instead of `--public` if you want to keep the repository private at first.

## After Publishing

Replace the static smoke-test badge in `README.md` with the real workflow badge:

```md
[![Smoke Test](https://github.com/YOUR_USER/dcs-radioforge/actions/workflows/smoke.yml/badge.svg)](https://github.com/YOUR_USER/dcs-radioforge/actions/workflows/smoke.yml)
```

Suggested repository topics:

```text
dcs-world, dcs, mission-editor, radio, voiceover, text-to-speech, srs-like, flight-sim
```
