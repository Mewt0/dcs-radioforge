"""Contract/syntax tests for the XTTS external worker template (no coqui/TTS installed)."""

from __future__ import annotations

import importlib
import io
import json
import os
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from typing import ClassVar
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKER = "examples.external_tts.xtts_worker"


def load_worker():
    return importlib.import_module(WORKER)


def stdin_from(text: str) -> mock._patch:
    """Patch sys.stdin with a StringIO (contextlib.redirect_stdin was removed in 3.14)."""
    return mock.patch("sys.stdin", io.StringIO(text))


class FakeTTS:
    tts_to_file_calls: ClassVar[list[dict]] = []

    def __init__(self, model_name=None, device=None) -> None:
        self.model_name = model_name
        self.device = device

    def tts_to_file(self, **kwargs) -> None:
        FakeTTS.tts_to_file_calls.append(kwargs)
        Path(kwargs["file_path"]).write_bytes(b"XTTS-WAV")


def install_fake_tts() -> None:
    api = types.ModuleType("TTS.api")
    api.TTS = FakeTTS
    pkg = types.ModuleType("TTS")
    pkg.api = api
    sys.modules["TTS"] = pkg
    sys.modules["TTS.api"] = api
    FakeTTS.tts_to_file_calls.clear()


def remove_fake_tts() -> None:
    sys.modules.pop("TTS", None)
    sys.modules.pop("TTS.api", None)


def run_main(job_str: str) -> tuple[int, str]:
    err = io.StringIO()
    with stdin_from(job_str), redirect_stderr(err):
        code = load_worker().main()
    return code, err.getvalue()


class WorkerImportTest(unittest.TestCase):
    def tearDown(self) -> None:
        remove_fake_tts()
        sys.modules.pop("torch", None)

    def test_worker_imports_without_tts(self) -> None:
        self.assertNotIn("TTS", sys.modules)
        self.assertNotIn("torch", sys.modules)
        importlib.import_module(WORKER)
        self.assertNotIn("TTS", sys.modules)
        self.assertNotIn("torch", sys.modules)

    def test_read_job_validation(self) -> None:
        mod = load_worker()
        with stdin_from("{}"), self.assertRaisesRegex(ValueError, "missing required field: text"):
            mod.read_job()
        with stdin_from('{"text": "hi"}'), self.assertRaisesRegex(ValueError, "missing required field: output"):
            mod.read_job()
        with stdin_from("not json"), self.assertRaisesRegex(ValueError, "invalid JSON"):
            mod.read_job()
        with stdin_from('{"text": "hi", "output": "C:/tmp/o.wav"}'):
            job = mod.read_job()
        self.assertEqual(job["text"], "hi")

    def test_resolve_speaker_wav_env_and_voice(self) -> None:
        mod = load_worker()
        with tempfile.TemporaryDirectory() as tmp:
            ref = Path(tmp) / "ref.wav"
            ref.write_bytes(b"wav")
            other = Path(tmp) / "other.wav"
            other.write_bytes(b"wav")
            with mock.patch.dict(os.environ, {"RF_XTTS_SPEAKER_WAV": str(ref)}):
                self.assertEqual(mod.resolve_speaker_wav({}), str(ref))
            with mock.patch.dict(os.environ, {"RF_XTTS_SPEAKER_WAV": str(ref)}):
                self.assertEqual(mod.resolve_speaker_wav({"voice": str(other)}), str(other))
            with mock.patch.dict(os.environ, {"RF_XTTS_SPEAKER_WAV": ""}):
                self.assertEqual(mod.resolve_speaker_wav({"voice": str(other)}), str(other))
                with self.assertRaisesRegex(ValueError, "no speaker reference"):
                    mod.resolve_speaker_wav({"voice": "some-voice-name"})

    def test_resolve_model_and_device(self) -> None:
        mod = load_worker()
        with mock.patch.dict(os.environ, {"RF_XTTS_MODEL": ""}):
            self.assertEqual(mod.resolve_model(), "tts_models/multilingual/multi-dataset/xtts_v2")
        with mock.patch.dict(os.environ, {"RF_XTTS_MODEL": "custom/model"}):
            self.assertEqual(mod.resolve_model(), "custom/model")
        with mock.patch.dict(os.environ, {"RF_XTTS_DEVICE": "cpu"}):
            self.assertEqual(mod.resolve_device(), "cpu")
        with mock.patch.dict(os.environ, {"RF_XTTS_DEVICE": "cuda"}):
            self.assertEqual(mod.resolve_device(), "cuda")
        torch_fake = types.ModuleType("torch")
        torch_fake.cuda = types.SimpleNamespace(is_available=lambda: True)
        sys.modules["torch"] = torch_fake
        try:
            with mock.patch.dict(os.environ, {"RF_XTTS_DEVICE": "auto"}):
                self.assertEqual(mod.resolve_device(), "cuda")
        finally:
            sys.modules.pop("torch", None)

    def test_synthesize_calls_tts_with_payload(self) -> None:
        mod = load_worker()
        install_fake_tts()
        with tempfile.TemporaryDirectory() as tmp:
            ref = Path(tmp) / "ref.wav"
            ref.write_bytes(b"wav")
            out = Path(tmp) / "out.wav"
            try:
                mod.synthesize({"text": "привет", "output": str(out)}, str(ref), "the-model", "cpu")
            finally:
                remove_fake_tts()
            self.assertTrue(out.exists())
            self.assertEqual(out.read_bytes(), b"XTTS-WAV")
            call = FakeTTS.tts_to_file_calls[-1]
            self.assertEqual(call["language"], "ru")
            self.assertEqual(call["speaker_wav"], str(ref))
            self.assertEqual(call["file_path"], str(out))

    def test_main_ok_and_error(self) -> None:
        install_fake_tts()
        with tempfile.TemporaryDirectory() as tmp:
            ref = Path(tmp) / "ref.wav"
            ref.write_bytes(b"wav")
            out = Path(tmp) / "out.wav"
            job = json.dumps({"text": "привет", "language": "ru", "output": str(out)})
            try:
                with mock.patch.dict(os.environ, {"RF_XTTS_DEVICE": "cpu", "RF_XTTS_SPEAKER_WAV": str(ref)}):
                    code, err = run_main(job)
            finally:
                remove_fake_tts()
            self.assertEqual(code, 0, err)
            self.assertTrue(out.exists())
            code, err = run_main("not json")
            self.assertEqual(code, 1)
            self.assertIn("xtts_worker error", err)

    def test_readme_documents_command_example(self) -> None:
        readme = (REPO_ROOT / "examples" / "external_tts" / "README_RU.md").read_text(encoding="utf-8")
        self.assertIn("RF_EXTERNAL_TTS_COMMAND", readme)
        self.assertIn("voice_ref_full_24k_mono.wav", readme)


if __name__ == "__main__":
    unittest.main()
