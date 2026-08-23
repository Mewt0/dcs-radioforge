"""Unit tests for the shared TTS layer (tts.py)."""

from __future__ import annotations

import asyncio
import unittest
from pathlib import Path

import edge_tts

import server
import tts
from tests._helpers import FakeCommunicate


class RegistryTest(unittest.TestCase):
    def test_edge_registered_by_default(self) -> None:
        self.assertIn("edge", tts.TTS_PROVIDERS)

    def test_server_registers_elevenlabs(self) -> None:
        self.assertIn("elevenlabs", tts.TTS_PROVIDERS)
        self.assertTrue(callable(tts.TTS_PROVIDERS["elevenlabs"]))

    def test_unknown_provider_defaults_to_edge(self) -> None:
        fallback = tts.TTS_PROVIDERS.get("no-such-provider", tts.TTS_PROVIDERS["edge"])
        self.assertIs(fallback, tts.TTS_PROVIDERS["edge"])


class SynthesizeItemTest(unittest.TestCase):
    def setUp(self) -> None:
        self.edge_calls: list[tuple] = []
        self.el_calls: list[tuple] = []

        async def fake_edge(text: str, voice: str, rate: str, pitch: str, volume: str, target: Path) -> None:
            self.edge_calls.append((text, voice, rate, pitch, volume, str(target)))

        def fake_el(text: str, voice_id: str, model_id: str, language_code: str, target: Path) -> dict:
            self.el_calls.append((text, voice_id, model_id, language_code, str(target)))
            return {"character_count": 7, "request_id": "r1", "model_id": model_id, "text_characters": len(text)}

        self._orig_tts_edge = tts.synthesize_mp3
        self._orig_el = server.synthesize_elevenlabs_mp3
        tts.synthesize_mp3 = fake_edge
        server.synthesize_elevenlabs_mp3 = fake_el

    def tearDown(self) -> None:
        tts.synthesize_mp3 = self._orig_tts_edge
        server.synthesize_elevenlabs_mp3 = self._orig_el

    def test_edge_dispatch_defaults(self) -> None:
        usage, voice_label = tts.synthesize_item({"text": "hi"}, Path("a.mp3"))
        self.assertIsNone(usage)
        self.assertEqual(voice_label, "ru-RU-DmitryNeural")
        self.assertEqual(self.edge_calls, [("hi", "ru-RU-DmitryNeural", "+0%", "+0Hz", "+0%", str(Path("a.mp3")))])
        self.assertEqual(self.el_calls, [])

    def test_edge_dispatch_explicit_params(self) -> None:
        item = {"text": "hi", "voice": "ru-RU-SvetlanaNeural", "rate": "+1%", "pitch": "-2Hz", "volume": "-3%"}
        usage, voice_label = tts.synthesize_item(item, Path("a.mp3"))
        self.assertIsNone(usage)
        self.assertEqual(voice_label, "ru-RU-SvetlanaNeural")
        self.assertEqual(self.edge_calls[0][:5], ("hi", "ru-RU-SvetlanaNeural", "+1%", "-2Hz", "-3%"))

    def test_elevenlabs_dispatch(self) -> None:
        item = {
            "text": "hi",
            "provider": "elevenlabs",
            "elevenVoiceId": "vc-1",
            "elevenModel": "eleven_turbo_v2_5",
            "elevenLanguage": "en",
        }
        usage, voice_label = tts.synthesize_item(item, Path("a.mp3"))
        self.assertEqual(
            usage,
            {"character_count": 7, "request_id": "r1", "model_id": "eleven_turbo_v2_5", "text_characters": 2},
        )
        self.assertEqual(voice_label, "vc-1")
        self.assertEqual(self.el_calls, [("hi", "vc-1", "eleven_turbo_v2_5", "en", str(Path("a.mp3")))])
        self.assertEqual(self.edge_calls, [])

    def test_elevenlabs_lang_fallback(self) -> None:
        item = {"text": "hi", "provider": "elevenlabs", "elevenVoiceId": "vc-2", "lang": "ru"}
        tts.synthesize_item(item, Path("a.mp3"))
        self.assertEqual(self.el_calls[0][3], "ru")

    def test_unknown_provider_falls_back_to_edge(self) -> None:
        usage, voice_label = tts.synthesize_item({"text": "hi", "provider": "foobar"}, Path("a.mp3"))
        self.assertIsNone(usage)
        self.assertEqual(voice_label, "ru-RU-DmitryNeural")
        self.assertEqual(len(self.edge_calls), 1)
        self.assertEqual(self.el_calls, [])


class SynthesizeMp3Test(unittest.TestCase):
    def test_constructs_communicate_with_params(self) -> None:
        original = edge_tts.Communicate
        edge_tts.Communicate = FakeCommunicate
        FakeCommunicate.calls.clear()
        try:
            asyncio.run(tts.synthesize_mp3("hello", "ru-RU-DmitryNeural", "+0%", "+0Hz", "+0%", Path("x.mp3")))
            self.assertEqual(
                FakeCommunicate.calls,
                [{"text": "hello", "voice": "ru-RU-DmitryNeural", "rate": "+0%", "pitch": "+0Hz", "volume": "+0%"}],
            )
            self.assertTrue(Path("x.mp3").exists())
        finally:
            edge_tts.Communicate = original
            Path("x.mp3").unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
