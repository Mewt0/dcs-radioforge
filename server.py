from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
import wave
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error as urlerror
from urllib import parse, request
from urllib.parse import unquote, urlparse

import imageio_ffmpeg

import tts

SOURCE_ROOT = Path(__file__).resolve().parent
RESOURCE_ROOT = Path(getattr(sys, "_MEIPASS", SOURCE_ROOT))
APP_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else SOURCE_ROOT
ROOT = APP_ROOT
WEB = RESOURCE_ROOT / "web"
BUILD = APP_ROOT / "build"
READY = BUILD / "dcs-ready"
TMP = BUILD / "_tmp_mp3"
PREVIEWS = BUILD / "elevenlabs-previews"
BACKUP_DIR = BUILD / "rf_backup"
ELEVENLABS_HOST = "https://api.elevenlabs.io"
ELEVENLABS_V1 = f"{ELEVENLABS_HOST}/v1"

VOICE_CATALOG = [
    {
        "name": "ru-RU-DmitryNeural",
        "lang": "ru",
        "gender": "Male",
        "role": "Russian controller",
        "tone": "Friendly, Positive",
    },
    {
        "name": "ru-RU-SvetlanaNeural",
        "lang": "ru",
        "gender": "Female",
        "role": "Russian package / ops",
        "tone": "Friendly, Positive",
    },
    {
        "name": "en-US-ChristopherNeural",
        "lang": "en",
        "gender": "Male",
        "role": "AWACS / command",
        "tone": "Reliable, Authority",
    },
    {"name": "en-US-SteffanNeural", "lang": "en", "gender": "Male", "role": "JTAC / controller", "tone": "Rational"},
    {"name": "en-US-EricNeural", "lang": "en", "gender": "Male", "role": "Tactical brief", "tone": "Rational"},
    {"name": "en-GB-ThomasNeural", "lang": "en", "gender": "Male", "role": "FAC / coalition", "tone": "Calm, British"},
    {"name": "en-CA-LiamNeural", "lang": "en", "gender": "Male", "role": "Flight lead", "tone": "Calm, clear"},
    {
        "name": "en-AU-WilliamMultilingualNeural",
        "lang": "en",
        "gender": "Male",
        "role": "Package lead",
        "tone": "Friendly, Positive",
    },
    {
        "name": "en-US-AriaNeural",
        "lang": "en",
        "gender": "Female",
        "role": "Intel / briefing",
        "tone": "Positive, Confident",
    },
    {
        "name": "en-GB-SoniaNeural",
        "lang": "en",
        "gender": "Female",
        "role": "British ops",
        "tone": "Friendly, Positive",
    },
]

ROLE_PRESETS = [
    {
        "id": "ru_gci",
        "label": "RU GCI",
        "voice": "ru-RU-DmitryNeural",
        "rate": "+3%",
        "pitch": "-10Hz",
        "preset": "srs_old_soviet",
    },
    {
        "id": "ru_raven",
        "label": "RU RAVEN",
        "voice": "ru-RU-SvetlanaNeural",
        "rate": "+1%",
        "pitch": "-3Hz",
        "preset": "srs_cockpit",
    },
    {
        "id": "en_awacs",
        "label": "EN AWACS",
        "voice": "en-US-ChristopherNeural",
        "rate": "-2%",
        "pitch": "-10Hz",
        "preset": "srs_awacs",
    },
    {
        "id": "en_jtac",
        "label": "EN JTAC",
        "voice": "en-US-SteffanNeural",
        "rate": "+1%",
        "pitch": "-8Hz",
        "preset": "srs_vhf_am",
    },
    {
        "id": "en_flightlead",
        "label": "EN FLIGHT LEAD",
        "voice": "en-CA-LiamNeural",
        "rate": "+0%",
        "pitch": "-6Hz",
        "preset": "srs_uhf_am",
    },
]

RADIO_PRESETS = {
    "clean": {
        "label": "Clean studio",
        "description": "Only loudness normalization. Good source for later editing.",
        "noise": 0.0,
        "tail_noise": 0.0,
        "tail_duration": 0.0,
        "clicks": False,
        "filters": ["loudnorm=I=-18:TP=-1.5:LRA=11"],
    },
    "srs_vhf_am": {
        "label": "SRS VHF AM",
        "description": "Narrow, bright and busy. Good for JTAC, FAC and low altitude package comms.",
        "noise": 0.0035,
        "tail_noise": 0.018,
        "tail_duration": 0.22,
        "clicks": True,
        "click_in": 1380,
        "click_out": 920,
        "filters": [
            "loudnorm=I=-18:TP=-1.5:LRA=11",
            "highpass=f=330",
            "lowpass=f=3000",
            "equalizer=f=1050:t=q:w=1.4:g=3",
            "acompressor=threshold=-24dB:ratio=4.2:attack=4:release=95",
            "volume=1.48",
            "alimiter=limit=0.92",
        ],
    },
    "srs_uhf_am": {
        "label": "SRS UHF AM",
        "description": "Cleaner fighter radio with tight compression and short squelch tail.",
        "noise": 0.002,
        "tail_noise": 0.012,
        "tail_duration": 0.16,
        "clicks": True,
        "click_in": 1550,
        "click_out": 1050,
        "filters": [
            "loudnorm=I=-18:TP=-1.5:LRA=10",
            "highpass=f=280",
            "lowpass=f=3600",
            "equalizer=f=1500:t=q:w=1.2:g=2.2",
            "acompressor=threshold=-22dB:ratio=3.2:attack=5:release=120",
            "volume=1.34",
            "alimiter=limit=0.94",
        ],
    },
    "srs_fm": {
        "label": "SRS FM",
        "description": "Fuller FM tactical radio for ground forces, helos and low level work.",
        "noise": 0.0028,
        "tail_noise": 0.015,
        "tail_duration": 0.20,
        "clicks": True,
        "click_in": 1200,
        "click_out": 780,
        "filters": [
            "loudnorm=I=-18:TP=-1.5:LRA=10",
            "highpass=f=220",
            "lowpass=f=4200",
            "equalizer=f=900:t=q:w=1.1:g=1.6",
            "acompressor=threshold=-21dB:ratio=3.0:attack=6:release=140",
            "volume=1.28",
            "alimiter=limit=0.94",
        ],
    },
    "srs_cockpit": {
        "label": "SRS Cockpit mic",
        "description": "Close helmet mic, compressed and readable without too much degradation.",
        "noise": 0.0022,
        "tail_noise": 0.010,
        "tail_duration": 0.14,
        "clicks": True,
        "click_in": 1500,
        "click_out": 980,
        "filters": [
            "loudnorm=I=-18:TP=-1.5:LRA=10",
            "highpass=f=260",
            "lowpass=f=3400",
            "equalizer=f=1250:t=q:w=1.3:g=2.3",
            "acompressor=threshold=-20dB:ratio=3.4:attack=5:release=115",
            "volume=1.36",
            "alimiter=limit=0.94",
        ],
    },
    "srs_awacs": {
        "label": "SRS AWACS",
        "description": "Authoritative long-range controller voice, crisp but less broken.",
        "noise": 0.0014,
        "tail_noise": 0.009,
        "tail_duration": 0.15,
        "clicks": True,
        "click_in": 1320,
        "click_out": 850,
        "filters": [
            "loudnorm=I=-17:TP=-1.5:LRA=9",
            "highpass=f=220",
            "lowpass=f=4200",
            "equalizer=f=1800:t=q:w=1.0:g=2.4",
            "acompressor=threshold=-22dB:ratio=2.7:attack=7:release=150",
            "volume=1.22",
            "alimiter=limit=0.95",
        ],
    },
    "srs_bad_reception": {
        "label": "SRS Bad reception",
        "description": "Noisy and clipped for distant or masked transmissions.",
        "noise": 0.010,
        "tail_noise": 0.030,
        "tail_duration": 0.28,
        "clicks": True,
        "click_in": 1100,
        "click_out": 720,
        "filters": [
            "loudnorm=I=-18:TP=-1.5:LRA=7",
            "highpass=f=430",
            "lowpass=f=2350",
            "equalizer=f=950:t=q:w=1.8:g=4",
            "acompressor=threshold=-27dB:ratio=5.8:attack=3:release=70",
            "volume=1.72",
            "alimiter=limit=0.88",
        ],
    },
    "srs_old_soviet": {
        "label": "Old Soviet radio",
        "description": "Very narrow and gritty, good for Russian GCI or old ground units.",
        "noise": 0.0075,
        "tail_noise": 0.026,
        "tail_duration": 0.24,
        "clicks": True,
        "click_in": 960,
        "click_out": 620,
        "filters": [
            "loudnorm=I=-18:TP=-1.5:LRA=7",
            "highpass=f=480",
            "lowpass=f=2200",
            "equalizer=f=820:t=q:w=2.0:g=4.2",
            "acompressor=threshold=-26dB:ratio=5.4:attack=3:release=75",
            "volume=1.68",
            "alimiter=limit=0.89",
        ],
    },
}


