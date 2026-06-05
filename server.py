from __future__ import annotations

import argparse
import asyncio
import base64
import csv
import json
import mimetypes
import os
import shutil
import subprocess
import sys
import time
import wave
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error as urlerror
from urllib import parse, request
from urllib.parse import unquote, urlparse

import edge_tts
import imageio_ffmpeg


SOURCE_ROOT = Path(__file__).resolve().parent
RESOURCE_ROOT = Path(getattr(sys, "_MEIPASS", SOURCE_ROOT))
APP_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else SOURCE_ROOT
ROOT = APP_ROOT
WEB = RESOURCE_ROOT / "web"
BUILD = APP_ROOT / "build"
READY = BUILD / "dcs-ready"
TMP = BUILD / "_tmp_mp3"
PREVIEWS = BUILD / "elevenlabs-previews"
ELEVENLABS_HOST = "https://api.elevenlabs.io"
ELEVENLABS_V1 = f"{ELEVENLABS_HOST}/v1"

VOICE_CATALOG = [
    {"name": "ru-RU-DmitryNeural", "lang": "ru", "gender": "Male", "role": "Russian controller", "tone": "Friendly, Positive"},
    {"name": "ru-RU-SvetlanaNeural", "lang": "ru", "gender": "Female", "role": "Russian package / ops", "tone": "Friendly, Positive"},
    {"name": "en-US-ChristopherNeural", "lang": "en", "gender": "Male", "role": "AWACS / command", "tone": "Reliable, Authority"},
    {"name": "en-US-SteffanNeural", "lang": "en", "gender": "Male", "role": "JTAC / controller", "tone": "Rational"},
    {"name": "en-US-EricNeural", "lang": "en", "gender": "Male", "role": "Tactical brief", "tone": "Rational"},
    {"name": "en-GB-ThomasNeural", "lang": "en", "gender": "Male", "role": "FAC / coalition", "tone": "Calm, British"},
    {"name": "en-CA-LiamNeural", "lang": "en", "gender": "Male", "role": "Flight lead", "tone": "Calm, clear"},
    {"name": "en-AU-WilliamMultilingualNeural", "lang": "en", "gender": "Male", "role": "Package lead", "tone": "Friendly, Positive"},
    {"name": "en-US-AriaNeural", "lang": "en", "gender": "Female", "role": "Intel / briefing", "tone": "Positive, Confident"},
    {"name": "en-GB-SoniaNeural", "lang": "en", "gender": "Female", "role": "British ops", "tone": "Friendly, Positive"},
]

ROLE_PRESETS = [
    {"id": "ru_gci", "label": "RU GCI", "voice": "ru-RU-DmitryNeural", "rate": "+3%", "pitch": "-10Hz", "preset": "srs_old_soviet"},
    {"id": "ru_raven", "label": "RU RAVEN", "voice": "ru-RU-SvetlanaNeural", "rate": "+1%", "pitch": "-3Hz", "preset": "srs_cockpit"},
    {"id": "en_awacs", "label": "EN AWACS", "voice": "en-US-ChristopherNeural", "rate": "-2%", "pitch": "-10Hz", "preset": "srs_awacs"},
    {"id": "en_jtac", "label": "EN JTAC", "voice": "en-US-SteffanNeural", "rate": "+1%", "pitch": "-8Hz", "preset": "srs_vhf_am"},
    {"id": "en_flightlead", "label": "EN FLIGHT LEAD", "voice": "en-CA-LiamNeural", "rate": "+0%", "pitch": "-6Hz", "preset": "srs_uhf_am"},
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
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def text_response(handler: BaseHTTPRequestHandler, text: str, status: int = 200) -> None:
    raw = text.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/plain; charset=utf-8")
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
) -> bytes | dict:
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
    except urlerror.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ElevenLabs API error {exc.code}: {detail}") from exc
    if binary:
        return raw
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


async def synthesize_mp3(text: str, voice: str, rate: str, pitch: str, volume: str, target: Path) -> None:
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch, volume=volume)
    await communicate.save(str(target))


