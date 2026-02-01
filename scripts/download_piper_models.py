#!/usr/bin/env python3
"""
Download Piper TTS models for offline text-to-speech.

Piper is a fast, local, neural text-to-speech system.
https://github.com/rhasspy/piper

Usage:
    python scripts/download_piper_models.py [--voices en,ar]

Available voices:
    - en_US-lessac-medium (English, ~50MB)
    - ar_JO-karlovery (Arabic, ~60MB)
"""

import argparse
import os
import sys
from pathlib import Path
from urllib.request import urlretrieve

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import PIPER_MODEL_DIR

# Piper voice URLs (from rhasspy/piper releases v1.2.0)
PIPER_VOICES = {
    "en_US-lessac-medium": {
        "url": "https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_en_US_lessac_medium.onnx",
        "url_json": "https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_en_US_lessac_medium.onnx.json",
        "size": "~50MB",
        "description": "English (US, Lessac) - Medium quality",
    },
    "ar_JO-karlovery": {
        "url": "https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_ar_JO_karlovery_medium.onnx",
        "url_json": "https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_ar_JO_karlovery_medium.onnx.json",
        "size": "~60MB",
        "description": "Arabic (Jordan, Karlovery) - Medium quality",
    },
}

# Config paths for voices (matching config/settings.py)
PIPER_VOICE_CONFIGS = {
    "en_US-lessac-medium": PIPER_MODEL_DIR / "en_US-lessac-medium.onnx",
    "ar_JO-karlovery": PIPER_MODEL_DIR / "ar_JO-karlovery.onnx",
}


def download_file(url: str, dest_path: Path, description: str = "file") -> bool:
    """Download a file with progress indication."""
    print(f"Downloading {description}...")
    try:
        def progress_hook(count, block_size, total_size):
            percent = min(count * block_size * 100 // total_size, 100)
            if count == 0:
                return
            if count == 1 or percent in [25, 50, 75] or percent == 100:
                print(f"  [{percent:3d}%] {dest_path.name}")

        urlretrieve(url, dest_path, reporthook=progress_hook)
        print(f"  Saved: {dest_path}")
        return True
    except Exception as e:
        print(f"  Failed: {e}")
        return False


def download_voice(voice_name: str) -> bool:
    """Download a single Piper voice model."""
    if voice_name not in PIPER_VOICES:
        print(f"Unknown voice: {voice_name}")
        print(f"Available: {', '.join(PIPER_VOICES.keys())}")
        return False

    voice_info = PIPER_VOICES[voice_name]
    model_path = PIPER_VOICE_CONFIGS[voice_name]

    print(f"\n{'='*50}")
    print(f"Downloading: {voice_name}")
    print(f"Size: {voice_info['size']}")
    print(f"{'='*50}")

    # Ensure directory exists
    model_path.parent.mkdir(parents=True, exist_ok=True)

    success = True

    # Download ONNX model
    if not model_path.exists():
        success &= download_file(
            voice_info["url"],
            model_path,
            f"{voice_name} model"
        )
    else:
        print(f"  Already exists: {model_path.name}")

    # Download JSON config
    json_path = model_path.with_suffix(".onnx.json")
    if not json_path.exists():
        success &= download_file(
            voice_info["url_json"],
            json_path,
            f"{voice_name} config"
        )
    else:
        print(f"  Already exists: {json_path.name}")

    return success


def list_voices():
    """List available Piper voices."""
    print("\nAvailable Piper Voices:")
    print("-" * 50)
    for name, info in PIPER_VOICES.items():
        print(f"  {name}")
        print(f"    {info['description']}")
        print(f"    Size: {info['size']}")
    print()


def verify_installation():
    """Verify installed Piper voices."""
    print("\nVerifying Piper TTS Installation:")
    print("-" * 50)

    installed = False
    for voice_name in PIPER_VOICES.keys():
        model_path = PIPER_VOICE_CONFIGS[voice_name]
        json_path = model_path.with_suffix(".onnx.json")

        if model_path.exists() and json_path.exists():
            size_mb = model_path.stat().st_size / (1024 * 1024)
            print(f"  [OK] {voice_name} ({size_mb:.1f} MB)")
            installed = True
        else:
            print(f"  [MISSING] {voice_name}")

    if not installed:
        print("\nNo voices installed.")
        print("Run: python scripts/download_piper_models.py --voices en,ar")
    else:
        print(f"\nInstalled: {len([v for v in PIPER_VOICE_CONFIGS.values() if v.exists()])} voices")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Download Piper TTS voice models for offline text-to-speech."
    )
    parser.add_argument(
        "--voices",
        type=str,
        default="en_US-lessac-medium,ar_JO-karlovery",
        help="Comma-separated voices (default: en_US-lessac-medium,ar_JO-karlovery)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available voices"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify installed voices"
    )

    args = parser.parse_args()

    if args.list:
        list_voices()
        return 0

    if args.verify:
        verify_installation()
        return 0

    # Parse voice list
    voices_to_download = [v.strip() for v in args.voices.split(",")]

    # Ensure model directory exists
    PIPER_MODEL_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*50}")
    print("Piper TTS Model Downloader")
    print(f"{'='*50}")
    print(f"Output: {PIPER_MODEL_DIR}")
    print(f"Voices: {', '.join(voices_to_download)}")
    print(f"{'='*50}\n")

    success = True
    for voice_name in voices_to_download:
        if not download_voice(voice_name):
            success = False

    print(f"\n{'='*50}")
    if success:
        print("Download complete!")
        print(f"Models at: {PIPER_MODEL_DIR}")
    else:
        print("Some downloads failed.")
    print(f"{'='*50}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())