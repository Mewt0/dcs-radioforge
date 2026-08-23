"""Regression tests for voicekit.generate (deterministic, no network)."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import edge_tts

import voicekit
from tests._helpers import FakeCommunicate

CSV_BODY = (
    "id,speaker,voice,rate,pitch,volume,radio,text\n"
    "test_001,Первый,,+0%,+0Hz,+0%,yes,Первая фраза для проверки\n"
    "test_002,Вторая,ru-RU-SvetlanaNeural,-5%,+2Hz,-10%,no,Вторая фраза\n"
    ",,,+1%,+0Hz,+0%,yes,Третья строка без id\n"
)


class VoicekitGenerateTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self.csv_path = tmp / "lines.csv"
        self.csv_path.write_text(CSV_BODY, encoding="utf-8")
        self.out_dir = tmp / "out"

        self._orig_comm = edge_tts.Communicate
        edge_tts.Communicate = FakeCommunicate
        FakeCommunicate.calls.clear()

        self._orig_conv = voicekit.convert_audio
        self._orig_wd = voicekit.wav_duration
        self._orig_wm = voicekit.write_manifests

        def fake_conv(src, dst, fmt, sample_rate, radio) -> None:
            dst.write_bytes(b"stub")

        voicekit.convert_audio = fake_conv
        voicekit.wav_duration = lambda p: 1.0
        self.manifest_rows: list[dict] = []
        voicekit.write_manifests = lambda rows, out_dir: self.manifest_rows.extend(rows)

        self.args = argparse.Namespace(
            input=str(self.csv_path),
            out=str(self.out_dir),
            voice="ru-RU-DmitryNeural",
            format="both",
            sample_rate=22050,
        )

    def tearDown(self) -> None:
        edge_tts.Communicate = self._orig_comm
        voicekit.convert_audio = self._orig_conv
        voicekit.wav_duration = self._orig_wd
        voicekit.write_manifests = self._orig_wm
        self._tmp.cleanup()

    def _run_generate(self) -> int:
        with contextlib.redirect_stdout(io.StringIO()):
            return asyncio.run(voicekit.generate(self.args))

    def test_exit_code_and_communicate_calls(self) -> None:
        code = self._run_generate()
        self.assertEqual(code, 0)
        self.assertEqual(
            FakeCommunicate.calls,
            [
                {
                    "text": "Первая фраза для проверки",
                    "voice": "ru-RU-DmitryNeural",
                    "rate": "+0%",
                    "pitch": "+0Hz",
                    "volume": "+0%",
                },
                {
                    "text": "Вторая фраза",
                    "voice": "ru-RU-SvetlanaNeural",
                    "rate": "-5%",
                    "pitch": "+2Hz",
                    "volume": "-10%",
                },
                {
                    "text": "Третья строка без id",
                    "voice": "ru-RU-DmitryNeural",
                    "rate": "+1%",
                    "pitch": "+0Hz",
                    "volume": "+0%",
                },
            ],
        )

    def test_manifest_rows(self) -> None:
        self._run_generate()
        self.assertEqual(len(self.manifest_rows), 3)
        first = self.manifest_rows[0]
        self.assertEqual(first["id"], "test_001")
        self.assertEqual(first["speaker"], "Первый")
        self.assertEqual(first["voice"], "ru-RU-DmitryNeural")
        self.assertEqual(first["wav"], "test_001.wav")
        self.assertEqual(first["ogg"], "test_001.ogg")
        self.assertEqual(first["duration_sec"], 1.0)
        self.assertEqual(first["text"], "Первая фраза для проверки")
        self.assertEqual(self.manifest_rows[2]["id"], "line_004")


if __name__ == "__main__":
    unittest.main()
