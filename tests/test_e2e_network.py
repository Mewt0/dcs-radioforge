"""Real end-to-end tests (edge-tts network + real ffmpeg).

Skipped unless the RF_NETWORK_TESTS=1 environment variable is set,
because they require internet access to the Edge TTS service.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import tempfile
import unittest
from pathlib import Path

import server
import voicekit

RUN_NETWORK = os.environ.get("RF_NETWORK_TESTS") == "1"


@unittest.skipUnless(RUN_NETWORK, "set RF_NETWORK_TESTS=1 to run real network E2E tests")
class NetworkE2ETest(unittest.TestCase):
    def test_server_edge_synthesis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            old = (server.BUILD, server.READY, server.TMP, server.PREVIEWS)
            server.BUILD = base / "build"
            server.READY = base / "build" / "dcs-ready"
            server.TMP = base / "build" / "_tmp_mp3"
            server.PREVIEWS = base / "build" / "previews"
            try:
                rows = server.generate_items(
                    [
                        {
                            "id": "e2e",
                            "text": "Проверка сети",
                            "voice": "ru-RU-DmitryNeural",
                            "preset": "srs_clean",
                            "formats": ["wav"],
                            "sampleRate": 22050,
                            "timestamp": False,
                        }
                    ]
                )
                row = rows[0]
                wav = server.READY / (row.get("wav") or "")
                self.assertTrue(wav.exists(), f"wav not created: {wav}")
                self.assertGreater(wav.stat().st_size, 0)
                self.assertGreater(float(row.get("duration_sec") or 0), 0)
            finally:
                server.BUILD, server.READY, server.TMP, server.PREVIEWS = old

    def test_voicekit_generate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            csv_path = tmp_path / "lines.csv"
            csv_path.write_text(
                "id,speaker,voice,rate,pitch,volume,radio,text\nvk_e2e,,,+0%,+0Hz,+0%,yes,Голос из voicekit\n",
                encoding="utf-8",
            )
            out_dir = tmp_path / "out"
            args = argparse.Namespace(
                input=str(csv_path),
                out=str(out_dir),
                voice="ru-RU-DmitryNeural",
                format="ogg",
                sample_rate=22050,
            )
            code = asyncio.run(voicekit.generate(args))
            self.assertEqual(code, 0)
            ready = out_dir / "dcs-ready"
            self.assertTrue((ready / "vk_e2e.ogg").exists())
            self.assertGreater((ready / "vk_e2e.ogg").stat().st_size, 0)
            self.assertTrue((out_dir / "manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
