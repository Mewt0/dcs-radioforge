# XTTS worker для внешнего TTS-провайдера (examples/external_tts)

Этот worker подключает Coqui XTTS v2 (и похожие движки) к DCS RadioForge через
универсальный external-провайдер. Работает **в отдельном venv** — не трогает
основной `repo\.venv` и не зависит от его версии Python.

> **Проверенный Windows-стек** (см. «Установка»): Python 3.11 + `coqui-tts` 0.27.5
> (поддерживаемый форк; PyPI-пакет `TTS` 0.22 на Windows требует сборки C-кода
> и не работает на Python 3.12+) + torch/torchaudio cu126 + torchcodec + FFmpeg
> shared. Реальная задержка на GTX 1060 — **примерно 30–35 секунд** на короткую
> фразу (после первого запуска, когда модель уже скачана).

## Контракт

RadioForge запускает worker и подаёт JSON на stdin:

```json
{ "text": "Текст реплики", "voice": "", "language": "ru", "output": "C:/tmp/out.wav" }
```

Worker обязан записать WAV в `output` и завершиться с кодом 0; при ошибке —
понятное сообщение в stderr и ненулевой код выхода.

Параметры:

| Поле | Значение |
|---|---|
| `text` | текст реплики (обязательно) |
| `voice` | опционально: путь к reference-wav (если не задан `RF_XTTS_SPEAKER_WAV`) |
| `language` | `ru`/`en` (опционально; иначе определяется по тексту) |
| `output` | путь к выходному WAV (обязательно) |

Env-переменные worker'а:

| Переменная | Значение |
|---|---|
| `RF_XTTS_SPEAKER_WAV` | путь к reference-голосу (обязателен, если `voice` не путь) |
| `RF_XTTS_MODEL` | модель (по умолчанию `tts_models/multilingual/multi-dataset/xtts_v2`) |
| `RF_XTTS_DEVICE` | `auto` / `cuda` / `cpu` (по умолчанию `auto`) |

## Установка (Windows, Python 3.11 в отдельном venv)

Python 3.12+ не подходит: coqui `TTS`/`coqui-tts` рассчитаны на Python < 3.12.
Проверено на Python 3.11.9 + torch 2.13.0+cu126 + GTX 1060 (Pascal, CC 6.1).

```powershell
py -3.11 -m venv .venv-xtts
.\venv-xtts\Scripts\python -m pip install --upgrade pip

# 1) CUDA torch + torchaudio ОДНИМ шагом (версии должны совпадать):
.\venv-xtts\Scripts\pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu126
# если cu126-колеса не поддерживают вашу видеокарту — попробуйте cu121

# 2) coqui-tts (форк) + закреплённые зависимости:
.\venv-xtts\Scripts\pip install -r ..\..\requirements-xtts.txt

# 3) FFmpeg shared DLL (нужны torchcodec'у на Windows): распакуйте shared-сборку
#    (например, BtbN/FFmpeg-Builds ffmpeg-master-latest-win64-gpl-shared.zip)
#    и добавьте её bin в PATH процесса сервера/worker'а.

# 4) Лицензия coqui (CPML, некоммерческая): при первом запуске модели нужен
#    неинтерактивный ответ — переменная окружения для worker'а/сервера:
#    COQUI_TOS_AGREED=1
```

Проверка CUDA:

```powershell
.\venv-xtts\Scripts\python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

Проверка импорта TTS:

```powershell
.\venv-xtts\Scripts\python -c "import TTS; print('TTS OK')"
```

## Настройка основного приложения

В `.env` (или переменные окружения сессии) укажите команду и reference-голос:

```ini
RF_EXTERNAL_TTS_ENABLED=1
RF_EXTERNAL_TTS_COMMAND="C:\project\.venv-xtts\Scripts\python.exe" "C:\project\repo\examples\external_tts\xtts_worker.py"
RF_EXTERNAL_TTS_TIMEOUT=300
RF_EXTERNAL_TTS_VOICE_LABEL=XTTS GPU
RF_XTTS_SPEAKER_WAV=C:\Users\Vlad\Documents\Codex\2026-08-23\https-github-com-mewt0-dcs-radioforge\outputs\voice_reference\voice_ref_full_24k_mono.wav
```

`RF_XTTS_SPEAKER_WAV` наследуется worker-процессом из окружения сервера, поэтому
задавать её повторно внутри `RF_EXTERNAL_TTS_COMMAND` не нужно. Таймаут 300 с
учитывает загрузку модели в первый раз.

## Проверка

1. Запустите сервер: `python server.py`.
2. `GET /api/tts/providers` — у `external` должно быть `"available": true`.
3. Кнопка «Проверить голос» в редакторе (провайдер Local GPU) или
   `POST /api/tts/preview` c `provider: "external"`.
4. Готовые файлы — как обычно в `build/dcs-ready`.

## Самотест worker'а (без запуска сервера)

```powershell
$env:COQUI_TOS_AGREED = "1"
$env:RF_XTTS_SPEAKER_WAV = "C:\path\to\reference.wav"
$env:PATH = "C:\path\ffmpeg-shared\bin;$env:PATH"
echo '{"text": "Привет", "voice": "", "language": "ru", "output": "C:/tmp/xtts_test.wav"}' |
  .\venv-xtts\Scripts\python.exe ..\..\examples\external_tts\xtts_worker.py
```

Если worker записал `C:/tmp/xtts_test.wav` и вышел с кодом 0 — связка готова.
