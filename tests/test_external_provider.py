"""Tests for the external local TTS provider (subprocess bridge, no real GPU engine)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import server
import tts

WORKER_OK = "import json, sys\npayload = json.load(sys.stdin)\nopen(payload['output'], 'wb').write(b'EXT-WAV')\n"
WORKER_FAIL = "import sys\nprint('boom', file=sys.stderr)\nsys.exit(1)\n"
WORKER_SLOW = (
    "import json, sys, time\n"
    "payload = json.load(sys.stdin)\n"
    "time.sleep(10)\n"
    "open(payload['output'], 'wb').write(b'EXT-WAV')\n"
)


def _env(command: str, **extra: str) -> dict:
    values = {"RF_EXTERNAL_TTS_ENABLED": "1", "RF_EXTERNAL_TTS_COMMAND": command}
    values.update(extra)
    return values


class ExternalUnavailableTest(unittest.TestCase):
    def tearDown(self) -> None:
        tts.TTS_PROVIDERS.pop("external", None)

    def test_import_tts_without_external_config(self) -> None:
        tts.sync_external_registration()  # must not crash
        self.assertNotIn("external", tts.TTS_PROVIDERS)
        status = tts.external_status()
        self.assertFalse(status["available"])
        self.assertEqual(status["reason"], "disabled")

    def test_command_missing(self) -> None:
        with mock.patch.dict(os.environ, {"RF_EXTERNAL_TTS_ENABLED": "1"}):
            status = tts.external_status()
        self.assertFalse(status["available"])
        self.assertEqual(status["reason"], "command_missing")

    def test_external_unavailable_does_not_break_others(self) -> None:
        with mock.patch.dict(os.environ, _env("")):
            tts.sync_external_registration()
            self.assertNotIn("external", tts.TTS_PROVIDERS)
            with self.assertRaisesRegex(RuntimeError, "External TTS provider is unavailable"):
                tts.synthesize_item({"text": "hi", "provider": "external"}, Path("x.wav"))

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

    def test_preview_external_structured_errors(self) -> None:
        with (
            mock.patch.dict(os.environ, {"RF_EXTERNAL_TTS_ENABLED": "0"}),
            self.assertRaises(server.PreviewError) as ctx,
        ):
            server.tts_preview({"provider": "external", "text": "hi"})
        self.assertEqual(ctx.exception.code, "external_disabled")
        with (
            mock.patch.dict(os.environ, {"RF_EXTERNAL_TTS_ENABLED": "1"}),
            self.assertRaises(server.PreviewError) as ctx,
        ):
            server.tts_preview({"provider": "external", "text": "hi"})
        self.assertEqual(ctx.exception.code, "external_command_missing")


class ExternalAvailableTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()
        tts.TTS_PROVIDERS.pop("external", None)

    def _command(self, worker_name: str) -> str:
        script = self.tmp / worker_name
        script.write_text(
            {
                "ok.py": WORKER_OK,
                "fail.py": WORKER_FAIL,
                "slow.py": WORKER_SLOW,
            }[worker_name],
            encoding="utf-8",
        )
        return f'"{sys.executable}" "{script}"'

    def test_registry_contains_external_only_when_available(self) -> None:
        command = self._command("ok.py")
        with mock.patch.dict(os.environ, _env(command)):
            tts.sync_external_registration()
            self.assertIn("external", tts.TTS_PROVIDERS)
            status = tts.external_status()
            self.assertTrue(status["available"])
            self.assertIn("timeout", status)
            self.assertIn("voice_label", status)
        with mock.patch.dict(os.environ, {"RF_EXTERNAL_TTS_ENABLED": "0", "RF_EXTERNAL_TTS_COMMAND": command}):
            tts.sync_external_registration()
            self.assertNotIn("external", tts.TTS_PROVIDERS)

    def test_external_provider_writes_wav(self) -> None:
        command = self._command("ok.py")
        with mock.patch.dict(os.environ, _env(command)):
            target = self.tmp / "out.wav"
            usage = tts.external_provider({"text": "привет", "lang": "ru"}, target)
            self.assertIsNone(usage)
            self.assertTrue(target.exists())
            self.assertEqual(target.read_bytes(), b"EXT-WAV")

    def test_external_provider_timeout(self) -> None:
        command = self._command("slow.py")
        with mock.patch.dict(os.environ, _env(command, RF_EXTERNAL_TTS_TIMEOUT="1")):
            with self.assertRaises(tts.ExternalTTSError) as ctx:
                tts.external_provider({"text": "hi"}, self.tmp / "out.wav")
            self.assertEqual(ctx.exception.code, "timeout")

    def test_external_provider_command_failed(self) -> None:
        command = self._command("fail.py")
        with mock.patch.dict(os.environ, _env(command)):
            with self.assertRaises(tts.ExternalTTSError) as ctx:
                tts.external_provider({"text": "hi"}, self.tmp / "out.wav")
            self.assertEqual(ctx.exception.code, "command_failed")
            self.assertIn("boom", str(ctx.exception))

    def test_preview_external_works_with_fake_worker(self) -> None:
        command = self._command("ok.py")
        original_tmp = server.TMP
        server.TMP = self.tmp / "build" / "_tmp_mp3"
        try:
            with mock.patch.dict(os.environ, _env(command)):
                result = server.tts_preview({"provider": "external", "text": "привет"})
        finally:
            server.TMP = original_tmp
        self.assertEqual(result["mime"], "audio/wav")
        self.assertEqual(result["format"], "wav")
        self.assertGreater(len(result["audio_base64"]), 0)

    def test_status_endpoint_includes_external(self) -> None:
        payload = server.tts_providers_status()
        self.assertIn("external", payload["providers"])
        self.assertIn("available", payload["providers"]["external"])


if __name__ == "__main__":
    unittest.main()
