# Использование в DCS Mission Editor

## Обычный sound trigger

1. Открой миссию в DCS Mission Editor.
2. Создай или выбери trigger.
3. Добавь action:
   - `SOUND TO ALL` для всех.
   - `SOUND TO GROUP` для конкретной группы игрока.
   - `RADIO TRANSMISSION`, если нужен источник радиопередачи в мире.
4. Выбери файл из `build/dcs-ready`.
5. Если нужны субтитры, добавь `MESSAGE TO ALL` или `MESSAGE TO GROUP`.

## Рекомендуемый паттерн

Для боевых подсказок лучше всегда парить звук и текст:

```text
ONCE: SEAD wakeup
CONDITION: FLAG 10 TRUE
ACTION: SOUND TO GROUP -> darkstar_wakeup.ogg
ACTION: MESSAGE TO GROUP -> "DARKSTAR: SAM network is awake..."
```

## Формат файлов

- `.ogg` - лучший вариант для большинства миссий.
- `.wav` - если нужна максимальная совместимость или дальнейший монтаж.
- ID реплик лучше делать короткими: `darkstar_wakeup`, `raven_magnum`, `gci_pop_up_group`.

## Как писать реплики

- Коротко.
- Главную тактическую информацию ставь в начало.
- Указывай угрозу, район и действие.
- Позывные добавляют атмосферу, но длинные монологи в бою обычно мешают.

Пример:

```text
DARKSTAR: Dagger One, SA-6 search radar active near Gali. Recommend push west and hold below angels eight.
```
