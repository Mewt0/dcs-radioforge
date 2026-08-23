from __future__ import annotations

import asyncio
import importlib
import os
import wave
from collections.abc import Callable
from pathlib import Path

import edge_tts

PIPER_DEFAULT_VOICE = "ru_RU-denis-medium"


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
    if provider == "piper" and "piper" not in TTS_PROVIDERS:
        raise RuntimeError(f"Piper provider is unavailable: {piper_status()['reason']}")
    fn = TTS_PROVIDERS.get(provider, TTS_PROVIDERS["edge"])
    usage = fn(item, target)
    if provider == "elevenlabs":
        return usage, item.get("elevenVoiceId") or ""
    if provider == "piper":
        return usage, item.get("voice") or PIPER_DEFAULT_VOICE
    return usage, item.get("voice") or "ru-RU-DmitryNeural"


def provider_source_format(name: str) -> str:
    """Source audio extension a provider writes (mp3 for edge/elevenlabs, wav for piper)."""
    if name == "piper":
        return "wav"
    return "mp3"


def piper_status() -> dict:
    """Report Piper/ONNX availability without loading heavy modules.

    Reads RF_PIPER_ENABLED / RF_PIPER_MODEL_DIR / RF_PIPER_DEFAULT_VOICE from the
    environment (server.load_local_env populates it per request). Piper itself is
    imported lazily and only while enabled.
    """
    if os.environ.get("RF_PIPER_ENABLED") != "1":
        return {"available": False, "reason": "disabled"}
    try:
        importlib.import_module("piper")
    except ImportError:
        return {"available": False, "reason": "not_installed"}
    model_dir = (os.environ.get("RF_PIPER_MODEL_DIR") or "").strip()
    if not model_dir or not Path(model_dir).is_dir():
        return {"available": False, "reason": "model_dir_missing"}
    voices = sorted(path.stem for path in Path(model_dir).glob("*.onnx"))
    if not voices:
        return {"available": False, "reason": "no_models"}
    return {
        "available": True,
        "model_dir": str(Path(model_dir).resolve()),
        "default_voice": os.environ.get("RF_PIPER_DEFAULT_VOICE") or PIPER_DEFAULT_VOICE,
        "voices": voices,
    }


def piper_provider(item: dict, target: Path) -> dict | None:
    """Local Piper/ONNX synthesis writing WAV directly. Heavy imports happen here."""
    status = piper_status()
    if not status["available"]:
        raise RuntimeError(f"Piper provider is unavailable: {status['reason']}")
    piper = importlib.import_module("piper")
    voice_name = item.get("voice") or status["default_voice"]
    model_dir = Path(status["model_dir"])
    model_path = model_dir / f"{voice_name}.onnx"
    config_path = model_dir / f"{voice_name}.onnx.json"
    if not model_path.exists():
        raise RuntimeError(f"Piper model not found: {model_path}")
    voice = piper.PiperVoice.load(str(model_path), config_path=str(config_path) if config_path.exists() else None)
    with wave.open(str(target), "wb") as wav_file:
        voice.synthesize((item.get("text") or "").strip(), wav_file)
    return None


def sync_piper_registration() -> None:
    """Keep TTS_PROVIDERS in sync with current piper availability (enabled + usable)."""
    if piper_status()["available"]:
        TTS_PROVIDERS.setdefault("piper", piper_provider)
    else:
        TTS_PROVIDERS.pop("piper", None)
