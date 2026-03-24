#!/usr/bin/env python3
"""
Install/check runtime dependencies for Smart Glasses.

Targets:
- speechrecognition (module: speech_recognition)
- pyaudio (module: pyaudio)
- libvips runtime + pyvips (for moondream dependencies)
- piper-tts (binary: piper)
- pygame (module: pygame)
- optional beautifulsoup4 (module: bs4)

Usage:
    python scripts/install_runtime_deps.py
    python scripts/install_runtime_deps.py --with-bs4
    python scripts/install_runtime_deps.py --manager uv
"""
from __future__ import annotations

import argparse
import ctypes
import importlib.util
import shutil
import subprocess
import sys
from ctypes.util import find_library
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PIPER_MODEL = PROJECT_ROOT / "models" / "piper" / "en_US-lessac-medium.onnx"


def _has_module(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _run(cmd: list[str]) -> bool:
    print(f"> {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), check=False)
    return result.returncode == 0


def _select_manager(manager: str) -> str:
    if manager in ("pip", "uv"):
        return manager
    return "uv" if shutil.which("uv") else "pip"


def _install_pkg(manager: str, package: str) -> bool:
    if manager == "uv":
        return _run(["uv", "add", package])
    return _run([sys.executable, "-m", "pip", "install", package])


def _has_libvips_runtime() -> bool:
    if sys.platform.startswith("win"):
        try:
            ctypes.WinDLL("libvips-42.dll")
            return True
        except Exception:
            return False
    lib = find_library("vips")
    if not lib:
        return False
    try:
        ctypes.CDLL(lib)
        return True
    except Exception:
        return False


def _install_libvips_windows() -> bool:
    if _has_libvips_runtime():
        return True

    winget = shutil.which("winget")
    if winget:
        candidates = [
            ["winget", "install", "-e", "--id", "libvips.Libvips", "--accept-package-agreements", "--accept-source-agreements"],
            ["winget", "install", "-e", "--id", "vips.vips", "--accept-package-agreements", "--accept-source-agreements"],
        ]
        for cmd in candidates:
            if _run(cmd) and _has_libvips_runtime():
                return True

    choco = shutil.which("choco")
    if choco:
        if _run(["choco", "install", "vips", "-y"]) and _has_libvips_runtime():
            return True

    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Smart Glasses runtime dependencies")
    parser.add_argument("--manager", choices=["auto", "pip", "uv"], default="auto")
    parser.add_argument("--with-bs4", action="store_true", help="Install optional beautifulsoup4")
    parser.add_argument("--skip-libvips", action="store_true", help="Skip libvips runtime checks/install")
    args = parser.parse_args()

    manager = _select_manager(args.manager)
    print(f"Using installer: {manager}")
    print(f"Python: {sys.executable}")
    print("Note: libvips is a system runtime, not a pip/uv Python package.")

    checks = [
        ("speech_recognition", "SpeechRecognition"),
        ("pyaudio", "pyaudio"),
        ("pyvips", "pyvips"),
        ("pygame", "pygame"),
    ]
    if args.with_bs4:
        checks.append(("bs4", "beautifulsoup4"))

    failed = []
    for module_name, package_name in checks:
        if _has_module(module_name):
            print(f"[OK] {module_name}")
            continue

        print(f"[MISS] {module_name} -> installing {package_name}")
        if not _install_pkg(manager, package_name):
            failed.append(package_name)
        else:
            print(f"[DONE] {package_name}")

    # Piper is CLI-first; ensure executable exists.
    if shutil.which("piper"):
        print("[OK] piper executable")
    else:
        print("[MISS] piper executable -> installing piper-tts")
        if not _install_pkg(manager, "piper-tts"):
            failed.append("piper-tts")
        elif shutil.which("piper"):
            print("[DONE] piper-tts")
        else:
            print("[WARN] piper-tts installed but `piper` not found on PATH. Set TTS_PIPER_EXE explicitly.")

    if not args.skip_libvips:
        if _has_libvips_runtime():
            print("[OK] libvips runtime")
        else:
            print("[MISS] libvips runtime")
            if sys.platform.startswith("win"):
                ok = _install_libvips_windows()
                if ok:
                    print("[DONE] libvips runtime installed")
                else:
                    failed.append("libvips-runtime")
                    print(
                        "[FAIL] Could not auto-install libvips runtime. "
                        "Install manually: https://github.com/libvips/libvips/releases"
                    )
            else:
                failed.append("libvips-runtime")
                print("[FAIL] Install libvips via your system package manager.")

    print("\nSummary:")
    if not DEFAULT_PIPER_MODEL.exists():
        print(f"[WARN] Piper model not found at {DEFAULT_PIPER_MODEL}")
        print("       Set TTS_PIPER_EN_MODEL to your .onnx model path in environment/config.")
    if failed:
        print("Failed installs:", ", ".join(failed))
        return 1

    print("All requested dependencies are installed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