def ffmpeg() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


def safe_id(value: str, fallback: str = "line") -> str:
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    cleaned = "".join(ch if ch in allowed else "_" for ch in value.strip())
    cleaned = "_".join(part for part in cleaned.split("_") if part).lower()
    if not cleaned:
        cleaned = fallback
    return cleaned[:80]


def json_response(handler: BaseHTTPRequestHandler, payload: object, status: int = 200) -> None:
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def text_response(handler: BaseHTTPRequestHandler, text: str, status: int = 200) -> None:
    raw = text.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/plain; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def load_local_env() -> None:
    for env_path in (APP_ROOT / ".env", SOURCE_ROOT / ".env"):
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def elevenlabs_api_key(required: bool = True) -> str | None:
    key = (os.environ.get("ELEVENLABS_API_KEY") or "").strip()
    if required and not key:
        raise RuntimeError("ELEVENLABS_API_KEY is not configured. Add it to .env or the environment.")
    return key or None


def elevenlabs_request(
    method: str,
    path: str,
    payload: dict | None = None,
    query: dict | None = None,
    binary: bool = False,
    include_headers: bool = False,
) -> bytes | dict | list | tuple[bytes | dict | list, dict[str, str]]:
    key = elevenlabs_api_key(required=True)
    url = f"{ELEVENLABS_HOST}{path}" if path.startswith("/v") else f"{ELEVENLABS_V1}{path}"
    if query:
        url = f"{url}?{parse.urlencode(query)}"
    body = json.dumps(payload or {}, ensure_ascii=False).encode("utf-8") if payload is not None else None
    headers = {"xi-api-key": key or "", "User-Agent": "DCS-RadioForge"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = request.Request(url, data=body, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=120) as response:
            raw = response.read()
            response_headers = {key.lower(): value for key, value in response.headers.items()}
    except urlerror.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ElevenLabs API error {exc.code}: {detail}") from exc
    if binary:
        return (raw, response_headers) if include_headers else raw
    data: dict | list
    if not raw:
        data = {}
    else:
        data = json.loads(raw.decode("utf-8"))
    return (data, response_headers) if include_headers else data


def int_or_none(value: object) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(float(str(value)))
    except (TypeError, ValueError):
        return None


def float_or_none(value: object) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(str(value))
    except (TypeError, ValueError):
        return None


def elevenlabs_usage_from_headers(headers: dict[str, str]) -> dict:
    character_count = int_or_none(headers.get("x-character-count"))
    request_id = headers.get("request-id") or headers.get("x-request-id") or ""
    return {
        "character_count": character_count,
        "request_id": request_id,
    }


def get_elevenlabs_subscription() -> dict:
    data = elevenlabs_request("GET", "/user/subscription")
    if not isinstance(data, dict):
        return {}
    overage = data.get("current_overage") or {}
    next_invoice = data.get("next_invoice") or {}
    return {
        "tier": data.get("tier") or "",
        "status": data.get("status") or "",
        "character_count": int_or_none(data.get("character_count")),
        "character_limit": int_or_none(data.get("character_limit")),
        "max_credit_limit_extension": data.get("max_credit_limit_extension"),
        "current_overage": {
            "amount": overage.get("amount") if isinstance(overage, dict) else None,
            "currency": overage.get("currency") if isinstance(overage, dict) else None,
        },
        "has_open_invoices": bool(data.get("has_open_invoices")),
        "next_invoice": {
            "amount_due_cents": int_or_none(next_invoice.get("amount_due_cents"))
            if isinstance(next_invoice, dict)
            else None,
        },
        "next_character_count_reset_unix": int_or_none(data.get("next_character_count_reset_unix")),
        "currency": data.get("currency") or "",
        "billing_period": data.get("billing_period") or "",
        "character_refresh_period": data.get("character_refresh_period") or "",
    }


def list_elevenlabs_models() -> list[dict]:
    data = elevenlabs_request("GET", "/models")
    if not isinstance(data, list):
        return []
    models: list[dict] = []
    for model in data:
        if not isinstance(model, dict) or not model.get("can_do_text_to_speech", True):
            continue
        rates = model.get("model_rates") or {}
        character_multiplier = (
            float_or_none(rates.get("character_cost_multiplier")) if isinstance(rates, dict) else None
        )
        discount_multiplier = float_or_none(rates.get("cost_discount_multiplier")) if isinstance(rates, dict) else None
        token_cost_factor = float_or_none(model.get("token_cost_factor"))
        effective_multiplier = character_multiplier
        if effective_multiplier is not None and discount_multiplier is not None:
            effective_multiplier *= discount_multiplier
        if effective_multiplier is None:
            effective_multiplier = token_cost_factor
        models.append(
            {
                "model_id": model.get("model_id") or "",
                "name": model.get("name") or model.get("model_id") or "",
                "token_cost_factor": token_cost_factor,
                "character_cost_multiplier": character_multiplier,
                "cost_discount_multiplier": discount_multiplier,
                "effective_character_cost_multiplier": effective_multiplier,
                "maximum_text_length_per_request": int_or_none(model.get("maximum_text_length_per_request")),
                "max_characters_request_free_user": int_or_none(model.get("max_characters_request_free_user")),
                "max_characters_request_subscribed_user": int_or_none(
                    model.get("max_characters_request_subscribed_user")
                ),
            }
        )
    return models


def synthesize_elevenlabs_mp3(
    text: str,
    voice_id: str,
    model_id: str,
    language_code: str,
    target: Path,
) -> dict:
    if not voice_id:
        raise RuntimeError("ElevenLabs voice id is empty")
    payload: dict = {
        "text": text,
        "model_id": model_id or "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.48,
            "similarity_boost": 0.78,
            "style": 0.18,
            "use_speaker_boost": True,
        },
    }
    if language_code:
        payload["language_code"] = language_code
    raw, headers = elevenlabs_request(
        "POST",
        f"/text-to-speech/{parse.quote(voice_id)}",
        payload=payload,
        query={"output_format": "mp3_44100_128"},
        binary=True,
        include_headers=True,
    )
    target.write_bytes(raw)  # type: ignore[arg-type]
    usage = elevenlabs_usage_from_headers(headers)
    usage.update(
        {
            "model_id": model_id or "eleven_multilingual_v2",
            "text_characters": len(text),
        }
    )
    return usage


