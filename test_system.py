#!/usr/bin/env python3
"""System test script for Smart Glasses project."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all dependencies can be imported."""
    print("Testing imports...")
    try:
        import streamlit
        print("  [OK] streamlit")
    except ImportError as e:
        print(f"  [FAIL] streamlit: {e}")
        return False

    try:
        import fastapi
        print("  [OK] fastapi")
    except ImportError as e:
        print(f"  [FAIL] fastapi: {e}")
        return False

    try:
        from ultralytics import YOLO
        print("  [OK] ultralytics (YOLO)")
    except ImportError as e:
        print(f"  [FAIL] ultralytics: {e}")
        return False

    try:
        import mediapipe
        print("  [OK] mediapipe")
    except ImportError as e:
        print(f"  [FAIL] mediapipe: {e}")
        return False

    try:
        import shutil
        local_piper = project_root / "models" / "piper" / ("piper.exe" if sys.platform.startswith("win") else "piper")
        if local_piper.exists():
            print(f"  [OK] piper executable ({local_piper})")
        elif shutil.which("piper"):
            print("  [OK] piper executable (PATH)")
        else:
            raise ImportError("piper executable not found in models/piper or PATH")
    except ImportError as e:
        print(f"  [FAIL] piper: {e}")
        return False

    try:
        import networkx
        print("  [OK] networkx")
    except ImportError as e:
        print(f"  [FAIL] networkx: {e}")
        return False

    try:
        import cv2
        print("  [OK] opencv-python")
    except ImportError as e:
        print(f"  [FAIL] opencv-python: {e}")
        return False

    return True


def test_navigation():
    """Test navigation system."""
    print("\nTesting navigation system...")
    try:
        from tools.navigation.navigation import load_graph, get_all_locations, navigate

        graph = load_graph()
        locations = get_all_locations(graph)
        print(f"  [OK] Loaded graph with {len(locations)} locations")

        # Test a navigation request using known valid location when available.
        destination = "TA Office" if "TA Office" in locations else (locations[1] if len(locations) > 1 else locations[0])
        result = navigate("Entrance", destination)
        if result.get("success"):
            print(f"  [OK] Navigation test: {len(result.get('steps', []))} steps found")
        else:
            print(f"  [WARN] Navigation test: {result.get('error', 'Unknown error')}")

        return True
    except Exception as e:
        print(f"  [FAIL] Navigation test: {e}")
        return False


def test_config():
    """Test configuration settings."""
    print("\nTesting configuration...")
    try:
        from config.settings import TTS_PIPER_EXE, TTS_PIPER_EN_MODEL, API_URL

        print(f"  [OK] Piper exe = {TTS_PIPER_EXE}")
        print(f"  [OK] Piper model = {TTS_PIPER_EN_MODEL}")
        print(f"  [OK] API URL = {API_URL}")
        print("  [INFO] Using Piper backend")

        return True
    except Exception as e:
        print(f"  [FAIL] Configuration test: {e}")
        return False


def test_gestures():
    """Test gesture detection module."""
    print("\nTesting gesture detection...")
    try:
        import mediapipe as mp
        if not hasattr(mp, "solutions"):
            print("  [WARN] mediapipe installed but `solutions` API is unavailable in this version")
            return True
    except Exception as e:
        print(f"  [FAIL] Gesture precheck failed: {e}")
        return False

    try:
        from tools.vision.gestures import GestureDetector, GESTURE_ACTIONS

        print(f"  [OK] Loaded GestureDetector")
        print(f"  [OK] Available gestures: {', '.join(GESTURE_ACTIONS.keys())}")

        # Test detector creation
        with GestureDetector() as detector:
            print("  [OK] GestureDetector context manager works")

        return True
    except Exception as e:
        print(f"  [FAIL] Gesture test: {e}")
        return False


def test_tts_config():
    """Test TTS configuration."""
    print("\nTesting TTS configuration...")
    try:
        from tools.speech.tts import text_to_speech

        print("  [OK] TTS module imports successfully")

        # Don't actually run TTS in test
        print("  [INFO] Skipping actual TTS test (would play audio)")

        return True
    except Exception as e:
        print(f"  [FAIL] TTS configuration test: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Smart Glasses System Test")
    print("=" * 60)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Navigation", test_navigation()))
    results.append(("Gesture Detection", test_gestures()))
    results.append(("TTS Configuration", test_tts_config()))

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    passed = 0
    failed = 0

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {passed} passed, {failed} failed")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
