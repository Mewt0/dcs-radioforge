# Tests

Regression suite for the shared TTS layer (tts.py), the HTTP studio (server.py)
and the batch CLI (voicekit.py). All tests are deterministic and need no network,
except `test_e2e_network.py` which is skipped by default.

## Run

From the repository root, using the project venv:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

## Network E2E (optional)

```powershell
$env:RF_NETWORK_TESTS = "1"
.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

This requires internet access to the Microsoft Edge TTS service and runs the real
edge-tts + ffmpeg pipeline for both server.py and voicekit.py.