def elevenlabs_provider(item: dict, target: Path) -> dict | None:
    return synthesize_elevenlabs_mp3(
        (item.get("text") or "").strip(),
        item.get("elevenVoiceId") or "",
        item.get("elevenModel") or "eleven_multilingual_v2",
        item.get("elevenLanguage") or item.get("lang") or "",
        target,
    )


tts.TTS_PROVIDERS["elevenlabs"] = elevenlabs_provider


def list_elevenlabs_voices() -> list[dict]:
    voices: list[dict] = []
    next_page_token: str | None = None
    while True:
        query = {"page_size": 100}
        if next_page_token:
            query["next_page_token"] = next_page_token
        data = elevenlabs_request("GET", "/v2/voices", query=query)
        if not isinstance(data, dict):
            break
        voices.extend(data.get("voices", []))
        if not data.get("has_more"):
            break
        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break
    return [
        {
            "voice_id": voice.get("voice_id", ""),
            "name": voice.get("name", ""),
            "category": voice.get("category", ""),
            "description": voice.get("description") or "",
            "preview_url": voice.get("preview_url") or "",
            "labels": voice.get("labels") or {},
        }
        for voice in voices
    ]


def design_elevenlabs_voice(payload: dict) -> dict:
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    description = (payload.get("voice_description") or payload.get("description") or "").strip()
    if len(description) < 20:
        raise RuntimeError("Voice description must be at least 20 characters")
    request_payload: dict = {
        "voice_description": description,
        "model_id": payload.get("model_id") or "eleven_multilingual_ttv_v2",
        "auto_generate_text": bool(payload.get("auto_generate_text", True)),
        "should_enhance": bool(payload.get("should_enhance", True)),
        "guidance_scale": float(payload.get("guidance_scale") or 7),
        "loudness": float(payload.get("loudness") or 0.5),
    }
    text = (payload.get("text") or "").strip()
    if len(text) >= 100:
        request_payload["text"] = text
    else:
        request_payload["auto_generate_text"] = True
    seed = payload.get("seed")
    if seed not in (None, ""):
        request_payload["seed"] = int(seed)
    data = elevenlabs_request(
        "POST",
        "/text-to-voice/design",
        payload=request_payload,
        query={"output_format": "mp3_44100_128"},
    )
    previews = []
    for index, preview in enumerate(data.get("previews", []), start=1):  # type: ignore[union-attr]
        generated_id = preview.get("generated_voice_id") or f"preview_{index}"
        audio_base64 = preview.get("audio_base_64") or ""
        filename = safe_id(f"eleven_preview_{generated_id}", f"eleven_preview_{index}") + ".mp3"
        if audio_base64:
            (PREVIEWS / filename).write_bytes(base64.b64decode(audio_base64))
        previews.append(
            {
                "generated_voice_id": generated_id,
                "duration_secs": preview.get("duration_secs"),
                "language": preview.get("language"),
                "media_type": preview.get("media_type") or "audio/mpeg",
                "url": f"/previews/{filename}" if audio_base64 else "",
            }
        )
    return {"text": data.get("text", ""), "previews": previews}  # type: ignore[union-attr]


def create_elevenlabs_voice(payload: dict) -> dict:
    voice_name = (payload.get("voice_name") or payload.get("name") or "").strip()
    voice_description = (payload.get("voice_description") or payload.get("description") or "").strip()
    generated_voice_id = (payload.get("generated_voice_id") or "").strip()
    if not voice_name:
        raise RuntimeError("Voice name is empty")
    if len(voice_description) < 20:
        raise RuntimeError("Voice description must be at least 20 characters")
    if not generated_voice_id:
        raise RuntimeError("Generated voice id is empty")
    request_payload = {
        "voice_name": voice_name,
        "voice_description": voice_description,
        "generated_voice_id": generated_voice_id,
        "labels": payload.get("labels") or {"use_case": "dcs-radioforge"},
    }
    result = elevenlabs_request("POST", "/text-to-voice", payload=request_payload)
    return result if isinstance(result, dict) else {}


