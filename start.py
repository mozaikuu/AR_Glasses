from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from collections.abc import Iterable
from dataclasses import dataclass

from app.config.settings import settings


@dataclass
class ManagedService:
    name: str
    command: list[str]
    process: subprocess.Popen[str] | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smart Glasses Distilled launcher")
    parser.add_argument("--host", default=settings.api_host)
    parser.add_argument("--port", type=int, default=settings.api_port)
    parser.add_argument("--profile", default=settings.launcher_profile)
    parser.add_argument("--reload", action="store_true", default=settings.auto_reload)
    parser.add_argument("--with-audio", action="store_true")
    parser.add_argument("--with-flask", action="store_true")
    parser.add_argument("--with-streamlit", action="store_true")
    parser.add_argument("--with-mcp", action="store_true")
    return parser.parse_args()


def _spawn(command: list[str]) -> subprocess.Popen[str]:
    # Spawn every component in its own process so one command can run all services.
    return subprocess.Popen(command, env=os.environ.copy())


def _terminate_all(services: Iterable[ManagedService]) -> None:
    for service in services:
        if service.process is not None and service.process.poll() is None:
            service.process.send_signal(signal.SIGTERM)
    for service in services:
        if service.process is not None and service.process.poll() is None:
            service.process.wait(timeout=5)


def main() -> None:
    args = parse_args()

    if args.profile == "production-local":
        enable_audio = True
        enable_flask = False
        enable_streamlit = True
        enable_mcp = True
    elif args.profile == "gateway-only":
        enable_audio = False
        enable_flask = False
        enable_streamlit = False
        enable_mcp = False
    else:
        enable_audio = args.with_audio or settings.enable_audio_sidecar
        enable_flask = args.with_flask or settings.enable_flask
        enable_streamlit = args.with_streamlit or settings.enable_streamlit
        enable_mcp = args.with_mcp or settings.enable_mcp_server

    services: list[ManagedService] = []

    gateway_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.api.gateway:app",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    if args.reload:
        gateway_cmd.append("--reload")
    services.append(ManagedService(name="gateway", command=gateway_cmd, process=_spawn(gateway_cmd)))
    print(f"[start.py] Gateway running at http://{args.host}:{args.port}")

    if enable_flask:
        flask_cmd = [sys.executable, "run_flask.py"]
        if args.reload:
            flask_cmd.append("--reload")
        services.append(ManagedService(name="flask", command=flask_cmd, process=_spawn(flask_cmd)))
        print(f"[start.py] Flask running at http://{settings.flask_host}:{settings.flask_port}")

    if enable_streamlit:
        streamlit_cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            settings.streamlit_app_path,
            "--server.address",
            settings.streamlit_host,
            "--server.port",
            str(settings.streamlit_port),
            "--browser.gatherUsageStats",
            "false",
        ]
        services.append(ManagedService(name="streamlit", command=streamlit_cmd, process=_spawn(streamlit_cmd)))
        print(f"[start.py] Streamlit running at http://{settings.streamlit_host}:{settings.streamlit_port}")

    if enable_audio:
        audio_cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "app.api.audio_sidecar:app",
            "--host",
            settings.audio_sidecar_host,
            "--port",
            str(settings.audio_sidecar_port),
        ]
        if args.reload:
            audio_cmd.append("--reload")
        services.append(ManagedService(name="audio_sidecar", command=audio_cmd, process=_spawn(audio_cmd)))
        print(
            f"[start.py] Audio sidecar running at http://{settings.audio_sidecar_host}:{settings.audio_sidecar_port}"
        )

    if enable_mcp:
        mcp_cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "server.server:app",
            "--host",
            settings.mcp_host,
            "--port",
            str(settings.mcp_port),
        ]
        if args.reload:
            mcp_cmd.append("--reload")
        services.append(ManagedService(name="mcp", command=mcp_cmd, process=_spawn(mcp_cmd)))
        print(f"[start.py] MCP server running at http://{settings.mcp_host}:{settings.mcp_port}")

    try:
        # Keep launcher alive and optionally restart crashed subprocesses.
        while any(service.process is not None and service.process.poll() is None for service in services):
            if settings.restart_crashed_services:
                for service in services:
                    if service.process is not None and service.process.poll() is not None:
                        print(f"[start.py] Restarting crashed service: {service.name}")
                        service.process = _spawn(service.command)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("[start.py] Shutdown requested")
    finally:
        _terminate_all(services)


if __name__ == "__main__":
    main()
