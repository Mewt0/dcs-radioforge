"""Shared test doubles for DCS RadioForge tests."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar


class FakeCommunicate:
    """Records edge_tts.Communicate construction; save() writes a stub file."""

    calls: ClassVar[list[dict]] = []

    def __init__(self, text: str, *, voice: str, rate: str, pitch: str, volume: str) -> None:
        FakeCommunicate.calls.append({"text": text, "voice": voice, "rate": rate, "pitch": pitch, "volume": volume})

    async def save(self, target: str | Path) -> None:
        Path(target).write_bytes(b"stub-mp3")
