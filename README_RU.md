# DCS RadioForge

**DCS RadioForge** - локальная студия радио-озвучки для миссий DCS World. Пишешь реплики на русском или английском, выбираешь голос, накручиваешь эффект связи в духе SRS и получаешь готовые `.ogg` / `.wav` для Mission Editor.

English documentation: [README.md](README.md)

Текущий пакет эффектов сделан **в духе SRS**: это не код SRS и не мод к нему, а имитация ощущения DCS-радиосвязи через FFmpeg-фильтры, узкую полосу, компрессию, шум эфира, щелчки рации и хвост передачи.

## Что внутри

- Русский и английский интерфейс.
- Русские голоса: `ru-RU-DmitryNeural`, `ru-RU-SvetlanaNeural`.
- Английские тактические голоса под AWACS, JTAC, ведущего, FAC, брифинг и коалиционные реплики.
- Радио-пресеты: чистый звук, VHF AM, UHF AM, FM, шлемофон, AWACS, плохой приём, старая советская рация.
- Ползунок качества связи: ниже значение - больше шума, слабого сигнала и грязного хвоста.
- Опциональные щелчки рации для ощущения push-to-talk.
- Экспорт DCS-ready файлов в `build/dcs-ready`.
- Не нужен платный API-ключ. Используются `edge-tts` и ffmpeg из `imageio-ffmpeg`.

## Что скачать

Самый простой вариант для Windows:

1. Скачай `DCS-RadioForge-v0.1.1-windows-portable.zip` из последнего релиза.
2. Распакуй куда удобно.
3. Запусти `DCS-RadioForge.exe`.
4. Браузер откроется сам.

Готовые файлы для DCS появятся рядом с exe:

```text
build/dcs-ready
```

Windows может показать SmartScreen-предупреждение, потому что exe не подписан сертификатом.

## Быстрый старт из исходников

Ленивый запуск через Python:

```powershell
python run.py --open
```

Или двойной клик на Windows:

```text
Start_RadioForge.bat
```

Классический PowerShell-вариант:

```powershell
.\setup.ps1
.\start_gui.ps1
```

Открыть студию:

```text
http://127.0.0.1:8765
```

Переключение языка:

```text
http://127.0.0.1:8765/?lang=ru
http://127.0.0.1:8765/?lang=en
```

## Как вставлять в DCS

1. Сгенерируй `.ogg` или `.wav` в интерфейсе.
2. Открой миссию в DCS Mission Editor.
3. Добавь trigger action: `SOUND TO ALL`, `SOUND TO GROUP` или `RADIO TRANSMISSION`.
4. Выбери файл из `build/dcs-ready`.
5. Если нужны субтитры, добавь `MESSAGE TO ALL/GROUP` тем же триггером.

Обычно лучше использовать OGG: качество нормальное, `.miz` весит меньше.

## Пресеты радио

| Пресет | Когда использовать |
| --- | --- |
| Clean studio | Чистый исходник для дальнейшей обработки |
| SRS VHF AM | JTAC, FAC, низкий эшелон, пакетная связь |
| SRS UHF AM | Истребительная связь |
| SRS FM | Наземка, вертолёты, низкая работа |
| SRS cockpit mic | Шлемофон, реплики звена |
| SRS AWACS | AWACS, GCI, picture calls |
| SRS bad reception | Слабый, дальний или забитый сигнал |
| Old Soviet radio | Русский GCI, старая наземная рация |

Для эффекта плохой связи опускай качество сигнала. Для ощущения реальной передачи оставляй включёнными щелчки рации.

## Пакетная генерация

Основной режим - GUI. Для пачки реплик можно отредактировать `lines.csv` и запустить:

```powershell
.\generate.ps1
```

## Сборка Windows EXE

Собрать portable exe локально:

```powershell
.\build_windows_exe.ps1
```

Результат:

```text
release/DCS-RadioForge-v0.1.1-windows-portable.zip
```

## Карта проекта

- [Карта проекта](docs/PROJECT_MAP_RU.md)
- [Гайд по DCS Mission Editor](docs/DCS_MISSION_EDITOR_RU.md)
- [Гайд по радио-пресетам](docs/RADIO_PRESETS_RU.md)
- [Чеклист релиза](docs/RELEASE_CHECKLIST_RU.md)
- [GitHub release guide](docs/GITHUB_RELEASE.md)
- [Changelog](CHANGELOG.md)
- [Release notes](RELEASE_NOTES.md)

## Дисклеймер

DCS World - торговая марка Eagle Dynamics SA. SRS / DCS-SimpleRadio Standalone принадлежит своим авторам. DCS RadioForge - независимый инструмент для создателей миссий и не связан с Eagle Dynamics или SRS.
