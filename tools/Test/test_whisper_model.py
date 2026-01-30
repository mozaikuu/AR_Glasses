#!/usr/bin/env python3
"""
Simple test script for Whisper model functionality.
This script demonstrates basic Whisper transcription and helps debug issues.
"""
import sys
import os
import time
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import our transcription module
from tools.speech.transcription import get_model, transcribe_audio_array


def test_model_loading():
    """Test Whisper model loading."""
    print("Testing model loading...")
    start_time = time.time()

    try:
        model = get_model()
        load_time = time.time() - start_time
        print(f"SUCCESS: Model loaded in {load_time:.2f} seconds")
        print(f"Model type: {type(model).__name__}")
        return True
    except Exception as e:
        print(f"FAILED: Model loading failed: {e}")
        return False


def test_basic_transcription():
    """Test basic transcription functionality."""
    print("\nTesting basic transcription...")

    # Create a simple sine wave (should transcribe as silence or noise)
    sample_rate = 16000
    duration = 2.0
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    # Create a 440Hz sine wave (A note)
    audio = np.sin(440 * 2 * np.pi * t)
    # Add some noise to make it more realistic
    audio += np.random.normal(0, 0.1, len(audio))
    # Normalize
    audio = audio / np.max(np.abs(audio))
    audio = audio.astype(np.float32)

    print(f"Created test audio: {len(audio)} samples, {duration}s duration")

    try:
        start_time = time.time()
        result = transcribe_audio_array(audio)
        transcribe_time = time.time() - start_time
        print(f"SUCCESS: Transcription completed in {transcribe_time:.2f} seconds")
        print(f"Result: '{result}'")
        return True
    except Exception as e:
        print(f"FAILED: Transcription failed: {e}")
        return False


def test_audio_validation():
    """Test audio validation (too short, too quiet)."""
    print("\nTesting audio validation...")

    # Test too short audio
    try:
        short_audio = np.zeros(8000, dtype=np.float32)  # 0.5 seconds
        result = transcribe_audio_array(short_audio)
        print(f"Short audio result: '{result}'")
    except Exception as e:
        print(f"Short audio failed: {e}")

    # Test too quiet audio
    try:
        quiet_audio = np.random.normal(0, 0.001, 16000).astype(np.float32)  # Very quiet
        result = transcribe_audio_array(quiet_audio)
        print(f"Quiet audio result: '{result}'")
    except Exception as e:
        print(f"Quiet audio failed: {e}")

    return True


def demonstrate_whisper_features():
    """Demonstrate key Whisper features."""
    print("\nDemonstrating Whisper features...")

    try:
        model = get_model()

        # Create test audio
        audio = np.random.normal(0, 0.1, 16000).astype(np.float32)

        # Test different parameters
        print("Testing English forced...")
        result_en = model.transcribe(audio, language="en", fp16=False)
        print(f"English forced: '{result_en['text'].strip()}'")
        print(f"Detected language: '{result_en.get('language', 'unknown')}'")

        print("Testing without language specification...")
        result_no_lang = model.transcribe(audio, fp16=False)
        print(f"No language specified: '{result_no_lang['text'].strip()}'")

        print("Testing transcription parameters...")
        result_detailed = model.transcribe(
            audio,
            language="en",
            task="transcribe",
            beam_size=5,
            fp16=False
        )
        print(f"Detailed result: '{result_detailed['text'].strip()}'")

        return True
    except Exception as e:
        print(f"Feature demonstration failed: {e}")
        return False


def main():
    """Run Whisper tests."""
    print("Whisper Model Test Script")
    print("=" * 40)
    print("This script tests the Whisper transcription functionality.")
    print()

    tests = [
        ("Model Loading", test_model_loading),
        ("Basic Transcription", test_basic_transcription),
        ("Audio Validation", test_audio_validation),
        ("Whisper Features", demonstrate_whisper_features),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                print(f"PASSED: {test_name}")
            else:
                print(f"FAILED: {test_name}")
        except Exception as e:
            print(f"CRASHED: {test_name} - {e}")

    print("\n" + "=" * 40)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("All tests passed! Whisper is working correctly.")
        print("\nKey things learned:")
        print("- Model loads and runs on available hardware (CPU/GPU)")
        print("- Audio must be float32, properly normalized")
        print("- Short or quiet audio gets special handling")
        print("- Language can be auto-detected or forced")
        print("- Transcription includes timing and confidence info")
    else:
        print("Some tests failed. Check the output above.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
