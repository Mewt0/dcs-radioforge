"""Tests for POST /api/replace (voice-over replacement of an existing audio file)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import server
import tts


def _fake_run_ffmpeg(args: list[str]) -> None:
    """Stand-in for server.run_ffmpeg: copy first input file to the output path."""
    src = args[args.index("-i") + 1]
    dst = args[-1]
    Path(dst).write_bytes(Path(src).read_bytes())


class ReplaceApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self._orig_tmp = server.TMP
        self._orig_backup = server.BACKUP_DIR
        self._orig_ready = server.READY
        server.TMP = self.tmp / "build" / "_tmp_mp3"
        server.BACKUP_DIR = self.tmp / "build" / "rf_backup"
        server.READY = self.tmp / "build" / "dcs-ready"

    def tearDown(self) -> None:
        server.TMP = self._orig_tmp
        server.BACKUP_DIR = self._orig_backup
        server.READY = self._orig_ready
        self._tmp.cleanup()

    def _make_target(self, name: str = "voice_line.ogg", data: bytes = b"OLD-AUDIO") -> Path:
        target = self.tmp / name
        target.write_bytes(data)
        return target

    def _patch_synth(self, data: bytes = b"SYNTH-WAV") -> None:
        def fake_synth(item: dict, target: Path) -> tuple:
            Path(target).write_bytes(data)
            return None, "XTTS GPU"

        patcher = mock.patch.object(tts, "synthesize_item", side_effect=fake_synth)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _patch_convert(self) -> None:
        def fake_convert(
            src: Path,
            dst: Path,
            fmt: str,
            sample_rate: int,
            preset_id: str,
            signal_quality: int = 86,
            mic_clicks: bool = True,
        ) -> None:
            Path(dst).write_bytes(b"CONV-" + fmt.encode("ascii"))

        patcher = mock.patch.object(server, "convert_audio", side_effect=fake_convert)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_missing_fields_rejected(self) -> None:
        with self.assertRaises(server.ReplaceError) as ctx:
            server.replace_audio({"path": "", "text": ""})
        self.assertEqual(ctx.exception.code, "missing_fields")

    def test_path_not_found(self) -> None:
        with self.assertRaises(server.ReplaceError) as ctx:
            server.replace_audio({"path": str(self.tmp / "nope.ogg"), "text": "привет"})
        self.assertEqual(ctx.exception.code, "file_not_found")

    def test_bad_extension(self) -> None:
        target = self._make_target("voice.flac")
        with self.assertRaises(server.ReplaceError) as ctx:
            server.replace_audio({"path": str(target), "text": "привет"})
        self.assertEqual(ctx.exception.code, "bad_extension")

    def test_replace_ogg_ok(self) -> None:
        target = self._make_target("voice_line.ogg")
        self._patch_synth()
        self._patch_convert()
        with (
            mock.patch.object(server, "run_ffmpeg", side_effect=_fake_run_ffmpeg),
            mock.patch.object(
                server, "probe_audio", return_value={"codec": "vorbis", "sample_rate": 22050, "channels": 1}
            ),
        ):
            result = server.replace_audio({"path": str(target), "text": "привет", "provider": "external"})

        self.assertTrue(result["ok"])
        self.assertEqual(result["path"], str(target))
        self.assertEqual(result["format"], "ogg")
        self.assertEqual(result["sample_rate"], 22050)
        self.assertEqual(target.read_bytes(), b"CONV-ogg")
        backups = list(server.BACKUP_DIR.glob("*.bak"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), b"OLD-AUDIO")
        self.assertEqual(result["backup"], str(backups[0]))

    def test_replace_unicode_name_preserved(self) -> None:
        target = self._make_target("ывзщаоывщашыв.ogg")
        self._patch_synth()
        self._patch_convert()
        with (
            mock.patch.object(server, "run_ffmpeg", side_effect=_fake_run_ffmpeg),
            mock.patch.object(
                server, "probe_audio", return_value={"codec": "vorbis", "sample_rate": 22050, "channels": 1}
            ),
        ):
            result = server.replace_audio({"path": str(target), "text": "привет"})
        self.assertTrue(result["ok"])
        self.assertTrue(target.exists())
        self.assertEqual(target.name, "ывзщаоывщашыв.ogg")
        self.assertEqual(target.read_bytes(), b"CONV-ogg")

    def test_replace_wav_stereo(self) -> None:
        target = self._make_target("voice.wav")
        self._patch_synth()
        self._patch_convert()
        with (
            mock.patch.object(server, "run_ffmpeg", side_effect=_fake_run_ffmpeg),
            mock.patch.object(server, "wav_duration", return_value=3.5),
            mock.patch.object(
                server, "probe_audio", return_value={"codec": "pcm_s16le", "sample_rate": 44100, "channels": 2}
            ),
        ):
            result = server.replace_audio({"path": str(target), "text": "привет"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["format"], "wav")
        self.assertEqual(result["channels"], 2)
        self.assertEqual(result["duration"], 3.5)
        self.assertEqual(target.read_bytes(), b"CONV-wav")
        self.assertEqual(len(list(server.BACKUP_DIR.glob("*.bak"))), 1)

    def test_replace_mp3(self) -> None:
        target = self._make_target("voice.mp3")
        self._patch_synth()
        self._patch_convert()
        with (
            mock.patch.object(server, "run_ffmpeg", side_effect=_fake_run_ffmpeg),
            mock.patch.object(
                server, "probe_audio", return_value={"codec": "mp3", "sample_rate": 24000, "channels": 1}
            ),
        ):
            result = server.replace_audio({"path": str(target), "text": "привет"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["format"], "mp3")
        # fake run_ffmpeg copies the wav stage into the mp3 target (real code encodes)
        self.assertEqual(target.read_bytes(), b"CONV-wav")

    def test_external_error_propagates(self) -> None:
        target = self._make_target("voice.ogg")

        def boom(item: dict, target: Path) -> tuple:
            raise tts.ExternalTTSError("worker died", "command_failed")

        with (
            mock.patch.object(tts, "synthesize_item", side_effect=boom),
            self.assertRaises(server.ReplaceError) as ctx,
        ):
            server.replace_audio({"path": str(target), "text": "привет"})
        self.assertEqual(ctx.exception.code, "external_command_failed")
        # target untouched, backup still created
        self.assertEqual(target.read_bytes(), b"OLD-AUDIO")
        self.assertEqual(len(list(server.BACKUP_DIR.glob("*.bak"))), 1)

    def test_synthesize_ok(self) -> None:
        self._patch_synth()
        self._patch_convert()
        with (
            mock.patch.object(server, "run_ffmpeg", side_effect=_fake_run_ffmpeg),
            mock.patch.object(
                server, "probe_audio", return_value={"codec": "vorbis", "sample_rate": 22050, "channels": 1}
            ),
        ):
            result = server.synthesize_audio({"text": "привет", "fileName": "draft_test"})
        self.assertTrue(result["ok"])
        self.assertTrue(result["url"].startswith("/files/"))
        self.assertEqual(result["format"], "ogg")
        path = Path(result["path"])
        self.assertTrue(path.exists())
        self.assertEqual(path.read_bytes(), b"CONV-ogg")

    def test_synthesize_requires_text(self) -> None:
        with self.assertRaises(server.ReplaceError) as ctx:
            server.synthesize_audio({"text": "  "})
        self.assertEqual(ctx.exception.code, "missing_fields")

    def test_restore_ok(self) -> None:
        target = self._make_target("voice.ogg", data=b"NEW-AUDIO")
        backup = self.tmp / "voice_ogg_backup.bak"
        backup.write_bytes(b"OLD-AUDIO")
        result = server.restore_audio({"path": str(target), "backup": str(backup)})
        self.assertTrue(result["ok"])
        self.assertEqual(target.read_bytes(), b"OLD-AUDIO")

    def test_restore_missing_backup(self) -> None:
        target = self._make_target("voice.ogg")
        with self.assertRaises(server.ReplaceError) as ctx:
            server.restore_audio({"path": str(target), "backup": str(self.tmp / "nope.bak")})
        self.assertEqual(ctx.exception.code, "backup_not_found")

    def test_synthesize_matches_original_format(self) -> None:
        target = self._make_target("voice.ogg")
        self._patch_synth()
        self._patch_convert()
        with (
            mock.patch.object(server, "run_ffmpeg", side_effect=_fake_run_ffmpeg),
            mock.patch.object(
                server, "probe_audio", return_value={"codec": "vorbis", "sample_rate": 44100, "channels": 2}
            ),
        ):
            result = server.synthesize_audio({"text": "привет", "matchPath": str(target)})
        self.assertTrue(result["ok"])
        self.assertEqual(result["format"], "ogg")
        self.assertEqual(result["sample_rate"], 44100)
        self.assertTrue(result["matched"])

    def test_replace_with_source_skips_synthesis(self) -> None:
        target = self._make_target("voice.ogg")
        draft = self.tmp / "draft.ogg"
        draft.write_bytes(b"DRAFT-AUDIO")
        self._patch_convert()
        with (
            mock.patch.object(server, "run_ffmpeg", side_effect=_fake_run_ffmpeg),
            mock.patch.object(
                server, "probe_audio", return_value={"codec": "vorbis", "sample_rate": 22050, "channels": 1}
            ),
        ):
            result = server.replace_audio({"path": str(target), "text": "привет", "source": str(draft)})
        self.assertTrue(result["ok"])
        # fake convert writes CONV-ogg; source was not synthesized (no tts mock -> would fail if called)
        self.assertEqual(target.read_bytes(), b"CONV-ogg")
        self.assertEqual(len(list(server.BACKUP_DIR.glob("*.bak"))), 1)


if __name__ == "__main__":
    unittest.main()
