# Локальный GPU TTS через внешний процесс (XTTS / F5-TTS / Fish)

Тяжёлые GPU-движки
 (Coqui XTTS v2, F5-TTS, Fish Speech) требуют свой собственный
Python/torch и часто конфликтуют с версией Python основного приложения (например,
coqui TTS не работает на Python 3.14). Поэтому DCS RadioForge подключает их через
**универсальный external-провайдер**: основное приложение вызывает отдельную
команду/venv и получает готовый WAV.

Основной запуск без этой настройки не меняется: провайдер просто недоступен и
показывается в UI серым с причиной.

## Быстрый запуск

Если всё готово (`.venv-xtts`, `ffmpeg-shared`, reference-голос), запустите
студию одной командой из корня проекта:

```powershell
.\start_gpu.ps1
```

Скрипт сам найдёт `.venv-xtts` и `ffmpeg-shared` (в корне проекта или рядом),
подключит внешний провайдер и откроет браузер. Если чего-то не хватает — он
предупредит и запустит студию с Edge TTS. Голос по умолчанию — intro из
`outputs\youtube_voice_reference_2`; другой: `.\start_gpu.ps1 -SpeakerWav D:\path\ref.wav`.

## Свои reference-голоса

Положите `.wav`-файлы в папку `references/` в корне проекта (mono, 24 кГц,
15-30 секунд, без шумов и клиппинга) — они появятся в выпадающем списке голосов
у провайдера **Local GPU** после перезапуска сервера. Дополнительные папки —
через `RF_XTTS_VOICES_DIR` (несколько через `;`). Голос по умолчанию (когда
в UI ничего не выбрано) — `RF_XTTS_SPEAKER_WAV`. Файлы из `references/` не
коммитятся.

Транслитерация английских терминов (MASTER ARM, AGM-65, HUD и т.п.) применяется
**автоматически** к тексту перед синтезом — словарь в
`examples/external_tts/xtts_worker.py` (отключить: `RF_XTTS_TRANSLITERATE=0`).
Поэтому в миссиях можно писать термины латиницей — прозвучат по-русски.
Голос по умолчанию — `references\yt2_ref_90s_intro_24k_mono.wav`; остальные
референсы из `outputs\youtube_voice_reference_2` подключает
`start_gpu.ps1` через `RF_XTTS_VOICES_DIR`.

## Контракт

RadioForge запускает команду из `RF_EXTERNAL_TTS_COMMAND` и подаёт JSON на stdin:

```json
{ "text": "Текст реплики", "voice": "", "language": "ru", "output": "C:/tmp/out.wav" }
```

Команда обязана записать WAV-файл в путь `output` и завершиться с кодом 0.
Всё, что команда выведет в stderr при ошибке, попадёт в сообщение об ошибке.

## Настройка

```ini
RF_EXTERNAL_TTS_ENABLED=1
RF_EXTERNAL_TTS_COMMAND="C:\path\.venv-xtts\Scripts\python.exe" "C:\path\xtts_worker.py"
RF_EXTERNAL_TTS_TIMEOUT=120
RF_EXTERNAL_TTS_VOICE_LABEL=XTTS GPU
```

- `RF_EXTERNAL_TTS_COMMAND` — полная командная строка (кавычки поддерживаются).
- `RF_EXTERNAL_TTS_TIMEOUT` — секунды на синтез (по умолчанию 120).
- `RF_EXTERNAL_TTS_VOICE_LABEL` — как показывать провайдера в UI (по умолчанию "Local GPU").

## Пример worker для XTTS (отдельный venv)

Отдельный venv с Python 3.12 и CUDA-torch (не трогает основной `repo\.venv`):

```powershell
py -3.12 -m venv .venv-xtts
.\venv-xtts\Scripts\pip install torch --index-url https://download.pytorch.org/whl/cu126
.\venv-xtts\Scripts\pip install -r requirements-xtts.txt
```

Файл `xtts_worker.py`:

```python
"""XTTS worker for DCS RadioForge external provider.

Reads {text, voice, language, output} from stdin and writes WAV to output.
Run it with the venv that has torch + TTS installed (not the main app venv).
"""

import json
import sys


def main() -> None:
    payload = json.load(sys.stdin)
    text = payload["text"]
    output = payload["output"]
    language = payload.get("language") or "en"
    speaker_wav = r"C:\path\to\reference_voice.wav"  # ваш reference голос

    from TTS.api import TTS

    model = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", device="auto")
    model.tts_to_file(text=text, speaker_wav=speaker_wav, language=language, file_path=output)


if __name__ == "__main__":
    main()
```

Настройка в `.env`:

```ini
RF_EXTERNAL_TTS_ENABLED=1
RF_EXTERNAL_TTS_COMMAND="C:\project\.venv-xtts\Scripts\python.exe" "C:\project\xtts_worker.py"
RF_EXTERNAL_TTS_TIMEOUT=180
RF_EXTERNAL_TTS_VOICE_LABEL=XTTS GPU
```

## Проверка

1. Запустите сервер.
2. `GET /api/tts/providers` — у `external` должно быть `"available": true`.
3. Кнопка «Проверить голос» в редакторе (провайдер Local GPU) или
   `POST /api/tts/preview` с `provider: "external"`.

## Ошибки (structured codes)

- `external_disabled` — `RF_EXTERNAL_TTS_ENABLED` не равен 1.
- `external_command_missing` — `RF_EXTERNAL_TTS_COMMAND` пуст.
- `external_command_failed` — команда завершилась с ненулевым кодом (или не записала WAV).
- `external_timeout` — команда не уложилась в `RF_EXTERNAL_TTS_TIMEOUT`.