# Локальный TTS на Piper (offline, CPU)

[Piper](https://github.com/rhasspy/piper) — локальный нейро-TTS на ONNX Runtime,
работает на CPU без интернета. В DCS RadioForge он добавлен как опциональный
провайдер `piper` рядом с `edge` и `elevenlabs`; по умолчанию выключен и
ничего не ломает, если не установлен.

## 1. Установка зависимости

```powershell
.venv\Scripts\pip install -r requirements-piper.txt
```

Ставится пакет `piper-tts` (тянет за собой onnxruntime и numpy — только CPU).

## 2. Скачивание моделей

Модели **не входят в репозиторий** (файлы .onnx большие). Скачайте их в папку,
которую укажете в `RF_PIPER_MODEL_DIR` (по умолчанию `piper-models` в корне
проекта). У каждого голоса два файла:

- `<voice>.onnx`
- `<voice>.onnx.json`

### Вариант А: готовый скрипт

```powershell
powershell -ExecutionPolicy Bypass -File scripts\download_piper_models.ps1
# или с другой папкой:
powershell -ExecutionPolicy Bypass -File scripts\download_piper_models.ps1 -ModelDir D:\piper\models
```

### Вариант Б: вручную с HuggingFace (rhasspy/piper-voices)

| Голос | URL (скачать `.onnx` и `.onnx.json`) |
|---|---|
| ru_RU-denis-medium | https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/denis/medium/ru_RU-denis-medium.onnx |
| ru_RU-irina-medium | https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/irina/medium/ru_RU-irina-medium.onnx |
| en_US-ryan-medium | https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx |
| en_US-lessac-medium | https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx |

У каждого голоса дополнительно скачайте файл с тем же именем и суффиксом
`.onnx.json` (конфиг с длиной кадра и т.п.). Пример структуры папки:

```text
piper-models/
  ru_RU-denis-medium.onnx
  ru_RU-denis-medium.onnx.json
  ru_RU-irina-medium.onnx
  ru_RU-irina-medium.onnx.json
  en_US-ryan-medium.onnx
  en_US-ryan-medium.onnx.json
```

## 3. Настройка (.env)

Добавьте в `.env` (пример уже есть в `.env.example`):

```ini
RF_PIPER_ENABLED=1
RF_PIPER_MODEL_DIR=piper-models
RF_PIPER_DEFAULT_VOICE=ru_RU-denis-medium
```

- `RF_PIPER_ENABLED=1` — включить провайдер.
- `RF_PIPER_MODEL_DIR` — папка с моделями (относительно корня проекта или абсолютный путь).
- `RF_PIPER_DEFAULT_VOICE` — голос по умолчанию, если в запросе не указан `voice`.

## 4. Проверка

Запустите сервер и откройте `GET /api/tts/providers`:

```json
{
  "providers": {
    "edge": { "available": true },
    "elevenlabs": { "configured": false },
    "piper": { "available": true, "model_dir": "...", "default_voice": "ru_RU-denis-medium", "voices": ["ru_RU-denis-medium", "ru_RU-irina-medium", "en_US-ryan-medium"] }
  }
}
```

## 5. Использование в API

Тот же формат, что и у других провайдеров, только `provider: "piper"`:

```json
POST /api/generate
{
  "items": [
    { "provider": "piper", "voice": "ru_RU-denis-medium", "text": "Привет, это локальный голос." }
  ]
}
```

Piper синтезирует WAV напрямую; дальше он проходит тот же ffmpeg-конвейер
(радио-пресеты), поэтому финальные `wav`/`ogg` и manifest не отличаются от
Edge/ElevenLabs. Если `piper` запрошен, но не установлен/не настроен — вернётся
понятная ошибка `Piper provider is unavailable: ...`, а Edge/ElevenLabs
продолжат работать как раньше.

## Примечания

- Используется классический API `piper.PiperVoice.load(model, config_path)` +
  `voice.synthesize(text, wav_file)` (piper-tts 1.2+). Если пакет обновится и
  API изменится, тесты (`tests/test_piper_provider.py`) покажут расхождение.
- GPU-модели (vits-piper с CUDA) пока не поддерживаются — только CPU.
