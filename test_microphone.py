#!/usr/bin/env python3
"""
Microphone testing script for Whisper transcription.
This script records audio from your microphone and transcribes it using Whisper.

Usage:
    python test_microphone.py

Instructions:
    1. Run the script
    2. Allow microphone permissions when prompted
    3. Speak clearly when "Recording..." appears
    4. Wait for transcription results
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
from tools.speech.transcription import transcribe_audio_array


def record_audio(duration=5.0, sample_rate=44100, channels=1):
    """
    Record audio from microphone.

    Args:
        duration: Recording duration in seconds
        sample_rate: Audio sample rate (Hz)
        channels: Number of audio channels (1=mono, 2=stereo)

    Returns:
        numpy array: Recorded audio data
    """
    try:
        import pyaudio
    except ImportError:
        print("ERROR: pyaudio not installed. Install with: pip install pyaudio")
        return None

    print(f"Initializing microphone (sample rate: {sample_rate}Hz, channels: {channels})...")

    # Audio settings
    chunk = 1024
    format_type = pyaudio.paFloat32  # Use float32 for easier processing

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    try:
        # Find default input device
        default_device = p.get_default_input_device_info()
        device_index = default_device['index']
        device_name = default_device['name']
        print(f"Using input device: {device_name} (index: {device_index})")

        # Open audio stream
        stream = p.open(
            format=format_type,
            channels=channels,
            rate=sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=chunk
        )

        print("🎤 Microphone ready! Get ready to speak...")
        print(f"Recording will start in 3 seconds and last {duration} seconds.")

        # Countdown
        for i in range(3, 0, -1):
            print(f"{i}...")
            time.sleep(1)

        print("🔴 RECORDING... Start speaking now!")

        # Record audio
        frames = []
        start_time = time.time()

        while time.time() - start_time < duration:
            try:
                data = stream.read(chunk, exception_on_overflow=False)
                frames.append(data)
            except IOError as e:
                print(f"Warning: Audio buffer overflow ({e}), continuing...")
                continue

        # Stop recording
        stream.stop_stream()
        stream.close()
        p.terminate()

        recording_time = time.time() - start_time
        print(f"Recording completed in {recording_time:.1f} seconds")
        # Convert frames to numpy array
        if format_type == pyaudio.paFloat32:
            audio_data = np.frombuffer(b''.join(frames), dtype=np.float32)
        elif format_type == pyaudio.paInt16:
            audio_data = np.frombuffer(b''.join(frames), dtype=np.int16).astype(np.float32)
            audio_data /= np.iinfo(np.int16).max
        elif format_type == pyaudio.paInt32:
            audio_data = np.frombuffer(b''.join(frames), dtype=np.int32).astype(np.float32)
            audio_data /= np.iinfo(np.int32).max
        else:
            print("ERROR: Unsupported audio format")
            return None

        # Ensure proper shape
        if channels > 1:
            audio_data = audio_data.reshape(-1, channels)
            # Convert to mono by averaging channels
            audio_data = np.mean(audio_data, axis=1)

        print(f"Audio captured: {len(audio_data)} samples, {len(audio_data)/sample_rate:.1f}s duration")
        print(f"Audio range: [{audio_data.min():.3f}, {audio_data.max():.3f}]")

        return audio_data

    except Exception as e:
        print(f"ERROR: Failed to record audio: {e}")
        if 'p' in locals():
            p.terminate()
        return None


def test_microphone_transcription():
    """Test microphone recording and transcription."""
    print("Whisper Microphone Transcription Test")
    print("=" * 45)

    # Step 1: Record audio
    print("\nStep 1: Recording from microphone...")
    audio_data = record_audio(duration=5.0, sample_rate=16000, channels=1)

    if audio_data is None:
        print("Failed to record audio. Exiting.")
        return False

    # Step 2: Transcribe audio
    print("\nStep 2: Transcribing audio with Whisper...")
    try:
        start_time = time.time()
        transcription = transcribe_audio_array(audio_data)
        transcribe_time = time.time() - start_time

        print(f"Transcription completed in {transcribe_time:.2f} seconds")
        print(f"Transcription: '{transcription}'")

        if not transcription.strip():
            print("\nNOTE: No speech detected. This could be because:")
            print("- You didn't speak during recording")
            print("- Speech was too quiet or unclear")
            print("- Background noise interfered")
            print("- Try speaking louder and closer to the microphone")
        else:
            print("\nSUCCESS: Speech detected and transcribed!")

        return True

    except Exception as e:
        print(f"ERROR: Transcription failed: {e}")
        return False


def interactive_test():
    """Run an interactive microphone test."""
    print("Interactive Microphone Transcription Test")
    print("=" * 50)
    print("This will record 5 seconds of audio and transcribe it.")
    print("Make sure your microphone is enabled and not muted.")
    print()

    # Ask for confirmation
    try:
        response = input("Ready to test? Press Enter to start, or 'q' to quit: ")
        if response.lower() in ['q', 'quit', 'exit']:
            print("Test cancelled.")
            return
    except KeyboardInterrupt:
        print("\nTest cancelled.")
        return

    # Run the test
    success = test_microphone_transcription()

    if success:
        print("\n" + "=" * 50)
        print("Test completed successfully!")
        print("\nTips for better results:")
        print("- Speak clearly and at normal volume")
        print("- Reduce background noise")
        print("- Hold microphone close to your mouth")
        print("- Speak in complete sentences")
    else:
        print("\n" + "=" * 50)
        print("Test failed. Check the error messages above.")


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(__doc__)
        return

    try:
        interactive_test()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")


if __name__ == "__main__":
    main()
