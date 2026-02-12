#!/usr/bin/env python3
"""
Single entry point for the Smart Glasses stack.

Default mode:
- Starts unified gateway server on port 8000.
- This server provides API + web dashboard endpoints.

Optional mode:
- --with-audio starts websocket audio server as a sidecar process.
"""
import argparse
import subprocess
import sys
import signal
from pathlib import Path

import uvicorn

from config.settings import API_HOST, API_PORT


PROJECT_ROOT = Path(__file__).parent
_child_processes = []


def _shutdown(*_args):
    for proc in _child_processes:
        try:
            proc.terminate()
        except Exception:
            pass

    for proc in _child_processes:
        try:
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    sys.exit(0)


def _start_audio_sidecar() -> None:
    proc = subprocess.Popen(
        [sys.executable, "-m", "server_audio.audio_stream_server"],
        cwd=str(PROJECT_ROOT),
    )
    _child_processes.append(proc)
    print("Started audio sidecar: ws://0.0.0.0:8765")


def main() -> None:
    parser = argparse.ArgumentParser(description="Smart Glasses unified launcher")
    parser.add_argument("--with-audio", action="store_true", help="Run websocket audio server sidecar")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    if args.with_audio:
        _start_audio_sidecar()

    print("=" * 60)
    print("Smart Glasses Unified Startup")
    print(f"Gateway/API: http://127.0.0.1:{API_PORT}")
    print(f"Dashboard:   http://127.0.0.1:{API_PORT}/dashboard")
    if args.with_audio:
        print("Audio WS:    ws://127.0.0.1:8765")
    print("=" * 60)

    uvicorn.run(
        "server.gateway:app",
        host=API_HOST,
        port=API_PORT,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
