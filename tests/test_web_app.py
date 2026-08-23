"""Web frontend regression tests (no ReferenceError at load)."""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_JS = REPO_ROOT / "web" / "app.js"


def _state_literal(text: str) -> str:
    marker = "const state = {"
    start = text.index(marker) + len(marker)
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return text[start - len(marker) : i]


class WebStateLiteralTest(unittest.TestCase):
    def test_state_literal_has_no_self_references(self) -> None:
        text = APP_JS.read_text(encoding="utf-8")
        literal = _state_literal(text)
        self.assertNotIn("state.", literal)
        self.assertNotIn("state[", literal)

    def test_default_line_provider_is_edge(self) -> None:
        text = APP_JS.read_text(encoding="utf-8")
        self.assertIn('provider: "edge",', _state_literal(text))


@unittest.skipIf(shutil.which("node") is None, "node not available")
class WebAppNodeSmokeTest(unittest.TestCase):
    def test_app_js_loads_without_reference_error(self) -> None:
        script = REPO_ROOT / "tests" / "web_app_smoke.js"
        proc = subprocess.run(["node", str(script)], capture_output=True, text=True, timeout=60, check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("STATE_OK", proc.stdout)


if __name__ == "__main__":
    unittest.main()
