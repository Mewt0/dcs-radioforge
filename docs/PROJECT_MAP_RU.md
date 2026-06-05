# Карта проекта

DCS RadioForge специально сделан маленьким и понятным: Python-бэкенд, статический web-интерфейс и папка с готовыми аудио, которая создаётся локально.

```text
dcs-radioforge/
├─ web/
│  ├─ index.html       # Оболочка интерфейса
│  ├─ app.js           # Состояние UI, локализация, API-запросы
│  └─ styles.css       # Тёмный DCS/cockpit-стиль
├─ server.py           # Локальный HTTP API, голоса, радио-обработка
├─ voicekit.py         # Пакетная генерация из CSV
├─ lines.csv           # Пример таблицы реплик
├─ setup.ps1           # Создание .venv и установка зависимостей
├─ start_gui.ps1       # Запуск локальной студии
├─ generate.ps1        # Запуск CSV-генерации
├─ run.py              # Ленивый Python-запуск
├─ Start_RadioForge.bat # Двойной клик для Windows
├─ build_windows_exe.ps1 # Сборка Windows portable EXE
├─ radioforge_launcher.py # Точка входа для PyInstaller
├─ requirements.txt    # Зависимости
├─ requirements-build.txt # Зависимости для сборки EXE
├─ .env.example       # Шаблон ElevenLabs key
├─ Set_ElevenLabs_Key.bat # Локальный помощник для ключа
├─ README.md           # Главная страница на английском
├─ README_RU.md        # Главная страница на русском
├─ CHANGELOG.md        # История релизов
├─ RELEASE_NOTES.md    # Заметки текущего релиза
├─ docs/               # Гайды и чеклисты
└─ build/              # Локальный вывод, не коммитится
```

## Поток работы

```text
Редактор реплики в GUI
  -> POST /api/generate
  -> синтез MP3 через edge-tts
  -> радио-обработка через ffmpeg
  -> OGG/WAV в build/dcs-ready
  -> trigger action в DCS Mission Editor
```

## Где что менять

- `server.py` - API, каталог голосов, пресеты радио, обработка аудио.
- `web/app.js` - состояние интерфейса, русский/английский текст, отправка генерации.
- `web/styles.css` - визуальный стиль.
- `voicekit.py` - CSV-режим для пакетной генерации.
- `run.py` - ленивый запуск из исходников.
- `radioforge_launcher.py` - входная точка для one-file EXE.
- `.env` - локальный ElevenLabs key, игнорируется git.
- `build/` - временный вывод, его не надо пушить на GitHub.
