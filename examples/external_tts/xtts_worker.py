"""XTTS worker for DCS RadioForge external TTS provider.

Reads a JSON job from stdin: {"text", "voice", "language", "output"} and writes
synthesized WAV to "output". Run it with a venv that has torch + TTS installed
(see README_RU.md). This module imports TTS/torch lazily, so it can be imported
and unit-tested without those heavy dependencies.

Contract with the main app (tts.external_provider):
  * stdin  : JSON job, e.g. {"text": "Привет", "voice": "", "language": "ru", "output": "C:/tmp/out.wav"}
  * stdout : unused
  * stderr : human-readable error on failure
  * exit   : 0 on success, non-zero on error
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

XTTS_DEFAULT_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"


def read_job() -> dict:
    """Parse the JSON job from stdin and validate required fields."""
    raw = sys.stdin.read()
    try:
        job = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON on stdin: {exc}") from exc
    text = (job.get("text") or "").strip()
    output = (job.get("output") or "").strip()
    if not text:
        raise ValueError("missing required field: text")
    if not output:
        raise ValueError("missing required field: output")
    return job


def resolve_speaker_wav(job: dict) -> str:
    """Speaker reference: env RF_XTTS_SPEAKER_WAV, else payload.voice if it is a path."""
    env_wav = (os.environ.get("RF_XTTS_SPEAKER_WAV") or "").strip()
    voice = (job.get("voice") or "").strip()
    if env_wav:
        if not Path(env_wav).exists():
            raise ValueError(f"RF_XTTS_SPEAKER_WAV does not exist: {env_wav}")
        return env_wav
    if voice and Path(voice).exists():
        return voice
    raise ValueError("no speaker reference: set RF_XTTS_SPEAKER_WAV or pass voice=<path to wav>")


def resolve_model() -> str:
    return (os.environ.get("RF_XTTS_MODEL") or "").strip() or XTTS_DEFAULT_MODEL


def resolve_device() -> str:
    requested = (os.environ.get("RF_XTTS_DEVICE") or "auto").strip().lower()
    if requested not in {"auto", "cuda", "cpu"}:
        requested = "auto"
    if requested == "cpu":
        return "cpu"
    if requested == "cuda":
        return "cuda"
    import torch  # lazy

    return "cuda" if torch.cuda.is_available() else "cpu"


def _detect_language(text: str) -> str:
    return "ru" if any("\u0400" <= char <= "\u04ff" for char in text) else "en"


def synthesize(job: dict, speaker_wav: str, model_name: str, device: str) -> None:
    from TTS.api import TTS  # lazy heavy import

    language = job.get("language") or _detect_language(job["text"])
    try:
        model = TTS(model_name=model_name, device=device)
    except TypeError:
        # coqui-tts fork (>=0.24) replaced the device= kwarg with gpu= in the constructor.
        model = TTS(model_name=model_name, gpu=(device == "cuda"))
    model.tts_to_file(text=job["text"], speaker_wav=speaker_wav, language=language, file_path=job["output"])


def main() -> int:
    try:
        job = read_job()
        speaker_wav = resolve_speaker_wav(job)
        synthesize(job, speaker_wav, resolve_model(), resolve_device())
        return 0
    except Exception as exc:  # noqa: BLE001 - worker must report and exit non-zero
        print(f"xtts_worker error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