def synthesize_elevenlabs_mp3(
    text: str,
    voice_id: str,
    model_id: str,
    language_code: str,
    target: Path,
) -> None:
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
    raw = elevenlabs_request(
        "POST",
        f"/text-to-speech/{parse.quote(voice_id)}",
        payload=payload,
        query={"output_format": "mp3_44100_128"},
        binary=True,
    )
    target.write_bytes(raw)  # type: ignore[arg-type]


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


def clamp(value: int | float, low: int | float, high: int | float) -> int | float:
    return max(low, min(high, value))


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
    base_filters = [
        f"aformat=channel_layouts=mono",
        f"aresample={sample_rate}",
        *preset["filters"],
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
        graph_parts.append(
            f"anoisesrc=color=white:amplitude={noise:.5f}:sample_rate={sample_rate}[noise]"
        )
        graph_parts.append(
            "[base][noise]amix=inputs=2:duration=first:dropout_transition=0,alimiter=limit=0.95[voice]"
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
        graph_parts.append(f"{''.join(concat_labels)}concat=n={len(concat_labels)}:v=0:a=1[out]")
    else:
        graph_parts.append("[voice]anull[out]")

    run_ffmpeg(["-i", str(src), "-vn", "-filter_complex", ";".join(graph_parts), "-map", "[out]", *codec, str(dst)])


def wav_duration(path: Path) -> float | None:
    if path.suffix.lower() != ".wav" or not path.exists():
        return None
    with wave.open(str(path), "rb") as f:
        return f.getnframes() / float(f.getframerate())


def append_manifest(rows: list[dict]) -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    manifest = BUILD / "gui_manifest.csv"
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
        provider = item.get("provider") or "edge"
        voice = item.get("voice") or "ru-RU-DmitryNeural"
        eleven_voice_id = item.get("elevenVoiceId") or ""
        eleven_model = item.get("elevenModel") or "eleven_multilingual_v2"
        eleven_language = item.get("elevenLanguage") or item.get("lang") or ""
        rate = item.get("rate") or "+0%"
        pitch = item.get("pitch") or "+0Hz"
        volume = item.get("volume") or "+0%"
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

        mp3 = TMP / f"{basename}.mp3"
        if provider == "elevenlabs":
            synthesize_elevenlabs_mp3(text, eleven_voice_id, eleven_model, eleven_language, mp3)
            voice_label = eleven_voice_id
        else:
            asyncio.run(synthesize_mp3(text, voice, rate, pitch, volume, mp3))
            voice_label = voice

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
            "files": [],
        }
        for fmt in formats:
            if fmt not in {"wav", "ogg"}:
                continue
            target = READY / f"{basename}.{fmt}"
            convert_audio(mp3, target, fmt, sample_rate, preset, signal_quality, mic_clicks)
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
        results.append(row)
    append_manifest(results)
    return results


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


class Handler(BaseHTTPRequestHandler):
    server_version = "DCSVoiceStudio/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path == "/api/health":
            json_response(self, {"ok": True, "root": str(ROOT)})
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
        if parsed.path not in {"/api/generate", "/api/elevenlabs/design", "/api/elevenlabs/create-voice"}:
            text_response(self, "not found", 404)
            return
        try:
            length = int(self.headers.get("Content-Length") or "0")
            raw = self.rfile.read(length)
            payload = json.loads(raw.decode("utf-8"))
            load_local_env()
            if parsed.path == "/api/generate":
                items = payload.get("items") or [payload]
                results = generate_items(items)
                json_response(self, {"ok": True, "results": results, "library": list_library()})
                return
            if parsed.path == "/api/elevenlabs/design":
                result = design_elevenlabs_voice(payload)
                json_response(self, {"ok": True, **result})
                return
            if parsed.path == "/api/elevenlabs/create-voice":
                result = create_elevenlabs_voice(payload)
                json_response(self, {"ok": True, "voice": result})
                return
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
