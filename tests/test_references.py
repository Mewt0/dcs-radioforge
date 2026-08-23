"""Tests for the reference voice manager (server.list_reference_voices)."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import server


class ReferenceVoicesTest(unittest.TestCase):
    def test_lists_project_references_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            refs = base / "references"
            refs.mkdir()
            (refs / "voice_a.wav").write_bytes(b"wav")
            (refs / "voice_b.wav").write_bytes(b"wav")
            (refs / "notes.txt").write_text("x", encoding="utf-8")
            old_root = server.APP_ROOT
            server.APP_ROOT = base
            try:
                with mock.patch.dict(os.environ, {"RF_XTTS_SPEAKER_WAV": "", "RF_XTTS_VOICES_DIR": ""}):
                    voices = server.list_reference_voices()
            finally:
                server.APP_ROOT = old_root
            self.assertEqual([v["name"] for v in voices], ["voice_a", "voice_b"])
            self.assertTrue(all(v["path"].endswith(".wav") for v in voices))

    def test_includes_speaker_wav_and_extra_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            refs = base / "references"
            refs.mkdir()
            extra = base / "extra"
            extra.mkdir()
            (refs / "project.wav").write_bytes(b"wav")
            (extra / "custom.wav").write_bytes(b"wav")
            speaker = base / "current.wav"
            speaker.write_bytes(b"wav")
            old_root = server.APP_ROOT
            server.APP_ROOT = base
            try:
                with mock.patch.dict(
                    os.environ, {"RF_XTTS_SPEAKER_WAV": str(speaker), "RF_XTTS_VOICES_DIR": str(extra)}
                ):
                    voices = server.list_reference_voices()
            finally:
                server.APP_ROOT = old_root
            self.assertEqual([v["name"] for v in voices], ["current", "project", "custom"])

    def test_no_duplicates_across_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            refs = base / "references"
            refs.mkdir()
            (refs / "dup.wav").write_bytes(b"wav")
            old_root = server.APP_ROOT
            server.APP_ROOT = base
            try:
                with mock.patch.dict(
                    os.environ, {"RF_XTTS_SPEAKER_WAV": str(refs / "dup.wav"), "RF_XTTS_VOICES_DIR": ""}
                ):
                    voices = server.list_reference_voices()
            finally:
                server.APP_ROOT = old_root
            self.assertEqual([v["name"] for v in voices], ["dup"])


if __name__ == "__main__":
    unittest.main()
