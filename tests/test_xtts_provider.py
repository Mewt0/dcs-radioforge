"""Tests for the optional XTTS (Coqui, GPU) provider scaffold (no torch/TTS installed)."""

from __future__ import annotations

import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from typing import ClassVar
from unittest import mock

import server
import tts


class FakeTTS:
    """Stands in for TTS.api.TTS: records tts_to_file calls and writes a stub wav."""

    tts_to_file_calls: ClassVar[list[dict]] = []

    def __init__(self, model_name=None, device=None) -> None:
        self.model_name = model_name
        self.device = device

    def tts_to_file(self, **kwargs) -> None:
        FakeTTS.tts_to_file_calls.append(kwargs)
        Path(kwargs["file_path"]).write_bytes(b"XTTS-WAV")


def install_fake_xtts(cuda_available: bool = True) -> None:
    torch_mod = types.ModuleType("torch")
    torch_mod.cuda = types.SimpleNamespace(is_available=lambda: cuda_available)
    sys.modules["torch"] = torch_mod
    api = types.ModuleType("TTS.api")
    api.TTS = FakeTTS
    tts_pkg = types.ModuleType("TTS")
    tts_pkg.api = api
    sys.modules["TTS"] = tts_pkg
    sys.modules["TTS.api"] = api
    FakeTTS.tts_to_file_calls.clear()


def remove_fake_xtts() -> None:
    sys.modules.pop("torch", None)
    sys.modules.pop("TTS", None)
    sys.modules.pop("TTS.api", None)


class XttsUnavailableTest(unittest.TestCase):
    def tearDown(self) -> None:
        remove_fake_xtts()
        tts.TTS_PROVIDERS.pop("xtts", None)

    def test_import_tts_without_xtts_deps(self) -> None:
        self.assertNotIn("torch", sys.modules)
        tts.sync_xtts_registration()  # must not crash
        self.assertNotIn("xtts", tts.TTS_PROVIDERS)
        status = tts.xtts_status()
        self.assertFalse(status["available"])
        self.assertIn("reason", status)

    def test_xtts_unavailable_does_not_break_others(self) -> None:
        with mock.patch.dict(os.environ, {"RF_XTTS_ENABLED": "1"}):
            remove_fake_xtts()
            tts.sync_xtts_registration()
            self.assertNotIn("xtts", tts.TTS_PROVIDERS)
            with self.assertRaisesRegex(RuntimeError, "XTTS provider is unavailable"):
                tts.synthesize_item({"text": "hi", "provider": "xtts"}, Path("x.wav"))

        # edge still works
        async def fake_edge(text: str, voice: str, rate: str, pitch: str, volume: str, target: Path) -> None:
            pass

        original = tts.synthesize_mp3
        tts.synthesize_mp3 = fake_edge
        try:
            usage, voice_label = tts.synthesize_item({"text": "hi"}, Path("x.mp3"))
            self.assertIsNone(usage)
            self.assertEqual(voice_label, "ru-RU-DmitryNeural")
        finally:
            tts.synthesize_mp3 = original

    def test_cuda_not_available(self) -> None:
        install_fake_xtts(cuda_available=False)
        with tempfile.TemporaryDirectory() as tmp:
            speaker = Path(tmp) / "ref.wav"
            speaker.write_bytes(b"wav")
            with mock.patch.dict(os.environ, {"RF_XTTS_ENABLED": "1", "RF_XTTS_SPEAKER_WAV": str(speaker)}):
                status = tts.xtts_status()
        self.assertFalse(status["available"])
        self.assertEqual(status["reason"], "cuda_not_available")

    def test_speaker_wav_missing(self) -> None:
        install_fake_xtts()
        with mock.patch.dict(os.environ, {"RF_XTTS_ENABLED": "1"}):
            status = tts.xtts_status()
        self.assertEqual(status["reason"], "speaker_wav_missing")

    def test_preview_xtts_unavailable_structured_error(self) -> None:
        with mock.patch.dict(os.environ, {"RF_XTTS_ENABLED": "0"}), self.assertRaises(server.PreviewError) as ctx:
            server.tts_preview({"provider": "xtts", "text": "hi"})
        self.assertEqual(ctx.exception.code, "xtts_disabled")

    def test_preview_xtts_package_missing(self) -> None:
        remove_fake_xtts()
        with mock.patch.dict(os.environ, {"RF_XTTS_ENABLED": "1"}), self.assertRaises(server.PreviewError) as ctx:
            server.tts_preview({"provider": "xtts", "text": "hi"})
        self.assertEqual(ctx.exception.code, "xtts_package_missing")


class XttsAvailableTest(unittest.TestCase):
    def tearDown(self) -> None:
        remove_fake_xtts()
        tts.TTS_PROVIDERS.pop("xtts", None)

    def test_registry_contains_xtts_only_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            speaker = Path(tmp) / "ref.wav"
            speaker.write_bytes(b"wav")
            install_fake_xtts()
            with mock.patch.dict(
                os.environ,
                {"RF_XTTS_ENABLED": "1", "RF_XTTS_SPEAKER_WAV": str(speaker), "RF_XTTS_DEVICE": "cpu"},
            ):
                tts.sync_xtts_registration()
                self.assertIn("xtts", tts.TTS_PROVIDERS)
                status = tts.xtts_status()
                self.assertTrue(status["available"])
                self.assertEqual(status["device"], "cpu")
                self.assertIn("model", status)
                self.assertIn("speaker_wav", status)
            with mock.patch.dict(os.environ, {"RF_XTTS_ENABLED": "0", "RF_XTTS_SPEAKER_WAV": str(speaker)}):
                tts.sync_xtts_registration()
                self.assertNotIn("xtts", tts.TTS_PROVIDERS)

    def test_xtts_provider_writes_wav(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            speaker = Path(tmp) / "ref.wav"
            speaker.write_bytes(b"wav")
            install_fake_xtts()
            with mock.patch.dict(
                os.environ,
                {"RF_XTTS_ENABLED": "1", "RF_XTTS_SPEAKER_WAV": str(speaker), "RF_XTTS_DEVICE": "cpu"},
            ):
                target = Path(tmp) / "out.wav"
                usage = tts.xtts_provider({"text": "привет"}, target)
                self.assertIsNone(usage)
                self.assertTrue(target.exists())
                self.assertEqual(target.read_bytes(), b"XTTS-WAV")
                call = FakeTTS.tts_to_file_calls[-1]
                self.assertEqual(call["language"], "ru")
                self.assertTrue(str(call["speaker_wav"]).endswith("ref.wav"))
                self.assertEqual(call["file_path"], str(target))

    def test_xtts_provider_language_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            speaker = Path(tmp) / "ref.wav"
            speaker.write_bytes(b"wav")
            install_fake_xtts()
            with mock.patch.dict(
                os.environ,
                {"RF_XTTS_ENABLED": "1", "RF_XTTS_SPEAKER_WAV": str(speaker), "RF_XTTS_DEVICE": "cpu"},
            ):
                target = Path(tmp) / "en.wav"
                tts.xtts_provider({"text": "hello world"}, target)
                self.assertEqual(FakeTTS.tts_to_file_calls[-1]["language"], "en")

    def test_status_endpoint_includes_xtts(self) -> None:
        payload = server.tts_providers_status()
        self.assertIn("xtts", payload["providers"])
        self.assertIn("available", payload["providers"]["xtts"])


if __name__ == "__main__":
    unittest.main()
