"""Regression tests for server.generate_items TTS dispatch (deterministic, no network)."""

from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

import server
import tts


class GenerateItemsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self._orig_dirs = (server.BUILD, server.READY, server.TMP, server.PREVIEWS)
        server.BUILD = base / "build"
        server.READY = base / "build" / "dcs-ready"
        server.TMP = base / "build" / "_tmp_mp3"
        server.PREVIEWS = base / "build" / "previews"

        self.edge_calls: list[tuple] = []
        self.el_calls: list[tuple] = []

        async def fake_edge(text: str, voice: str, rate: str, pitch: str, volume: str, target: Path) -> None:
            self.edge_calls.append((text, voice, rate, pitch, volume, str(target)))
            Path(target).write_bytes(b"mp3")

        def fake_el(text: str, voice_id: str, model_id: str, language_code: str, target: Path) -> dict:
            self.el_calls.append((text, voice_id, model_id, language_code, str(target)))
            return {"character_count": 123, "request_id": "req-1", "model_id": model_id, "text_characters": len(text)}

        def fake_conv(src, dst, fmt, sample_rate, preset_id, signal_quality=86, mic_clicks=True) -> None:
            dst.write_bytes(b"stub")

        self._orig_tts_edge = tts.synthesize_mp3
        self._orig_el = server.synthesize_elevenlabs_mp3
        self._orig_conv = server.convert_audio
        self._orig_wd = server.wav_duration
        self._orig_app = server.append_manifest
        tts.synthesize_mp3 = fake_edge
        server.synthesize_elevenlabs_mp3 = fake_el
        server.convert_audio = fake_conv
        server.wav_duration = lambda p: 1.0
        self.manifest_rows: list[dict] = []
        server.append_manifest = lambda rows: self.manifest_rows.extend(rows)

    def tearDown(self) -> None:
        tts.synthesize_mp3 = self._orig_tts_edge
        server.synthesize_elevenlabs_mp3 = self._orig_el
        server.convert_audio = self._orig_conv
        server.wav_duration = self._orig_wd
        server.append_manifest = self._orig_app
        server.BUILD, server.READY, server.TMP, server.PREVIEWS = self._orig_dirs
        self._tmp.cleanup()

    def test_edge_default_params(self) -> None:
        rows = server.generate_items([{"id": "a1", "text": "hi", "timestamp": False}])
        self.assertEqual(rows[0]["voice"], "ru-RU-DmitryNeural")
        self.assertEqual(self.edge_calls[0][:5], ("hi", "ru-RU-DmitryNeural", "+0%", "+0Hz", "+0%"))
        self.assertEqual(self.el_calls, [])

    def test_edge_explicit_params(self) -> None:
        item = {
            "id": "a2",
            "text": "hi",
            "voice": "ru-RU-SvetlanaNeural",
            "rate": "+1%",
            "pitch": "-2Hz",
            "volume": "-3%",
            "timestamp": False,
        }
        rows = server.generate_items([item])
        self.assertEqual(rows[0]["voice"], "ru-RU-SvetlanaNeural")
        self.assertEqual(self.edge_calls[0][:5], ("hi", "ru-RU-SvetlanaNeural", "+1%", "-2Hz", "-3%"))

    def test_elevenlabs_usage_and_row(self) -> None:
        item = {
            "id": "a3",
            "text": "hi",
            "provider": "elevenlabs",
            "elevenVoiceId": "vc-42",
            "elevenModel": "eleven_turbo_v2_5",
            "elevenLanguage": "en",
            "timestamp": False,
        }
        rows = server.generate_items([item])
        row = rows[0]
        self.assertEqual(row["voice"], "vc-42")
        self.assertEqual(
            row["elevenlabs"],
            {"character_count": 123, "request_id": "req-1", "model_id": "eleven_turbo_v2_5", "text_characters": 2},
        )
        self.assertEqual(row["elevenlabs_character_cost"], 123)
        self.assertEqual(self.el_calls[0][:4], ("hi", "vc-42", "eleven_turbo_v2_5", "en"))
        mp3_path = Path(self.el_calls[0][4])
        self.assertEqual(mp3_path.parent, server.TMP)
        self.assertEqual(mp3_path.suffix, ".mp3")
        self.assertEqual(mp3_path.stem, Path(row["wav"]).stem)
        self.assertEqual(self.edge_calls, [])

    def test_unknown_provider_falls_back_to_edge(self) -> None:
        rows = server.generate_items([{"id": "a4", "text": "hi", "provider": "foobar", "timestamp": False}])
        self.assertEqual(rows[0]["voice"], "ru-RU-DmitryNeural")
        self.assertEqual(len(self.edge_calls), 1)
        self.assertEqual(self.el_calls, [])

    def test_elevenlabs_lang_fallback(self) -> None:
        server.generate_items(
            [
                {
                    "id": "a5",
                    "text": "hi",
                    "provider": "elevenlabs",
                    "elevenVoiceId": "vc-7",
                    "lang": "ru",
                    "timestamp": False,
                }
            ]
        )
        self.assertEqual(self.el_calls[0][3], "ru")

    def test_empty_text_skipped(self) -> None:
        rows = server.generate_items(
            [{"id": "a6", "text": "   ", "timestamp": False}, {"id": "a7", "text": "ok", "timestamp": False}]
        )
        self.assertEqual([r["id"] for r in rows], ["a7"])
        self.assertEqual(len(self.edge_calls), 1)

    def test_output_files_and_manifest_row(self) -> None:
        rows = server.generate_items([{"id": "a8", "text": "hi", "preset": "srs_clean", "timestamp": False}])
        row = rows[0]
        self.assertTrue(row["wav"].startswith("a8_"))
        self.assertTrue(row["wav"].endswith(".wav"))
        self.assertTrue(row["ogg"].startswith("a8_"))
        self.assertTrue(row["ogg"].endswith(".ogg"))
        self.assertEqual(Path(row["wav"]).stem, Path(row["ogg"]).stem)
        self.assertEqual(row["duration_sec"], 1.0)
        self.assertTrue((server.READY / row["wav"]).exists())
        self.assertTrue((server.READY / row["ogg"]).exists())
        self.assertEqual(len(self.manifest_rows), 1)
        self.assertEqual(self.manifest_rows[0]["id"], "a8")

    def test_duplicate_ids_get_unique_names(self) -> None:
        rows = server.generate_items(
            [
                {"id": "dup", "text": "one", "timestamp": False},
                {"id": "dup", "text": "two", "timestamp": False},
            ]
        )
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["id"], rows[1]["id"])
        self.assertNotEqual(rows[0]["wav"], rows[1]["wav"])
        self.assertNotEqual(rows[0]["ogg"], rows[1]["ogg"])
        for row in rows:
            self.assertTrue(row["wav"].startswith("dup_"))
            self.assertTrue(row["ogg"].startswith("dup_"))
        mp3_stems = {Path(call[5]).stem for call in self.edge_calls}
        wav_stems = {Path(row["wav"]).stem for row in rows}
        self.assertEqual(mp3_stems, wav_stems)
        self.assertEqual(len(mp3_stems), 2)

    def test_temp_mp3_removed_after_success(self) -> None:
        rows = server.generate_items([{"id": "a10", "text": "hi", "timestamp": False}])
        self.assertTrue(rows[0]["wav"])
        self.assertEqual(list(server.TMP.glob("*.mp3")), [])

    def test_temp_mp3_kept_when_conversion_fails(self) -> None:
        def boom(src, dst, fmt, sample_rate, preset_id, signal_quality=86, mic_clicks=True) -> None:
            raise RuntimeError("convert failed")

        original_conv = server.convert_audio
        server.convert_audio = boom
        try:
            with self.assertRaisesRegex(RuntimeError, "convert failed"):
                server.generate_items([{"id": "a11", "text": "hi", "timestamp": False}])
        finally:
            server.convert_audio = original_conv
        mp3_files = list(server.TMP.glob("a11_*.mp3"))
        self.assertEqual(len(mp3_files), 1)

    def test_empty_voice_id_raises(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "ElevenLabs voice id is empty"):
            self._orig_el("x", "", "m", "ru", Path("x.mp3"))


