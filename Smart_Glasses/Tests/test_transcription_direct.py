#!/usr/bin/env python3
"""
Simple direct test for transcription functionality.
Run this to quickly test microphone transcription.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.speech.transcription import transcribe_audio

def main():
    print("[MIC] Direct Transcription Test")
    print("This test will help diagnose microphone issues.")
    print("Make sure:")
    print("  - Your microphone is not muted")
    print("  - Microphone volume is turned up in system settings")
    print("  - You're speaking clearly and loudly")
    print("  - Try different microphone devices if available")
    print()

    # First, show available devices
    print("Available microphone devices:")
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        mic_count = 0
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info.get('maxInputChannels', 0) > 0:
                print(f"  Device {i}: {device_info.get('name')}")
                mic_count += 1
        p.terminate()
        if mic_count == 0:
            print("  No microphone devices found!")
            return
    except Exception as e:
        print(f"  Error checking devices: {e}")

    print()
    print("Speak clearly and loudly for 3 seconds after 'Recording...' appears...")

    try:
        result = transcribe_audio(record_seconds=3)
        print(f"\n[SUCCESS] Transcription: '{result}'")
        if not result or result.strip() == "":
            print("\n[WARNING] No speech detected. Try:")
            print("  - Speaking louder and closer to the microphone")
            print("  - Checking microphone permissions/settings")
            print("  - Using a different microphone device (try device 13 or 1)")
            print("  - Testing with: python tools/speech/transcription.py synthetic")
            print("  - Checking Windows Sound settings for microphone levels")
        else:
            print("[SUCCESS] Speech was transcribed!")
    except KeyboardInterrupt:
        print("\n[CANCELLED] Test cancelled by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("Make sure your microphone is connected and permissions are granted.")

if __name__ == "__main__":
    main()
