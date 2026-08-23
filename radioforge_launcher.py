from __future__ import annotations

import sys

import server

if __name__ == "__main__":
    args = sys.argv[1:] or ["--host", "127.0.0.1", "--port", "8765", "--open"]
    raise SystemExit(server.main(args))
