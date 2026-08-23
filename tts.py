from __future__ import annotations

import asyncio
import importlib
import json
import os
import subprocess
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
        raise RuntimeError(f"Piper provider is unavailable: {piper_status().get('reason', 'unavailable')}")
    if provider == "xtts" and "xtts" not in TTS_PROVIDERS:
        raise RuntimeError(f"XTTS provider is unavailable: {xtts_status().get('reason', 'unavailable')}")
    if provider == "external" and "external" not in TTS_PROVIDERS:
        raise RuntimeError(f"External TTS provider is unavailable: {external_status().get('reason', 'unavailable')}")
    fn = TTS_PROVIDERS.get(provider, TTS_PROVIDERS["edge"])
    usage = fn(item, target)
    if provider == "elevenlabs":
        return usage, item.get("elevenVoiceId") or ""
    if provider == "piper":
        return usage, item.get("voice") or PIPER_DEFAULT_VOICE
    if provider == "xtts":
        return usage, item.get("voice") or "xtts"
    if provider == "external":
        return usage, item.get("voice") or os.environ.get("RF_EXTERNAL_TTS_VOICE_LABEL") or "local-gpu"
    return usage, item.get("voice") or "ru-RU-DmitryNeural"


def provider_source_format(name: str) -> str:
    """Source audio extension a provider writes (mp3 for edge/elevenlabs, wav for piper/xtts/external)."""
    if name in {"piper", "xtts", "external"}:
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


XTTS_DEFAULT_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"


def _xtts_language(text: str) -> str:
    return "ru" if any("\u0400" <= char <= "\u04ff" for char in text) else "en"


def xtts_status() -> dict:
    """Report XTTS/Coqui availability (local GPU TTS) without heavy imports.

    Reads RF_XTTS_ENABLED / RF_XTTS_DEVICE / RF_XTTS_MODEL / RF_XTTS_SPEAKER_WAV
    from the environment. torch/TTS are imported lazily and only while enabled.
    """
    if os.environ.get("RF_XTTS_ENABLED") != "1":
        return {"available": False, "reason": "disabled"}
    try:
        importlib.import_module("torch")
        importlib.import_module("TTS.api")
    except ImportError:
        return {"available": False, "reason": "not_installed"}
    model = os.environ.get("RF_XTTS_MODEL") or XTTS_DEFAULT_MODEL
    speaker_wav = (os.environ.get("RF_XTTS_SPEAKER_WAV") or "").strip()
    if not speaker_wav or not Path(speaker_wav).exists():
        return {"available": False, "reason": "speaker_wav_missing", "model": model}
    requested = (os.environ.get("RF_XTTS_DEVICE") or "auto").strip().lower()
    if requested not in {"auto", "cuda", "cpu"}:
        requested = "auto"
    if requested == "cpu":
        device = "cpu"
    else:
        torch = importlib.import_module("torch")
        if not torch.cuda.is_available():
            return {
                "available": False,
                "reason": "cuda_not_available",
                "device": "cuda",
                "model": model,
                "speaker_wav": str(Path(speaker_wav).resolve()),
            }
        device = "cuda"
    return {
        "available": True,
        "device": device,
        "model": model,
        "speaker_wav": str(Path(speaker_wav).resolve()),
    }


def xtts_provider(item: dict, target: Path) -> dict | None:
    """Coqui XTTS v2 synthesis writing WAV directly (GPU by default). Heavy imports here."""
    status = xtts_status()
    if not status["available"]:
        raise RuntimeError(f"XTTS provider is unavailable: {status['reason']}")
    tts_api = importlib.import_module("TTS.api")
    model = tts_api.TTS(model_name=status["model"], device=status["device"])
    text = (item.get("text") or "").strip()
    model.tts_to_file(
        text=text,
        speaker_wav=status["speaker_wav"],
        language=_xtts_language(text),
        file_path=str(target),
    )
    return None


def sync_xtts_registration() -> None:
    """Keep TTS_PROVIDERS in sync with current xtts availability (enabled + usable)."""
    if xtts_status()["available"]:
        TTS_PROVIDERS.setdefault("xtts", xtts_provider)
    else:
        TTS_PROVIDERS.pop("xtts", None)


class ExternalTTSError(Exception):
    """Runtime failure of the external TTS command with a machine-readable code."""

    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.code = code


def _external_timeout() -> int:
    raw = (os.environ.get("RF_EXTERNAL_TTS_TIMEOUT") or "").strip()
    try:
        return max(1, int(float(raw)))
    except (TypeError, ValueError):
        return 120


def external_status() -> dict:
    """Report external TTS command availability (separate venv/process bridge).

    Reads RF_EXTERNAL_TTS_ENABLED / RF_EXTERNAL_TTS_COMMAND / RF_EXTERNAL_TTS_TIMEOUT /
    RF_EXTERNAL_TTS_VOICE_LABEL from the environment. The command itself is not
    probed here; runtime failures surface as ExternalTTSError during synthesis.
    """
    if os.environ.get("RF_EXTERNAL_TTS_ENABLED") != "1":
        return {"available": False, "reason": "disabled"}
    command = (os.environ.get("RF_EXTERNAL_TTS_COMMAND") or "").strip()
    if not command:
        return {"available": False, "reason": "command_missing"}
    return {
        "available": True,
        "command": command,
        "timeout": _external_timeout(),
        "voice_label": os.environ.get("RF_EXTERNAL_TTS_VOICE_LABEL") or "Local GPU",
    }


def _split_command(command: str) -> list[str]:
    """Split a Windows command line into argv.

    Double quotes group tokens and are removed; backslashes are kept literal
    (unlike shlex posix=True, which would eat them in paths like C:/Users/...).
    """
    tokens: list[str] = []
    current: list[str] = []
    in_quotes = False
    for char in command:
        if char == '"':
            in_quotes = not in_quotes
        elif char.isspace() and not in_quotes:
            if current:
                tokens.append("".join(current))
                current = []
        else:
            current.append(char)
    if current:
        tokens.append("".join(current))
    return tokens


def external_provider(item: dict, target: Path) -> dict | None:
    """Run an external TTS command (its own venv/process) and take the WAV it writes.

    The command receives a JSON job on stdin: {text, voice, language, output}
    and must write WAV audio to the "output" path.
    """
    status = external_status()
    if not status["available"]:
        raise RuntimeError(f"External TTS provider is unavailable: {status['reason']}")
    text = (item.get("text") or "").strip()
    raw_lang = item.get("lang") or ""
    language = raw_lang if raw_lang in {"ru", "en"} else _xtts_language(text)
    payload = {
        "text": text,
        "voice": item.get("voice") or "",
        "language": language,
        "output": str(target),
    }
    try:
        proc = subprocess.run(
            _split_command(status["command"]),
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=status["timeout"],
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise ExternalTTSError(f"External TTS command timed out after {status['timeout']}s", "timeout") from None
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        detail = stderr or "no output"
        raise ExternalTTSError(f"External TTS command failed (exit {proc.returncode}): {detail}", "command_failed")
    if not target.exists():
        raise ExternalTTSError("External TTS command did not write the output wav", "command_failed")
    return None


def sync_external_registration() -> None:
    """Keep TTS_PROVIDERS in sync with current external command availability."""
    if external_status()["available"]:
        TTS_PROVIDERS.setdefault("external", external_provider)
    else:
        TTS_PROVIDERS.pop("external", None)


def sync_provider_registrations() -> None:
    """Refresh all optional provider registrations (piper, xtts, external)."""
    sync_piper_registration()
    sync_xtts_registration()
    sync_external_registration()