def run_ffmpeg(args: list[str]) -> None:
    subprocess.run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def clamp(value: float, low: float, high: float) -> int | float:
    return max(low, min(high, value))


def loudness_target() -> str:
    """Target integrated loudness (LUFS) for generated audio. Default matches the
    reference lesson loudness (~-9 LUFS); override with RF_TTS_LOUDNESS_TARGET."""
    return (os.environ.get("RF_TTS_LOUDNESS_TARGET") or "-9").strip() or "-9"


_CREST_FILTERS = (
    "acompressor=threshold=-20dB:ratio=20:attack=0.05:release=30,"
    "acompressor=threshold=-30dB:ratio=20:attack=0.05:release=30"
)


def loudnorm_params(path: Path) -> dict:
    """Measure EBU R128 loudness of a file via ffmpeg (for a two-pass loudnorm)."""
    result = subprocess.run(
        [
            ffmpeg(),
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-af",
            f"loudnorm=I={loudness_target()}:TP=-1.5:LRA=11:print_format=json",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )
    text = (result.stdout or "") + (result.stderr or "")
    params: dict = {}
    for key in ("input_i", "input_tp", "input_lra", "input_thresh"):
        match = re.search(rf'"{key}"\s*:\s*"?(-?[\d.]+)"?', text)
        if match:
            params[key] = match.group(1)
    return params


def loudnorm_apply_filter(params: dict) -> str:
    """Two-pass loudnorm filter string using previously measured loudness params."""
    base = f"loudnorm=I={loudness_target()}:TP=-1.5:LRA=11"
    if not params.get("input_i"):
        return f"{base}:linear=false"
    return (
        f"{base}:measured_I={params['input_i']}:measured_TP={params['input_tp']}:"
        f"measured_LRA={params['input_lra']}:measured_thresh={params['input_thresh']}:linear=false"
    )


def convert_audio(
    src: Path,
    dst: Path,
    fmt: str,
    sample_rate: int,
    preset_id: str,
    signal_quality: int = 86,
    mic_clicks: bool = True,
) -> None:
    preset = RADIO_PRESETS.get(preset_id, RADIO_PRESETS["srs_cockpit"])
    quality = int(clamp(signal_quality, 15, 100))
    weakness = (100 - quality) / 100.0
    preset_filters = [f for f in preset["filters"] if not f.startswith("loudnorm")]
    base_filters = [
        "aformat=channel_layouts=mono",
        f"aresample={sample_rate}",
        *preset_filters,
    ]
    if weakness > 0.18:
        depth = min(0.22, weakness * 0.20)
        base_filters.append(f"tremolo=f=7.5:d={depth:.3f}")
    filters = ",".join(base_filters)
    codec = ["-c:a", "pcm_s16le"] if fmt == "wav" else ["-c:a", "libvorbis", "-q:a", "4"]
    noise = float(preset.get("noise") or 0) * (1.0 + weakness * 4.0)
    tail_noise = float(preset.get("tail_noise") or 0) * (1.0 + weakness * 3.0)
    tail_duration = float(preset.get("tail_duration") or 0) * (1.0 + weakness * 0.8)

    graph_parts: list[str] = []
    if noise > 0:
        graph_parts.append(f"[0:a]{filters}[base]")
        graph_parts.append(f"anoisesrc=color=white:amplitude={noise:.5f}:sample_rate={sample_rate}[noise]")
        graph_parts.append(
            "[base][noise]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,alimiter=limit=0.95[voice]"
        )
    else:
        graph_parts.append(f"[0:a]{filters}[voice]")

    concat_labels: list[str] = []
    if mic_clicks and preset.get("clicks"):
        click_in = int(preset.get("click_in") or 1400)
        click_out = int(preset.get("click_out") or 900)
        graph_parts.append(
            f"sine=frequency={click_in}:duration=0.035:sample_rate={sample_rate},"
            "aformat=channel_layouts=mono,volume=0.36,afade=t=out:st=0.018:d=0.017[clickin]"
        )
        graph_parts.append(
            f"sine=frequency={click_out}:duration=0.045:sample_rate={sample_rate},"
            "aformat=channel_layouts=mono,volume=0.28,afade=t=out:st=0.020:d=0.025[clickout]"
        )
        concat_labels.append("[clickin]")

    concat_labels.append("[voice]")

    if mic_clicks and preset.get("clicks"):
        concat_labels.append("[clickout]")

    if tail_noise > 0 and tail_duration > 0:
        tail_fade_start = max(0.02, tail_duration * 0.38)
        tail_fade_len = max(0.03, tail_duration - tail_fade_start)
        graph_parts.append(
            f"anoisesrc=color=white:amplitude={tail_noise:.5f}:duration={tail_duration:.3f}:sample_rate={sample_rate},"
            "aformat=channel_layouts=mono,highpass=f=420,lowpass=f=2800,"
            f"afade=t=out:st={tail_fade_start:.3f}:d={tail_fade_len:.3f}[tail]"
        )
        concat_labels.append("[tail]")

    if len(concat_labels) > 1:
        graph_parts.append(f"{''.join(concat_labels)}concat=n={len(concat_labels)}:v=0:a=1,{_CREST_FILTERS}[out]")
    else:
        graph_parts.append(f"[voice]anull,{_CREST_FILTERS}[out]")

    staged = TMP / f"{dst.stem}_stage.wav"
    run_ffmpeg(
        [
            "-i",
            str(src),
            "-vn",
            "-filter_complex",
            ";".join(graph_parts),
            "-map",
            "[out]",
            "-c:a",
            "pcm_s16le",
            str(staged),
        ]
    )
    try:
        params = loudnorm_params(staged)
        run_ffmpeg(["-i", str(staged), "-af", loudnorm_apply_filter(params), "-ar", str(sample_rate), *codec, str(dst)])
    finally:
        staged.unlink(missing_ok=True)


def wav_duration(path: Path) -> float | None:
    if path.suffix.lower() != ".wav" or not path.exists():
        return None
    with wave.open(str(path), "rb") as f:
        return f.getnframes() / float(f.getframerate())


_MANIFEST_LOCK = threading.Lock()


def append_manifest(rows: list[dict]) -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    manifest = BUILD / "gui_manifest.csv"
    with _MANIFEST_LOCK:
        exists = manifest.exists()
        with manifest.open("a", encoding="utf-8-sig", newline="") as f:
            fields = [
                "time",
                "id",
                "speaker",
                "voice",
                "preset",
                "signal_quality",
                "mic_clicks",
                "wav",
                "ogg",
                "duration_sec",
                "elevenlabs_character_cost",
                "elevenlabs_text_characters",
                "text",
            ]
            writer = csv.DictWriter(f, fieldnames=fields)
            if not exists:
                writer.writeheader()
            for row in rows:
                writer.writerow({key: row.get(key, "") for key in fields})


def generate_items(items: list[dict]) -> list[dict]:
    READY.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    now = time.strftime("%Y%m%d-%H%M%S")
    for index, item in enumerate(items, start=1):
        text = (item.get("text") or "").strip()
        if not text:
            continue
        line_id = safe_id(item.get("id") or f"line_{index:03d}", f"line_{index:03d}")
        speaker = (item.get("speaker") or "").strip()
        preset = item.get("preset") or "srs_cockpit"
        signal_quality = int(item.get("signalQuality") or 86)
        mic_clicks = bool(item.get("micClicks", True))
        sample_rate = int(item.get("sampleRate") or 22050)
        formats = item.get("formats") or ["ogg", "wav"]
        if isinstance(formats, str):
            formats = [formats]
        basename = safe_id(item.get("fileName") or line_id, line_id)
        if item.get("timestamp", True):
            basename = f"{basename}_{now}"
        basename = f"{basename}_{uuid.uuid4().hex[:8]}"

        source = TMP / f"{basename}.{tts.provider_source_format(item.get('provider') or 'edge')}"
        elevenlabs_usage, voice_label = tts.synthesize_item(item, source)

        row = {
            "time": now,
            "id": line_id,
            "speaker": speaker,
            "voice": voice_label,
            "preset": preset,
            "signal_quality": signal_quality,
            "mic_clicks": mic_clicks,
            "text": text,
            "wav": "",
            "ogg": "",
            "duration_sec": "",
            "elevenlabs_character_cost": "",
            "elevenlabs_text_characters": "",
            "files": [],
        }
        if elevenlabs_usage:
            row["elevenlabs"] = elevenlabs_usage
            row["elevenlabs_character_cost"] = elevenlabs_usage.get("character_count") or ""
            row["elevenlabs_text_characters"] = elevenlabs_usage.get("text_characters") or ""
        converted = False
        for fmt in formats:
            if fmt not in {"wav", "ogg"}:
                continue
            target = READY / f"{basename}.{fmt}"
            convert_audio(source, target, fmt, sample_rate, preset, signal_quality, mic_clicks)
            converted = True
            if fmt == "wav":
                row["wav"] = target.name
                duration = wav_duration(target)
                row["duration_sec"] = round(duration, 2) if duration is not None else ""
            if fmt == "ogg":
                row["ogg"] = target.name
            row["files"].append(
                {
                    "name": target.name,
                    "url": f"/files/{target.name}",
                    "path": str(target),
                    "format": fmt,
                    "size": target.stat().st_size,
                }
            )
        if converted:
            source.unlink(missing_ok=True)
        results.append(row)
    append_manifest(results)
    return results


def aggregate_elevenlabs_usage(results: list[dict]) -> dict:
    total_character_cost = 0
    total_text_characters = 0
    requests_count = 0
    request_ids: list[str] = []
    for row in results:
        usage = row.get("elevenlabs") or {}
        if not isinstance(usage, dict):
            continue
        requests_count += 1
        total_character_cost += int_or_none(usage.get("character_count")) or 0
        total_text_characters += int_or_none(usage.get("text_characters")) or 0
        request_id = usage.get("request_id")
        if request_id:
            request_ids.append(str(request_id))
    return {
        "requests": requests_count,
        "character_count": total_character_cost if requests_count else None,
        "text_characters": total_text_characters if requests_count else None,
        "request_ids": request_ids,
    }


def list_reference_voices() -> list[dict]:
    """Scan configured folders for reference voices (wav files for the XTTS worker)."""
    dirs: list[Path] = []
    project_refs = APP_ROOT / "references"
    if project_refs.is_dir():
        dirs.append(project_refs)
    extra = (os.environ.get("RF_XTTS_VOICES_DIR") or "").strip()
    if extra and Path(extra).is_dir():
        dirs.append(Path(extra))
    voices: list[dict] = []
    seen: set[str] = set()
    for directory in dirs:
        for path in sorted(directory.glob("*.wav")):
            key = str(path.resolve())
            if key in seen:
                continue
            seen.add(key)
            voices.append({"name": path.stem, "path": key, "size": path.stat().st_size})
    speaker = (os.environ.get("RF_XTTS_SPEAKER_WAV") or "").strip()
    if speaker and Path(speaker).exists():
        key = str(Path(speaker).resolve())
        if key not in seen:
            voices.insert(0, {"name": Path(speaker).stem, "path": key, "size": Path(speaker).stat().st_size})
    return voices


def tts_providers_status() -> dict:
    """Report TTS provider availability for the UI (edge/elevenlabs/piper/xtts/external)."""
    tts.sync_provider_registrations()
    return {
        "providers": {
            "edge": {"available": True},
            "elevenlabs": {"configured": bool(elevenlabs_api_key(required=False))},
            "piper": tts.piper_status(),
            "xtts": tts.xtts_status(),
            "external": tts.external_status(),
        }
    }


class PreviewError(Exception):
    """Validation/setup error for /api/tts/preview with a machine-readable code."""

    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.code = code


class ReplaceError(Exception):
    """Error for /api/replace (voice-over replacement) with a machine-readable code."""

    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.code = code


PREVIEW_TEXT_LIMIT = 1000

PIPER_SETUP_ERRORS: dict[str, tuple[str, str]] = {
    "disabled": (
        "piper_disabled",
        "Piper is not enabled: set RF_PIPER_ENABLED=1 in .env",
    ),
    "not_installed": (
        "piper_package_missing",
        "Piper package is not installed: pip install -r requirements-piper.txt",
    ),
    "model_dir_missing": (
        "piper_model_dir_missing",
        r"Piper model dir is missing: set RF_PIPER_MODEL_DIR or run scripts\download_piper_models.ps1",
    ),
    "no_models": (
        "piper_no_voices",
        r"No Piper models found: run scripts\download_piper_models.ps1 to download them",
    ),
}

XTTS_SETUP_ERRORS: dict[str, tuple[str, str]] = {
    "disabled": (
        "xtts_disabled",
        "XTTS is not enabled: set RF_XTTS_ENABLED=1 in .env",
    ),
    "not_installed": (
        "xtts_package_missing",
        "XTTS package is not installed: pip install -r requirements-xtts.txt",
    ),
    "speaker_wav_missing": (
        "xtts_speaker_wav_missing",
        "XTTS speaker wav is missing: set RF_XTTS_SPEAKER_WAV to a reference voice file",
    ),
    "cuda_not_available": (
        "xtts_cuda_not_available",
        "CUDA is not available (CPU fallback disabled); install CUDA torch or set RF_XTTS_DEVICE=cpu",
    ),
}

EXTERNAL_SETUP_ERRORS: dict[str, tuple[str, str]] = {
    "disabled": (
        "external_disabled",
        "External TTS is not enabled: set RF_EXTERNAL_TTS_ENABLED=1 in .env",
    ),
    "command_missing": (
        "external_command_missing",
        "External TTS command is not set: configure RF_EXTERNAL_TTS_COMMAND",
    ),
}


def tts_preview(payload: dict) -> dict:
    """Synthesize a short provider preview and return it as base64 audio."""
    provider = (payload.get("provider") or "edge").strip()
    voice = (payload.get("voice") or "").strip()
    text = (payload.get("text") or "").strip()
    if not text:
        raise PreviewError("Preview text is empty", "empty_text")
    if len(text) > PREVIEW_TEXT_LIMIT:
        raise PreviewError(f"Preview text is too long (max {PREVIEW_TEXT_LIMIT} characters)", "text_too_long")
    tts.sync_provider_registrations()
    if provider == "piper":
        status = tts.piper_status()
        if not status["available"]:
            code, message = PIPER_SETUP_ERRORS[status["reason"]]
            raise PreviewError(message, code)
    if provider == "xtts":
        status = tts.xtts_status()
        if not status["available"]:
            code, message = XTTS_SETUP_ERRORS[status["reason"]]
            raise PreviewError(message, code)
    if provider == "external":
        status = tts.external_status()
        if not status["available"]:
            code, message = EXTERNAL_SETUP_ERRORS[status["reason"]]
            raise PreviewError(message, code)
    if provider == "elevenlabs" and not elevenlabs_api_key(required=False):
        raise PreviewError("ELEVENLABS_API_KEY is not configured", "elevenlabs_not_configured")
    TMP.mkdir(parents=True, exist_ok=True)
    ext = tts.provider_source_format(provider)
    target = TMP / f"preview_{uuid.uuid4().hex[:8]}.{ext}"
    item: dict = {"provider": provider, "voice": voice, "text": text}
    if provider == "elevenlabs":
        item["elevenVoiceId"] = voice
    staged = TMP / f"preview_{uuid.uuid4().hex[:8]}_stage.wav"
    norm_target = TMP / f"preview_{uuid.uuid4().hex[:8]}_norm.wav"
    try:
        _, voice_label = tts.synthesize_item(item, target)
        run_ffmpeg(
            [
                "-i",
                str(target),
                "-af",
                f"aformat=channel_layouts=mono,{_CREST_FILTERS}",
                "-ar",
                "24000",
                "-c:a",
                "pcm_s16le",
                str(staged),
            ]
        )
        params = loudnorm_params(staged)
        run_ffmpeg(
            [
                "-i",
                str(staged),
                "-af",
                loudnorm_apply_filter(params),
                "-ar",
                "24000",
                "-c:a",
                "pcm_s16le",
                str(norm_target),
            ]
        )
        audio = norm_target.read_bytes()
    except tts.ExternalTTSError as exc:
        raise PreviewError(str(exc), f"external_{exc.code}") from exc
    finally:
        target.unlink(missing_ok=True)
        staged.unlink(missing_ok=True)
        norm_target.unlink(missing_ok=True)
    return {
        "provider": provider,
        "voice": voice_label,
        "mime": "audio/wav",
        "format": "wav",
        "characters": len(text),
        "audio_base64": base64.b64encode(audio).decode("ascii"),
    }


def list_library() -> list[dict]:
    READY.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(READY.glob("*")):
        if path.suffix.lower() not in {".wav", ".ogg", ".mp3"}:
            continue
        rows.append(
            {
                "name": path.name,
                "url": f"/files/{path.name}",
                "path": str(path),
                "format": path.suffix.lower().lstrip("."),
                "size": path.stat().st_size,
                "modified": path.stat().st_mtime,
            }
        )
    return rows


def probe_audio(path: Path) -> dict:
    """Read sample rate / channel layout of an audio file via ffmpeg."""
    result = subprocess.run(
        [ffmpeg(), "-hide_banner", "-nostats", "-i", str(path)],
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )
    text = (result.stdout or "") + (result.stderr or "")
    info: dict = {"codec": None, "sample_rate": None, "channels": 1}
    match = re.search(r"Audio:\s*([a-z0-9_]+)", text)
    if match:
        info["codec"] = match.group(1)
    match = re.search(r"(\d+)\s*Hz", text)
    if match:
        info["sample_rate"] = int(match.group(1))
    match = re.search(r"Hz,\s*([a-z0-9]+)", text)
    if match and match.group(1).startswith("stereo"):
        info["channels"] = 2
    return info


def _format_codec(fmt: str) -> list[str]:
    """ffmpeg encoding args for wav/ogg/mp3."""
    if fmt == "ogg":
        return ["-c:a", "libvorbis", "-q:a", "4"]
    if fmt == "mp3":
        return ["-c:a", "libmp3lame", "-b:a", "192k"]
    return ["-c:a", "pcm_s16le"]


def _synth_source(payload: dict, basename: str) -> tuple[Path, str]:
    """Synthesize a voice-over source file; returns (source_path, voice_label)."""
    provider = (payload.get("provider") or "external").strip() or "external"
    voice = (payload.get("voice") or "").strip()
    text = (payload.get("text") or "").strip()
    source = TMP / f"{basename}.{tts.provider_source_format(provider)}"
    item: dict = {"provider": provider, "text": text}
    if voice:
        item["voice"] = voice
    _, voice_label = tts.synthesize_item(item, source)
    return source, voice_label


def _convert_voiceover(
    source: Path,
    basename: str,
    fmt: str,
    sample_rate: int,
    channels: int,
    preset_id: str,
    signal_quality: int,
    mic_clicks: bool,
) -> Path:
    """Convert a synthesized source to the target format/rate/channels (radio preset applied)."""
    if fmt in {"wav", "ogg"}:
        converted = TMP / f"{basename}.{fmt}"
        convert_audio(source, converted, fmt, sample_rate, preset_id, signal_quality, mic_clicks)
    else:  # mp3: convert via wav stage
        staged_wav = TMP / f"{basename}_conv.wav"
        convert_audio(source, staged_wav, "wav", sample_rate, preset_id, signal_quality, mic_clicks)
        converted = TMP / f"{basename}.mp3"
        run_ffmpeg(["-i", str(staged_wav), *_format_codec("mp3"), str(converted)])
        staged_wav.unlink(missing_ok=True)
    if channels == 2:
        stereo = TMP / f"{basename}_stereo.{fmt}"
        run_ffmpeg(["-i", str(converted), "-af", "aformat=channel_layouts=stereo", *_format_codec(fmt), str(stereo)])
        converted.unlink(missing_ok=True)
        converted = stereo
    return converted


def replace_audio(payload: dict) -> dict:
    """Voice-over a text line and replace an existing audio file in place.

    The server is the single owner of the replacement: it probes the original
    format/sample rate, backs it up, synthesizes the text (or reuses a ready
    file passed as "source"), applies the radio preset, converts strictly to
    the original format, and atomically swaps the file via os.replace. The
    file name and mapResource keys stay untouched (DCS-safe).
    """
    raw_path = (payload.get("path") or "").strip()
    if not raw_path:
        raise ReplaceError("path is required", "missing_fields")
    target = Path(raw_path)
    if not target.exists() or not target.is_file():
        raise ReplaceError(f"Audio file not found: {target}", "file_not_found")
    ext = target.suffix.lower()
    if ext not in {".wav", ".ogg", ".mp3"}:
        raise ReplaceError(f"Unsupported audio format: {ext}", "bad_extension")

    probe = probe_audio(target)
    sample_rate = int(probe.get("sample_rate") or 24000)
    channels = int(probe.get("channels") or 1)
    fmt = ext.lstrip(".")
    preset_id = payload.get("preset") or "srs_cockpit"
    signal_quality = int(payload.get("signalQuality") or 86)
    mic_clicks = bool(payload.get("micClicks", True))

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    # Backup names are bound to the full path hash so that two different
    # missions (work dirs) with the same audio file name never share a
    # baseline: 'restore original' can never pull a file from mission A
    # while working on mission B.
    digest = hashlib.sha1(str(target.resolve()).lower().encode("utf-8")).hexdigest()[:12]
    key = f"{digest}_{target.stem}_{target.suffix.lstrip('.')}"
    backup = BACKUP_DIR / f"{key}_{stamp}.bak"
    shutil.copy2(target, backup)
    # baseline = first-ever state of this exact file path; "restore original"
    # always uses it, so repeated replacements never shadow the original audio.
    baseline = BACKUP_DIR / f"{key}.baseline.bak"
    if not baseline.exists():
        shutil.copy2(target, baseline)

    TMP.mkdir(parents=True, exist_ok=True)
    basename = f"replace_{uuid.uuid4().hex[:8]}"
    source: Path | None = None
    converted: Path | None = None
    tmp_target: Path | None = None
    try:
        ready_source = (payload.get("source") or "").strip()
        if ready_source and Path(ready_source).exists() and Path(ready_source).is_file():
            source = Path(ready_source)
            voice_label = "RadioForge draft"
        else:
            source, voice_label = _synth_source(payload, basename)

        converted = _convert_voiceover(
            source, basename, fmt, sample_rate, channels, preset_id, signal_quality, mic_clicks
        )

        tmp_target = target.with_name(f".{target.name}.tmp{uuid.uuid4().hex[:6]}")
        shutil.copy2(converted, tmp_target)
        os.replace(tmp_target, target)
        tmp_target = None

        duration = wav_duration(target) if fmt == "wav" else None
        return {
            "ok": True,
            "path": str(target),
            "format": fmt,
            "sample_rate": sample_rate,
            "channels": channels,
            "duration": duration,
            "voice": voice_label,
            "backup": str(backup),
            "baseline": str(baseline),
        }
    except tts.ExternalTTSError as exc:
        raise ReplaceError(str(exc), f"external_{exc.code}") from exc
    finally:
        if tmp_target is not None:
            tmp_target.unlink(missing_ok=True)
        if converted is not None:
            converted.unlink(missing_ok=True)
        if source is not None and source.parent == TMP:
            source.unlink(missing_ok=True)


def restore_audio(payload: dict) -> dict:
    """Restore a previously backed-up audio file into its original path."""
    raw_path = (payload.get("path") or "").strip()
    raw_backup = (payload.get("backup") or "").strip()
    if not raw_path or not raw_backup:
        raise ReplaceError("path and backup are required", "missing_fields")
    target = Path(raw_path)
    backup = Path(raw_backup)
    if not target.exists() or not target.is_file():
        raise ReplaceError(f"Audio file not found: {target}", "file_not_found")
    if not backup.exists() or not backup.is_file():
        raise ReplaceError(f"Backup not found: {backup}", "backup_not_found")
    tmp = target.with_name(f".{target.name}.restore{uuid.uuid4().hex[:6]}")
    shutil.copy2(backup, tmp)
    os.replace(tmp, target)
    return {"ok": True, "path": str(target), "restored": str(backup)}


def synthesize_audio(payload: dict) -> dict:
    """Synthesize a voice-over draft file into build/dcs-ready (no replacement).

    Returns {ok, path, url, format, sample_rate, duration, voice} so the client
    can listen first and later apply it via /api/replace with "source".
    """
    text = (payload.get("text") or "").strip()
    if not text:
        raise ReplaceError("text is required", "missing_fields")
    preset_id = payload.get("preset") or "srs_cockpit"
    signal_quality = int(payload.get("signalQuality") or 86)
    mic_clicks = bool(payload.get("micClicks", True))
    sample_rate = int(payload.get("sampleRate") or 22050)
    fmt = (payload.get("format") or "ogg").strip().lower()
    if fmt not in {"ogg", "wav", "mp3"}:
        fmt = "ogg"
    match_path = (payload.get("matchPath") or "").strip()
    matched = False
    if match_path and Path(match_path).exists():
        probe = probe_audio(Path(match_path))
        probe_rate = probe.get("sample_rate")
        if probe_rate:
            sample_rate = int(probe_rate)
        probe_ext = Path(match_path).suffix.lower().lstrip(".")
        if probe_ext in {"ogg", "wav", "mp3"}:
            fmt = probe_ext
        matched = True
    file_name = safe_id((payload.get("fileName") or "").strip() or "voiceover", "voiceover")

    READY.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    basename = f"{file_name}_{time.strftime('%Y%m%d-%H%M%S')}_{uuid.uuid4().hex[:6]}"
    source: Path | None = None
    converted: Path | None = None
    try:
        source, voice_label = _synth_source(payload, basename)
        converted = _convert_voiceover(source, basename, fmt, sample_rate, 1, preset_id, signal_quality, mic_clicks)
        target = READY / f"{basename}.{fmt}"
        os.replace(converted, target)
        converted = None
        duration = wav_duration(target) if fmt == "wav" else None
        return {
            "ok": True,
            "path": str(target),
            "url": f"/files/{target.name}",
            "format": fmt,
            "sample_rate": sample_rate,
            "duration": duration,
            "voice": voice_label,
            "matched": matched,
        }
    except tts.ExternalTTSError as exc:
        raise ReplaceError(str(exc), f"external_{exc.code}") from exc
    finally:
        if converted is not None:
            converted.unlink(missing_ok=True)
        if source is not None:
            source.unlink(missing_ok=True)


class Handler(BaseHTTPRequestHandler):
    server_version = "DCSVoiceStudio/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path == "/api/health":
            json_response(self, {"ok": True, "root": str(ROOT)})
            return
        if path == "/api/tts/providers":
            load_local_env()
            json_response(self, tts_providers_status())
            return
        if path == "/api/tts/references":
            load_local_env()
            json_response(self, {"voices": list_reference_voices()})
            return
        if path == "/api/voices":
            json_response(self, {"voices": VOICE_CATALOG, "roles": ROLE_PRESETS})
            return
        if path == "/api/presets":
            json_response(self, {"presets": RADIO_PRESETS})
            return
        if path == "/api/library":
            json_response(self, {"files": list_library()})
            return
        if path == "/api/elevenlabs/status":
            load_local_env()
            json_response(self, {"configured": bool(elevenlabs_api_key(required=False))})
            return
        if path == "/api/elevenlabs/voices":
            load_local_env()
            try:
                json_response(self, {"configured": True, "voices": list_elevenlabs_voices()})
            except Exception as exc:  # noqa: BLE001 - local tool, show actionable UI error.
                json_response(self, {"configured": False, "error": str(exc), "voices": []}, 500)
            return
        if path == "/api/elevenlabs/usage":
            load_local_env()
            try:
                json_response(
                    self,
                    {
                        "configured": True,
                        "subscription": get_elevenlabs_subscription(),
                        "models": list_elevenlabs_models(),
                    },
                )
            except Exception as exc:  # noqa: BLE001 - local tool, show actionable UI error.
                json_response(
                    self,
                    {"configured": False, "error": str(exc), "subscription": {}, "models": []},
                    500,
                )
            return
        if path.startswith("/files/"):
            self.serve_file(READY / path.removeprefix("/files/"))
            return
        if path.startswith("/previews/"):
            self.serve_file(PREVIEWS / path.removeprefix("/previews/"))
            return
        if path == "/":
            self.serve_file(WEB / "index.html")
            return
        self.serve_file(WEB / path.lstrip("/"))

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path not in {
            "/api/generate",
            "/api/elevenlabs/design",
            "/api/elevenlabs/create-voice",
            "/api/tts/preview",
            "/api/replace",
            "/api/replace/restore",
            "/api/synthesize",
        }:
            text_response(self, "not found", 404)
            return
        try:
            length = int(self.headers.get("Content-Length") or "0")
            raw = self.rfile.read(length)
            payload = json.loads(raw.decode("utf-8"))
            load_local_env()
            tts.sync_provider_registrations()
            if parsed.path == "/api/generate":
                items = payload.get("items") or [payload]
                results = generate_items(items)
                json_response(
                    self,
                    {
                        "ok": True,
                        "results": results,
                        "library": list_library(),
                        "elevenlabs": aggregate_elevenlabs_usage(results),
                    },
                )
                return
            if parsed.path == "/api/elevenlabs/design":
                result = design_elevenlabs_voice(payload)
                json_response(self, {"ok": True, **result})
                return
            if parsed.path == "/api/elevenlabs/create-voice":
                result = create_elevenlabs_voice(payload)
                json_response(self, {"ok": True, "voice": result})
                return
            if parsed.path == "/api/tts/preview":
                json_response(self, {"ok": True, **tts_preview(payload)})
                return
            if parsed.path == "/api/replace":
                json_response(self, replace_audio(payload))
                return
            if parsed.path == "/api/synthesize":
                json_response(self, synthesize_audio(payload))
                return
            if parsed.path == "/api/replace/restore":
                json_response(self, restore_audio(payload))
                return
        except PreviewError as exc:
            json_response(self, {"ok": False, "error": str(exc), "code": exc.code}, 400)
        except ReplaceError as exc:
            json_response(self, {"ok": False, "error": str(exc), "code": exc.code}, 400)
            json_response(self, {"ok": False, "error": str(exc), "code": exc.code}, 400)
        except Exception as exc:  # noqa: BLE001 - small local tool, return useful UI error.
            json_response(self, {"ok": False, "error": str(exc)}, 500)

    def serve_file(self, path: Path) -> None:
        try:
            if str(path).startswith(str(READY)):
                base = READY
            elif str(path).startswith(str(PREVIEWS)):
                base = PREVIEWS
            else:
                base = WEB
            resolved = path.resolve()
            if base.resolve() not in resolved.parents and resolved != base.resolve():
                text_response(self, "forbidden", 403)
                return
            if not resolved.exists() or not resolved.is_file():
                text_response(self, "not found", 404)
                return
            ctype = mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
            raw = resolved.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        except OSError as exc:
            text_response(self, str(exc), 500)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} - {fmt % args}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", help="Open the browser after starting the local studio.")
    args = parser.parse_args(argv)

    load_local_env()
    tts.sync_provider_registrations()
    if not WEB.exists():
        raise RuntimeError(f"web assets were not found: {WEB}")
    READY.mkdir(parents=True, exist_ok=True)
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    if not shutil.which(ffmpeg()) and not Path(ffmpeg()).exists():
        raise RuntimeError("ffmpeg binary was not found")

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}"
    print(f"DCS RadioForge: {url}")
    print(f"DCS-ready output: {READY}")
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
