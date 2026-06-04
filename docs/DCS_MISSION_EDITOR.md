# DCS Mission Editor Usage

## Basic Sound Trigger

1. Open your mission in DCS Mission Editor.
2. Create or select a trigger.
3. Add an action:
   - `SOUND TO ALL` for everyone.
   - `SOUND TO GROUP` for a specific player group.
   - `RADIO TRANSMISSION` if you want an in-world radio source.
4. Select a generated file from `build/dcs-ready`.
5. Add `MESSAGE TO ALL` or `MESSAGE TO GROUP` if you want subtitles.

## Recommended Pattern

For mission guidance, pair sound and text:

```text
ONCE: SEAD wakeup
CONDITION: FLAG 10 TRUE
ACTION: SOUND TO GROUP -> darkstar_wakeup.ogg
ACTION: MESSAGE TO GROUP -> "DARKSTAR: SAM network is awake..."
```

## File Format

- Use `.ogg` for most mission lines.
- Use `.wav` only when you need maximum compatibility or later editing.
- Keep line IDs short and mission-friendly: `darkstar_wakeup`, `raven_magnum`, `gci_pop_up_group`.

## Good DCS Line Design

- Keep radio calls short.
- Put the important tactical fact first.
- Mention the threat, area, and action.
- Use repeated call signs for atmosphere, but avoid long cinematic speeches during combat.

Example:

```text
DARKSTAR: Dagger One, SA-6 search radar active near Gali. Recommend push west and hold below angels eight.
```
