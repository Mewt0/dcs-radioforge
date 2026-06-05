# Чеклист релиза

Используй перед публикацией на GitHub.

## Исходники

- [ ] `README.md` и `README_RU.md` описывают текущий интерфейс.
- [ ] `CHANGELOG.md` содержит запись релиза.
- [ ] `RELEASE_NOTES.md` совпадает с версией тега.
- [ ] `build/`, `.venv/`, `__pycache__/` и сгенерированные аудио не попали в коммит.
- [ ] `requirements.txt` совпадает с `pyproject.toml`.

## Smoke test

```powershell
python -m py_compile server.py voicekit.py
```

```powershell
.\setup.ps1
.\start_gui.ps1
```

Открыть:

```text
http://127.0.0.1:8765/?lang=ru
http://127.0.0.1:8765/?lang=en
```

Сгенерировать хотя бы один OGG:

- русский голос;
- английский голос;
- чистый пресет;
- грязный SRS-like пресет.

## GitHub Release

- [ ] Tag: `v0.1.3`
- [ ] Title: `DCS RadioForge 0.1.3`
- [ ] Attach clean source archive.
- [ ] Attach Windows portable EXE archive.
- [ ] Confirm `.env` is ignored and no API key is committed.
- [ ] Optional: attach a small demo audio pack.
- [ ] Mention that voice generation requires internet access.
