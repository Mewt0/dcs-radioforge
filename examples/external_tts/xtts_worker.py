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
import re
import sys
from pathlib import Path

XTTS_DEFAULT_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"

# DCS terms -> spoken Russian. Applied to the text before synthesis so embedded
# English words (callsigns, weapon names) do not get half-pronounced by XTTS.
# Opt out with RF_XTTS_TRANSLITERATE=0. See docs/TTS_TIPS_RU.md.
_TERMS: dict[str, str] = {
    "MASTER ARM": "мастер арм",
    "ARM": "арм",
    "AGM-65B": "эй джи эм шестьдесят пять бэ",
    "AGM-65": "эй джи эм шестьдесят пять",
    "AGM-88": "эй джи эм восемьдесят восемь",
    "AIM-120": "эй ай эм сто двадцать",
    "AIM-54": "эй ай эм пятьдесят четыре",
    "AIM-9": "эй ай эм девять",
    "AIM-7": "эй ай эм семь",
    "GBU-38": "джи би ю тридцать восемь",
    "GBU-31": "джи би ю тридцать один",
    "GBU-12": "джи би ю двенадцать",
    "CBU-97": "си би ю девяносто семь",
    "MK-84": "эм кей восемьдесят четыре",
    "MK-82": "эм кей восемьдесят два",
    "R-73": "р семьдесят три",
    "R-27": "р двадцать семь",
    "KH-29": "х двадцать девять",
    "F-4E": "эф четыре и",
    "F-35": "эф тридцать пять",
    "F-22": "эф двадцать два",
    "F/A-18": "эф восемнадцать",
    "F-16": "эф шестнадцать",
    "F-15": "эф пятнадцать",
    "F-14": "эф четырнадцать",
    "A-10": "эй десять",
    "B-52": "би пятьдесят два",
    "SU-25": "су двадцать пять",
    "SU-27": "су двадцать семь",
    "MIG-29": "миг двадцать девять",
    "MIG-21": "миг двадцать один",
    "AH-64": "эйч шестьдесят четыре",
    "KA-50": "ка пятьдесят",
    "UH-60": "ю эйч шестьдесят",
    "KC-135": "кей си сто тридцать пять",
    "C-130": "си сто тридцать",
    "AMRAAM": "амрэм",
    "SIDEWINDER": "сайдуиндер",
    "MAVERICK": "мэверик",
    "PHOENIX": "феникс",
    "SPARROW": "спэрроу",
    "PAVEWAY": "пэйввей",
    "JDAM": "джейдам",
    "HARM": "харм",
    "HUD": "хад",
    "MFD": "мфд",
    "AWACS": "авакс",
    "JTAC": "джитак",
    "WSO": "оператор вооружения",
    "TACAN": "такан",
    "CAVOK": "кавок",
    "BULLSEYE": "буллзай",
    "BINGO": "бинго",
    "JOKER": "джокер",
    "WINCHESTER": "винчестер",
    "SPLASH": "сплэш",
    "MAYDAY": "мэйдэй",
    "PAN-PAN": "пан-пан",
    "FOX 3": "фокс три",
    "FOX 2": "фокс два",
    "FOX 1": "фокс один",
    "BVR": "за пределами видимости",
    "WVR": "в пределах видимости",
    "RWR": "сигнализатор облучения",
    "TGP": "контейнер наведения",
    "FLIR": "тепловизор",
    "DME": "дальномер",
    "IFF": "свой-чужой",
    "ECM": "рэб",
    "RTB": "возвращение на базу",
    "CAP": "кэп",
    "SEAD": "подавление пво",
    "FAC": "фак",
    "GCI": "джи-си-ай",
    "BANDIT": "бандит",
    "BOGEY": "богги",
    "RIFLE": "райфл",
    "MAGNUM": "магнум",
    "SPIKE": "спайк",
    "VIPER": "вайпер",
    "HORNET": "хорнет",
    "EAGLE": "игл",
    "TOMCAT": "томкэт",
    "RAPTOR": "рэптор",
}

_TERM_KEYS = sorted(_TERMS, key=len, reverse=True)
_TERM_RE = re.compile(r"\b(?:" + "|".join(re.escape(key) for key in _TERM_KEYS) + r")\b", re.IGNORECASE)


def transliterate(text: str) -> str:
    """Replace known Latin DCS terms with their spoken Russian equivalents."""
    if os.environ.get("RF_XTTS_TRANSLITERATE", "1") != "1":
        return text
    return _TERM_RE.sub(lambda match: _TERMS[match.group(0).upper()], text)


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
    """Speaker reference: payload.voice if it is an existing path, else env RF_XTTS_SPEAKER_WAV."""
    voice = (job.get("voice") or "").strip()
    if voice and Path(voice).exists():
        return voice
    env_wav = (os.environ.get("RF_XTTS_SPEAKER_WAV") or "").strip()
    if env_wav:
        if not Path(env_wav).exists():
            raise ValueError(f"RF_XTTS_SPEAKER_WAV does not exist: {env_wav}")
        return env_wav
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

    text = transliterate((job.get("text") or "").strip())
    language = job.get("language") or _detect_language(text)
    try:
        model = TTS(model_name=model_name, device=device)
    except TypeError:
        # coqui-tts fork (>=0.24) replaced the device= kwarg with gpu= in the constructor.
        model = TTS(model_name=model_name, gpu=(device == "cuda"))
    model.tts_to_file(text=text, speaker_wav=speaker_wav, language=language, file_path=job["output"])


def main() -> int:
    try:
        job = read_job()
        speaker_wav = resolve_speaker_wav(job)
        synthesize(job, speaker_wav, resolve_model(), resolve_device())
        return 0
    except Exception as exc:  # noqa: BLE001 - worker must report and exit non-zero
        message = str(exc).strip().splitlines()[0] if str(exc).strip() else type(exc).__name__
        print(f"xtts_worker error: {type(exc).__name__}: {message[:300]}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
