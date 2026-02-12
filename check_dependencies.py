"""Check if core runtime dependencies are installed."""
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent

required_packages = [
    "fastapi",
    "uvicorn",
    "flask",
    "streamlit",
    "streamlit_webrtc",
    "pydantic",
    "torch",
    "transformers",
    "PIL",
    "numpy",
    "cv2",
    "ultralytics",
    "whisper",
    "mutagen",
    "pygame",
    "pyaudio",
    "duckduckgo_search",
    "bs4",
    "requests",
    "fastmcp",
    "piper",
]


def _has_piper() -> bool:
    local = PROJECT_ROOT / "models" / "piper" / ("piper.exe" if sys.platform.startswith("win") else "piper")
    return local.exists() or bool(shutil.which("piper"))


def main() -> int:
    missing_packages = []
    print("Checking dependencies...\n")

    for package in required_packages:
        try:
            if package == "PIL":
                __import__("PIL")
            elif package == "cv2":
                __import__("cv2")
            elif package == "bs4":
                __import__("bs4")
            elif package == "streamlit_webrtc":
                __import__("streamlit_webrtc")
            elif package == "piper":
                if not _has_piper():
                    raise ImportError("piper executable not found in models/piper or PATH")
            else:
                __import__(package)
            print(f"[OK] {package}")
        except ImportError:
            print(f"[MISS] {package}")
            missing_packages.append(package)

    print("\n" + "=" * 50)
    if missing_packages:
        print(f"\n{len(missing_packages)} package(s) missing:")
        for pkg in missing_packages:
            print(f" - {pkg}")
        print("\nInstall dependencies with:")
        print(" uv sync")
        print(" or")
        print(" pip install -r requirements.txt")
        return 1

    print("\nAll dependencies are installed.")
    print("You can now start the gateway with: python start_gateway.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
