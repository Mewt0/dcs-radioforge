# XTTS worker для внешнего TTS-провайдера (examples/external_tts)

Этот worker подключает Coqui XTTS v2 (и похожие движки) к DCS RadioForge через
универсальный external-провайдер. Работает **в отдельном venv** — не трогает
основной `repo\.venv` и не зависит от его версии Python.

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

## Установка (Python 3.11/3.12 в отдельном venv)

```powershell
py -3.12 -m venv .venv-xtts
.\venv-xtts\Scripts\python -m pip install --upgrade pip

# CUDA-версия torch (версию CUDA сверь с nvidia-smi):
.\venv-xtts\Scripts\pip install torch --index-url https://download.pytorch.org/whl/cu126
# если колеса cu126 не поддерживают вашу видеокарту — попробуйте cu121:
#   .\venv-xtts\Scripts\pip install torch --index-url https://download.pytorch.org/whl/cu121

.\venv-xtts\Scripts\pip install -r ..\..\requirements-xtts.txt
```

Проверка CUDA:

```powershell
.\venv-xtts\Scripts\python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

## Настройка основного приложения

В `.env` (или переменные окружения сессии) укажите команду и reference-голос:

```ini
RF_EXTERNAL_TTS_ENABLED=1
RF_EXTERNAL_TTS_COMMAND="C:\project\.venv-xtts\Scripts\python.exe" "C:\project\repo\examples\external_tts\xtts_worker.py"
RF_EXTERNAL_TTS_TIMEOUT=180
RF_EXTERNAL_TTS_VOICE_LABEL=XTTS GPU
RF_XTTS_SPEAKER_WAV=C:\Users\Vlad\Documents\Codex\2026-08-23\https-github-com-mewt0-dcs-radioforge\outputs\voice_reference\voice_ref_full_24k_mono.wav
```

`RF_XTTS_SPEAKER_WAV` наследуется worker-процессом из окружения сервера, поэтому
задавать её повторно внутри `RF_EXTERNAL_TTS_COMMAND` не нужно.

## Проверка

1. Запустите сервер: `python server.py`.
2. `GET /api/tts/providers` — у `external` должно быть `"available": true`.
3. Кнопка «Проверить голос» в редакторе (провайдер Local GPU) или
   `POST /api/tts/preview` c `provider: "external"`.
4. Готовые файлы — как обычно в `build/dcs-ready`.

## Самотест worker'а (без запуска сервера)

```powershell
echo '{"text": "Привет", "voice": "", "language": "ru", "output": "C:/tmp/xtts_test.wav"}' |
  .\venv-xtts\Scripts\python.exe ..\..\examples\external_tts\xtts_worker.py
```

Если worker записал `C:/tmp/xtts_test.wav` и вышел с кодом 0 — связка готова.