class ManifestLockTest(unittest.TestCase):
    """Exercises the real append_manifest with its threading.Lock."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_build = server.BUILD
        server.BUILD = Path(self._tmp.name)

    def tearDown(self) -> None:
        server.BUILD = self._orig_build
        self._tmp.cleanup()

    def _read_lines(self) -> list[str]:
        manifest = server.BUILD / "gui_manifest.csv"
        return manifest.read_text(encoding="utf-8-sig").splitlines()

    def test_header_written_once_across_appends(self) -> None:
        server.append_manifest([{"id": "r1", "text": "one"}])
        server.append_manifest([{"id": "r2", "text": "two"}])
        server.append_manifest([])
        lines = self._read_lines()
        self.assertEqual([line for line in lines if line.startswith("time")], [lines[0]])
        self.assertEqual(len(lines), 3)

    def test_concurrent_appends_single_header(self) -> None:
        errors: list[Exception] = []

        def worker(i: int) -> None:
            try:
                server.append_manifest([{"id": f"t{i}", "text": "x"}])
            except Exception as exc:  # noqa: BLE001 - test harness collects failures
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(errors, [])
        lines = self._read_lines()
        self.assertEqual([line for line in lines if line.startswith("time")], [lines[0]])
        self.assertEqual(len(lines), 9)


if __name__ == "__main__":
    unittest.main()
