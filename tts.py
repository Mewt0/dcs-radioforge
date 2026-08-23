from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path

import edge_tts


async def synthesize_mp3(text: str, voice: str, rate: str, pitch: str, volume: str, target: Path) -> None:
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch, volume=volume)
    await communicate.save(str(target))


def edge_provider(item: dict, target: Path) -> dict | None:
    asyncio.run(
        synthesize_mp3(
            (item.get("text") or "").strip(),
            item.get("voice") or "ru-RU-DmitryNeural",
            item.get("rate") or "+0%",
            item.get("pitch") or "+0Hz",
            item.get("volume") or "+0%",
            target,
        )
    )
    return None


TTS_PROVIDERS: dict[str, Callable[[dict, Path], dict | None]] = {
    "edge": edge_provider,
}


def synthesize_item(item: dict, target: Path) -> tuple[dict | None, str]:
    provider = item.get("provider") or "edge"
    fn = TTS_PROVIDERS.get(provider, TTS_PROVIDERS["edge"])
    usage = fn(item, target)
    if provider == "elevenlabs":
        return usage, item.get("elevenVoiceId") or ""
    return usage, item.get("voice") or "ru-RU-DmitryNeural"
