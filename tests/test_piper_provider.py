"""Tests for the optional local Piper provider (no real piper/onnxruntime needed)."""

from __future__ import annotations

import json
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


class FakePiperVoice:
    """Stands in for piper.PiperVoice: records load() and synthesize() calls."""

    load_calls: ClassVar[list[tuple[str, str | None]]] = []

    def __init__(self) -> None:
        self.synthesize_calls: list[tuple] = []

    @classmethod
    def load(cls, model_path: str, config_path: str | None = None) -> FakePiperVoice:
        FakePiperVoice.load_calls.append((model_path, config_path))
        return cls()

    def synthesize(self, text: str, wav_file) -> None:
        self.synthesize_calls.append((text, wav_file))
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(22050)
        wav_file.writeframes(b"\x00" * 100)


def install_fake_piper() -> None:
    fake = types.ModuleType("piper")
    fake.PiperVoice = FakePiperVoice
    FakePiperVoice.load_calls.clear()
    sys.modules["piper"] = fake


def remove_fake_piper() -> None:
    sys.modules.pop("piper", None)


class PiperProviderTest(unittest.TestCase):
    def setUp(self) -> None:
        self._env = mock.patch.dict(os.environ, {}, clear=False)

    def tearDown(self) -> None:
        self._env.stop()
        remove_fake_piper()
        tts.TTS_PROVIDERS.pop("piper", None)


class PiperUnavailableTest(PiperProviderTest):
    def test_import_tts_without_piper_deps(self) -> None:
        self.assertNotIn("piper", sys.modules)
        tts.sync_piper_registration()  # must not crash
        self.assertNotIn("piper", tts.TTS_PROVIDERS)
        status = tts.piper_status()
        self.assertFalse(status["available"])
        self.assertIn("reason", status)

    def test_piper_unavailable_does_not_break_edge(self) -> None:
        with mock.patch.dict(os.environ, {"RF_PIPER_ENABLED": "1"}):
            remove_fake_piper()
            tts.sync_piper_registration()
            self.assertNotIn("piper", tts.TTS_PROVIDERS)
            with self.assertRaisesRegex(RuntimeError, "Piper provider is unavailable"):
                tts.synthesize_item({"text": "hi", "provider": "piper"}, Path("x.wav"))

        # edge still works fine
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


class PiperAvailableTest(PiperProviderTest):
    def _env_with_models(self, model_dir: Path) -> mock._patch:
        return mock.patch.dict(
            os.environ,
            {"RF_PIPER_ENABLED": "1", "RF_PIPER_MODEL_DIR": str(model_dir)},
        )

    def test_registry_contains_piper_only_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            model_dir = Path(tmp)
            (model_dir / "ru_RU-denis-medium.onnx").write_bytes(b"fake")
            (model_dir / "ru_RU-denis-medium.onnx.json").write_text("{}", encoding="utf-8")
            install_fake_piper()
            with self._env_with_models(model_dir):
                tts.sync_piper_registration()
                self.assertIn("piper", tts.TTS_PROVIDERS)
                status = tts.piper_status()
                self.assertTrue(status["available"])
                self.assertEqual(status["voices"], ["ru_RU-denis-medium"])
                self.assertEqual(status["default_voice"], "ru_RU-denis-medium")
            with mock.patch.dict(os.environ, {"RF_PIPER_ENABLED": "0", "RF_PIPER_MODEL_DIR": str(model_dir)}):
                tts.sync_piper_registration()
                self.assertNotIn("piper", tts.TTS_PROVIDERS)

    def test_piper_provider_synthesizes_wav(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            model_dir = Path(tmp)
            (model_dir / "ru_RU-denis-medium.onnx").write_bytes(b"fake")
            (model_dir / "ru_RU-denis-medium.onnx.json").write_text("{}", encoding="utf-8")
            install_fake_piper()
            with self._env_with_models(model_dir):
                target = Path(tmp) / "out.wav"
                usage = tts.piper_provider({"text": "привет", "voice": "ru_RU-denis-medium"}, target)
                self.assertIsNone(usage)
                self.assertTrue(target.exists())
                self.assertGreater(target.stat().st_size, 0)
                model_path, config_path = FakePiperVoice.load_calls[-1]
                self.assertEqual(Path(model_path).name, "ru_RU-denis-medium.onnx")
                self.assertEqual(Path(config_path).name, "ru_RU-denis-medium.onnx.json")

    def test_synthesize_item_uses_piper_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            model_dir = Path(tmp)
            (model_dir / "ru_RU-denis-medium.onnx").write_bytes(b"fake")
            install_fake_piper()
            with self._env_with_models(model_dir):
                tts.sync_piper_registration()
                target = Path(tmp) / "replica.wav"
                usage, voice_label = tts.synthesize_item({"text": "привет", "provider": "piper"}, target)
                self.assertIsNone(usage)
                self.assertEqual(voice_label, "ru_RU-denis-medium")
                self.assertTrue(target.exists())
                self.assertGreater(target.stat().st_size, 0)

    def test_providers_status_json(self) -> None:
        payload = server.tts_providers_status()
        providers = payload["providers"]
        self.assertTrue(providers["edge"]["available"])
        self.assertIn("configured", providers["elevenlabs"])
        self.assertIn("available", providers["piper"])
        json.dumps(payload)  # must serialize


if __name__ == "__main__":
    unittest.main()
