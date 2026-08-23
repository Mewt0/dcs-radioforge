"""Tests for POST /api/tts/preview (server.tts_preview) and Piper diagnostics codes."""

from __future__ import annotations

import base64
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import server
import tts
from tests.test_piper_provider import install_fake_piper, remove_fake_piper

FAKE_LOUDNESS = {"input_i": "-36.0", "input_tp": "-27.9", "input_lra": "1.2", "input_thresh": "-46.5"}


def _fake_loudnorm_params(path: Path) -> dict:
    return dict(FAKE_LOUDNESS)


def _fake_run_ffmpeg(args: list[str]) -> None:
    """Stand-in for server.run_ffmpeg: copy first input file to the output path."""
    src = args[args.index("-i") + 1]
    dst = args[-1]
    Path(dst).write_bytes(Path(src).read_bytes())


class PreviewValidationTest(unittest.TestCase):
    def test_empty_text_rejected(self) -> None:
        with self.assertRaises(server.PreviewError) as ctx:
            server.tts_preview({"provider": "edge", "text": "   "})
        self.assertEqual(ctx.exception.code, "empty_text")

    def test_long_text_rejected(self) -> None:
        with self.assertRaises(server.PreviewError) as ctx:
            server.tts_preview({"provider": "edge", "text": "x" * 1001})
        self.assertEqual(ctx.exception.code, "text_too_long")

    def test_lesson_length_text_accepted(self) -> None:
        async def fake_synth(text: str, voice: str, rate: str, pitch: str, volume: str, target: Path) -> None:
            Path(target).write_bytes(b"MP3")

        original = tts.synthesize_mp3
        tts.synthesize_mp3 = fake_synth
        try:
            with (
                mock.patch.object(server, "run_ffmpeg", side_effect=_fake_run_ffmpeg),
                mock.patch.object(server, "loudnorm_params", side_effect=_fake_loudnorm_params),
            ):
                result = server.tts_preview({"provider": "edge", "text": "x" * 1000})
        finally:
            tts.synthesize_mp3 = original
        self.assertEqual(result["characters"], 1000)


class PreviewSynthTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_tmp = server.TMP
        server.TMP = Path(self._tmp.name)
        self._ffmpeg_patch = mock.patch.object(server, "run_ffmpeg", side_effect=_fake_run_ffmpeg)
        self._ffmpeg_patch.start()
        self._loudness_patch = mock.patch.object(server, "loudnorm_params", side_effect=_fake_loudnorm_params)
        self._loudness_patch.start()

    def tearDown(self) -> None:
        self._loudness_patch.stop()
        self._ffmpeg_patch.stop()
        server.TMP = self._orig_tmp
        self._tmp.cleanup()
        remove_fake_piper()
        tts.TTS_PROVIDERS.pop("piper", None)

    def test_edge_preview_with_mocked_synth(self) -> None:
        async def fake_synth(text: str, voice: str, rate: str, pitch: str, volume: str, target: Path) -> None:
            Path(target).write_bytes(b"MP3-DUMMY")

        original = tts.synthesize_mp3
        tts.synthesize_mp3 = fake_synth
        try:
            result = server.tts_preview({"provider": "edge", "voice": "ru-RU-DmitryNeural", "text": "привет"})
        finally:
            tts.synthesize_mp3 = original
        self.assertEqual(result["provider"], "edge")
        self.assertEqual(result["voice"], "ru-RU-DmitryNeural")
        self.assertEqual(result["mime"], "audio/wav")
        self.assertEqual(result["format"], "wav")
        self.assertEqual(base64.b64decode(result["audio_base64"]), b"MP3-DUMMY")
        self.assertEqual(result["characters"], 6)

    def test_two_hundred_chars_accepted(self) -> None:
        async def fake_synth(text: str, voice: str, rate: str, pitch: str, volume: str, target: Path) -> None:
            Path(target).write_bytes(b"MP3")

        original = tts.synthesize_mp3
        tts.synthesize_mp3 = fake_synth
        try:
            result = server.tts_preview({"provider": "edge", "text": "x" * 200})
        finally:
            tts.synthesize_mp3 = original
        self.assertEqual(result["characters"], 200)

    def test_piper_preview_with_mocked_provider(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            model_dir = Path(tmp)
            (model_dir / "ru_RU-denis-medium.onnx").write_bytes(b"fake")
            (model_dir / "ru_RU-denis-medium.onnx.json").write_text("{}", encoding="utf-8")
            install_fake_piper()
            with mock.patch.dict(os.environ, {"RF_PIPER_ENABLED": "1", "RF_PIPER_MODEL_DIR": str(model_dir)}):
                result = server.tts_preview({"provider": "piper", "voice": "ru_RU-denis-medium", "text": "привет"})
        self.assertEqual(result["provider"], "piper")
        self.assertEqual(result["mime"], "audio/wav")
        self.assertEqual(result["format"], "wav")
        self.assertGreater(len(base64.b64decode(result["audio_base64"])), 0)

    def test_elevenlabs_preview_with_mocked_synth(self) -> None:
        def fake_el(text: str, voice_id: str, model_id: str, language_code: str, target: Path) -> dict:
            Path(target).write_bytes(b"MP3-ELEVEN")
            return {"character_count": 10, "request_id": "r", "model_id": model_id, "text_characters": len(text)}

        original = server.synthesize_elevenlabs_mp3
        server.synthesize_elevenlabs_mp3 = fake_el
        try:
            with mock.patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test-key"}):
                result = server.tts_preview({"provider": "elevenlabs", "voice": "vc-1", "text": "привет"})
        finally:
            server.synthesize_elevenlabs_mp3 = original
        self.assertEqual(result["mime"], "audio/wav")
        self.assertEqual(result["voice"], "vc-1")
        self.assertEqual(base64.b64decode(result["audio_base64"]), b"MP3-ELEVEN")

    def test_elevenlabs_not_configured(self) -> None:
        with mock.patch.dict(os.environ, {"ELEVENLABS_API_KEY": ""}), self.assertRaises(server.PreviewError) as ctx:
            server.tts_preview({"provider": "elevenlabs", "voice": "vc-1", "text": "hi"})
        self.assertEqual(ctx.exception.code, "elevenlabs_not_configured")


class PiperErrorCodesTest(unittest.TestCase):
    def tearDown(self) -> None:
        remove_fake_piper()
        tts.TTS_PROVIDERS.pop("piper", None)

    def test_piper_disabled(self) -> None:
        with mock.patch.dict(os.environ, {"RF_PIPER_ENABLED": "0"}), self.assertRaises(server.PreviewError) as ctx:
            server.tts_preview({"provider": "piper", "text": "hi"})
        self.assertEqual(ctx.exception.code, "piper_disabled")

    def test_piper_package_missing(self) -> None:
        remove_fake_piper()
        with mock.patch.dict(os.environ, {"RF_PIPER_ENABLED": "1"}), self.assertRaises(server.PreviewError) as ctx:
            server.tts_preview({"provider": "piper", "text": "hi"})
        self.assertEqual(ctx.exception.code, "piper_package_missing")

    def test_piper_model_dir_missing(self) -> None:
        install_fake_piper()
        with mock.patch.dict(os.environ, {"RF_PIPER_ENABLED": "1"}), self.assertRaises(server.PreviewError) as ctx:
            server.tts_preview({"provider": "piper", "text": "hi"})
        self.assertEqual(ctx.exception.code, "piper_model_dir_missing")

    def test_piper_no_voices(self) -> None:
        install_fake_piper()
        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch.dict(os.environ, {"RF_PIPER_ENABLED": "1", "RF_PIPER_MODEL_DIR": tmp}),
            self.assertRaises(server.PreviewError) as ctx,
        ):
            server.tts_preview({"provider": "piper", "text": "hi"})
        self.assertEqual(ctx.exception.code, "piper_no_voices")


class LoudnessTargetTest(unittest.TestCase):
    def test_default_target(self) -> None:
        with mock.patch.dict(os.environ, {"RF_TTS_LOUDNESS_TARGET": ""}):
            self.assertEqual(server.loudness_target(), "-9")

    def test_env_target(self) -> None:
        with mock.patch.dict(os.environ, {"RF_TTS_LOUDNESS_TARGET": "-14"}):
            self.assertEqual(server.loudness_target(), "-14")

    def test_blank_env_target_falls_back(self) -> None:
        with mock.patch.dict(os.environ, {"RF_TTS_LOUDNESS_TARGET": "   "}):
            self.assertEqual(server.loudness_target(), "-9")

    def test_loudnorm_apply_filter_uses_measured_params(self) -> None:
        out = server.loudnorm_apply_filter(
            {"input_i": "-36.0", "input_tp": "-27.9", "input_lra": "1.2", "input_thresh": "-46.5"}
        )
        self.assertIn("loudnorm=I=-9:TP=-1.5:LRA=11", out)
        self.assertIn("measured_I=-36.0", out)
        self.assertIn("measured_TP=-27.9", out)
        self.assertIn("measured_LRA=1.2", out)
        self.assertIn("measured_thresh=-46.5", out)
        self.assertIn("linear=false", out)

    def test_loudnorm_apply_filter_falls_back_without_measurement(self) -> None:
        out = server.loudnorm_apply_filter({})
        self.assertEqual(out, "loudnorm=I=-9:TP=-1.5:LRA=11:linear=false")

    def test_loudnorm_apply_filter_honors_env_target(self) -> None:
        with mock.patch.dict(os.environ, {"RF_TTS_LOUDNESS_TARGET": "-14"}):
            out = server.loudnorm_apply_filter(
                {"input_i": "-30.0", "input_tp": "-22.0", "input_lra": "1.0", "input_thresh": "-40.0"}
            )
        self.assertIn("loudnorm=I=-14:TP=-1.5:LRA=11", out)


if __name__ == "__main__":
    unittest.main()
