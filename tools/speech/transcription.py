"""Audio transcription using Google Speech Recognition with Whisper fallback."""
import numpy as np
from typing import Union
import io

# Import speech recognition libraries
try:
    import speech_recognition as sr
    GOOGLE_SPEECH_AVAILABLE = True
except ImportError:
    GOOGLE_SPEECH_AVAILABLE = False
    print("Warning: speech_recognition not available, using Whisper fallback", file=__import__('sys').stderr)

# Fallback Whisper imports
_whisper_model = None
def get_whisper_model():
    """Get or load Whisper model (fallback only)."""
    global _whisper_model
    if _whisper_model is None:
        try:
            import torch
            import whisper
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Loading Whisper tiny model on {device} (fallback)...", file=__import__('sys').stderr)
            _whisper_model = whisper.load_model("tiny").to(device)
            print("Whisper model loaded successfully", file=__import__('sys').stderr)
        except ImportError:
            print("Warning: Whisper not available", file=__import__('sys').stderr)
            _whisper_model = None
    return _whisper_model


def transcribe_audio_bytes(audio_bytes: bytes, sample_rate: int = 16000, dtype: str = "float32") -> str:
    """
    Transcribe audio from bytes using Google Speech Recognition with Whisper fallback.
    
    Args:
        audio_bytes: Raw audio bytes
        sample_rate: Sample rate of the audio (default: 16000 for Google Speech)
        dtype: Data type of audio bytes ("int16", "int32", "float32")
        
    Returns:
        Transcribed text
    """
    print(f"DEBUG: Transcribing audio_bytes with dtype={dtype}, length={len(audio_bytes)}, sample_rate={sample_rate}", file=__import__('sys').stderr)

    # Try Google Speech Recognition first (fast and accurate for short clips)
    if GOOGLE_SPEECH_AVAILABLE:
        print(f"DEBUG: Attempting Google Speech Recognition...", file=__import__('sys').stderr)
        try:
            # Convert audio bytes to WAV format for Google Speech Recognition
            print(f"DEBUG: Converting audio to WAV format...", file=__import__('sys').stderr)
            wav_data = convert_to_wav(audio_bytes, sample_rate, dtype)
            print(f"DEBUG: WAV conversion successful, size: {len(wav_data)} bytes", file=__import__('sys').stderr)

            # Create speech recognition object
            print(f"DEBUG: Creating speech recognition objects...", file=__import__('sys').stderr)
            recognizer = sr.Recognizer()
            audio_data = sr.AudioData(wav_data, sample_rate, 2)  # 16-bit
            print(f"DEBUG: AudioData created successfully", file=__import__('sys').stderr)

            # Recognize
            print(f"DEBUG: Calling Google Speech API...", file=__import__('sys').stderr)
            result = recognizer.recognize_google(audio_data, language="en-US")
            result = result.strip()
            print(f"DEBUG: Google API call completed", file=__import__('sys').stderr)

            if result:
                print(f"DEBUG: Google Speech SUCCESS: '{result}'", file=__import__('sys').stderr)
                return result
            else:
                print("DEBUG: Google Speech returned empty result", file=__import__('sys').stderr)

        except sr.UnknownValueError as e:
            print(f"DEBUG: Google Speech could not understand audio: {e}", file=__import__('sys').stderr)
        except sr.RequestError as e:
            print(f"DEBUG: Google Speech service error: {e}", file=__import__('sys').stderr)
        except Exception as e:
            print(f"DEBUG: Google Speech failed with {type(e).__name__}: {e}", file=__import__('sys').stderr)
            import traceback
            traceback.print_exc(file=__import__('sys').stderr)

    # Fallback to Whisper if Google Speech fails
    print(f"DEBUG: Falling back to Whisper transcription...", file=__import__('sys').stderr)
    return transcribe_audio_bytes_whisper(audio_bytes, sample_rate, dtype)


def transcribe_audio_bytes_whisper(audio_bytes: bytes, sample_rate: int = 16000, dtype: str = "float32") -> str:
    """
    Transcribe audio using Whisper (fallback method).
    """
    try:
        import torch
        import whisper
    except ImportError:
        print("DEBUG: Whisper not available", file=__import__('sys').stderr)
        return ""

    # Convert bytes to numpy array based on dtype
    if dtype == "int16":
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        audio_array = audio_array.astype(np.float32) / np.iinfo(np.int16).max
    elif dtype == "int32":
        audio_array = np.frombuffer(audio_bytes, dtype=np.int32)
        audio_array = audio_array.astype(np.float32) / np.iinfo(np.int32).max
    elif dtype == "float32":
        audio_array = np.frombuffer(audio_bytes, dtype=np.float32).copy()
        if np.max(np.abs(audio_array)) > 1.0:
            audio_array = audio_array / np.max(np.abs(audio_array))
    else:
        raise ValueError(f"Unsupported dtype: {dtype}")

    print(f"DEBUG: Whisper audio shape: {audio_array.shape}, range: [{audio_array.min():.3f}, {audio_array.max():.3f}]", file=__import__('sys').stderr)

    # Validation
    if len(audio_array) < 8000:
        print(f"DEBUG: Audio too short ({len(audio_array)} samples)", file=__import__('sys').stderr)
        return ""
    if np.max(np.abs(audio_array)) < 0.005:
        print(f"DEBUG: Audio too quiet (max amplitude: {np.max(np.abs(audio_array)):.6f})", file=__import__('sys').stderr)
        return ""

    model = get_whisper_model()
    if model is None:
        return ""

    result = model.transcribe(
        audio_array,
        fp16=torch.cuda.is_available(),
        language="en",
        task="transcribe",
        beam_size=1,
        patience=1.0,
        temperature=0.0,
    )

    transcribed_text = result["text"].strip()
    print(f"DEBUG: Whisper result: '{transcribed_text}'", file=__import__('sys').stderr)
    return transcribed_text


def convert_to_wav(audio_bytes: bytes, sample_rate: int, dtype: str) -> bytes:
    """
    Convert audio bytes to WAV format for Google Speech Recognition.
    """
    import wave
    import struct

    # Convert to 16-bit PCM
    if dtype == "float32":
        audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
        # Convert float32 [-1, 1] to int16
        audio_array = (audio_array * 32767).astype(np.int16)
    elif dtype == "int32":
        audio_array = np.frombuffer(audio_bytes, dtype=np.int32)
        audio_array = (audio_array / 65536).astype(np.int16)  # Scale down to int16 range
    elif dtype == "int16":
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
    else:
        raise ValueError(f"Unsupported dtype: {dtype}")
    
    # Create WAV file in memory
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_array.tobytes())

    return wav_buffer.getvalue()


def transcribe_audio_array(audio_array: np.ndarray, sample_rate: int = 16000) -> str:
    """
    Transcribe audio from numpy array using Google Speech Recognition with Whisper fallback.
    
    Args:
        audio_array: Audio as numpy array (float32, normalized to [-1, 1])
        sample_rate: Sample rate of the audio
        
    Returns:
        Transcribed text
    """
    # Try Google Speech Recognition first
    print(f"DEBUG: GOOGLE_SPEECH_AVAILABLE = {GOOGLE_SPEECH_AVAILABLE}", file=__import__('sys').stderr)
    if GOOGLE_SPEECH_AVAILABLE:
        try:
            # Convert numpy array to WAV bytes
            wav_data = convert_numpy_to_wav(audio_array, sample_rate)

            recognizer = sr.Recognizer()
            audio_data = sr.AudioData(wav_data, sample_rate, 2)  # 16-bit

            print(f"DEBUG: Using Google Speech Recognition for array...", file=__import__('sys').stderr)
            result = recognizer.recognize_google(audio_data, language="en-US")
            result = result.strip()

            if result:
                print(f"DEBUG: Google Speech result: '{result}'", file=__import__('sys').stderr)
                return result

        except sr.UnknownValueError:
            print("DEBUG: Google Speech could not understand audio array", file=__import__('sys').stderr)
        except sr.RequestError as e:
            print(f"DEBUG: Google Speech service error: {e}", file=__import__('sys').stderr)
        except Exception as e:
            print(f"DEBUG: Google Speech failed: {e}", file=__import__('sys').stderr)

    # Fallback to Whisper
    print(f"DEBUG: Falling back to Whisper for array...", file=__import__('sys').stderr)
    return transcribe_audio_array_whisper(audio_array)


def transcribe_audio_array_whisper(audio_array: np.ndarray) -> str:
    """
    Transcribe audio array using Whisper (fallback).
    """
    try:
        import torch
        import whisper
    except ImportError:
        print("DEBUG: Whisper not available", file=__import__('sys').stderr)
        return ""

    model = get_whisper_model()
    if model is None:
        return ""

    result = model.transcribe(audio_array, fp16=False)
    return result["text"].strip()


def convert_numpy_to_wav(audio_array: np.ndarray, sample_rate: int) -> bytes:
    """
    Convert numpy array to WAV bytes for Google Speech Recognition.
    """
    import wave

    # Ensure proper format
    audio_array = np.clip(audio_array, -1.0, 1.0)
    audio_int16 = (audio_array * 32767).astype(np.int16)

    # Create WAV file in memory
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())

    return wav_buffer.getvalue()


def transcribe_audio(record_seconds=5, device_index=13):  # Use Realtek mic by default
    """
    Record audio from microphone and transcribe.
    Full pipeline for microphone input.

    Args:
        record_seconds: Duration to record in seconds (default: 5)
        device_index: Audio device index to use (default: None, auto-detect)
    """
    import pyaudio
    
    FORMAT = pyaudio.paInt16  # Use 16-bit for better compatibility
    channels = 1
    sample_rate = 16000  # Use 16kHz for better Google Speech compatibility
    chunk = 1024

    # Use default device if not specified
    if device_index is None:
        device_index = None  # Use default system device
    
    p = pyaudio.PyAudio()

    # Debug: List available audio devices
    print(f"DEBUG: Available audio devices:", file=__import__('sys').stderr)
    for i in range(p.get_device_count()):
        try:
            device_info = p.get_device_info_by_index(i)
            print(f"DEBUG: Device {i}: {device_info.get('name')} (inputs: {device_info.get('maxInputChannels')})", file=__import__('sys').stderr)
        except Exception as e:
            print(f"DEBUG: Error getting device {i} info: {e}", file=__import__('sys').stderr)

    print(f"DEBUG: Using device index: {device_index}", file=__import__('sys').stderr)
    stream = p.open(
        format=FORMAT,
        channels=channels,
        rate=sample_rate,
        input=True,
        output=False,
        input_device_index=device_index,
        frames_per_buffer=chunk
    )
    
    frames = []
    print("Recording...")
    for i in range(int(sample_rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)
    
    print("Finished recording.")
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Convert audio frames to numpy array
    audio_data = b''.join(frames)
    audio_array = np.frombuffer(audio_data, dtype=np.int16)

    # Convert to float32 and normalize properly
    audio_array = audio_array.astype(np.float32)
    # Normalize from int16 range to [-1, 1]
    max_val = float(np.iinfo(np.int16).max)
    audio_array = audio_array / max_val

    print(f"[AUDIO] Recorded: {len(audio_array)} samples at {sample_rate}Hz, range: [{audio_array.min():.3f}, {audio_array.max():.3f}]", file=__import__('sys').stderr)

    result = transcribe_audio_array(audio_array, sample_rate)
    print(f"[DEBUG] Raw transcription result: '{result}' (length: {len(result)})", file=__import__('sys').stderr)
    return result


if __name__ == "__main__":
    """
    Run transcription tests directly from command line.

    Usage:
    python tools/speech/transcription.py microphone    # Test with microphone
    python tools/speech/transcription.py file <path>   # Test with audio file
    python tools/speech/transcription.py synthetic     # Test with synthetic audio
    """
    import sys
    import os

    if len(sys.argv) < 2:
        print("Usage: python tools/speech/transcription.py <test_type> [args...]")
        print("  microphone [device]  - Test with live microphone input (device 13=default)")
        print("  file <path>          - Test with audio file (WAV/MP3 format)")
        print("  synthetic            - Test with generated sine wave")
        sys.exit(1)

    test_type = sys.argv[1].lower()

    if test_type == "microphone":
        # Allow specifying device index
        device_index = 13  # Default to Realtek mic
        if len(sys.argv) >= 3:
            try:
                device_index = int(sys.argv[2])
            except ValueError:
                print(f"[ERROR] Invalid device index: {sys.argv[2]}")
                sys.exit(1)

        print(f"[MIC] Testing with microphone input (device {device_index})...")
        print("Speak clearly and loudly for 3 seconds after 'Recording...' appears...")
        print("Make sure your microphone is not muted and volume is turned up.")
        try:
            result = transcribe_audio(record_seconds=3, device_index=device_index)
            print(f"\n[RESULT] Transcription: '{result}'")
            if not result or result.strip() == "":
                print("\n[TIPS] No speech detected. Try:")
                print("  - Speaking louder and closer to the microphone")
                print("  - Checking microphone permissions/settings")
                print("  - Using a different microphone device")
                print("  - Running: python tools/speech/transcription.py synthetic")
                print("  - Try: python tools/speech/transcription.py microphone <device_number>")
        except Exception as e:
            print(f"[ERROR] {e}")

    elif test_type == "file":
        if len(sys.argv) < 3:
            print("[ERROR] Usage: python tools/speech/transcription.py file <audio_file_path>")
            sys.exit(1)

        file_path = sys.argv[2]
        if not os.path.exists(file_path):
            print(f"[ERROR] File not found: {file_path}")
            sys.exit(1)

        print(f"[FILE] Testing with audio file: {file_path}")

        try:
            # Load audio file
            import librosa
            audio_array, sample_rate = librosa.load(file_path, sr=16000, mono=True)
            audio_array = audio_array.astype(np.float32)

            print(f"[AUDIO] Loaded: {len(audio_array)} samples, {sample_rate}Hz")

            # Transcribe
            result = transcribe_audio_array(audio_array)
            print(f"\n[RESULT] Transcription: '{result}'")

        except ImportError:
            print("[ERROR] librosa not installed. Install with: pip install librosa")
        except Exception as e:
            print(f"[ERROR] {e}")

    elif test_type == "synthetic":
        print("[SYNTH] Testing with synthetic audio (sine wave)...")

        # Generate a test tone that might be recognizable
        sample_rate = 16000
        duration = 2.0
        frequency = 440  # A note
        t = np.linspace(0, duration, int(sample_rate * duration), False)

        # Create a sine wave
        audio_array = np.sin(frequency * 2 * np.pi * t)
        audio_array = audio_array.astype(np.float32)

        print(f"[AUDIO] Generated sine wave: {len(audio_array)} samples, {frequency}Hz")

        # Transcribe
        result = transcribe_audio_array(audio_array)
        print(f"\n[RESULT] Transcription: '{result}'")
        print("Note: Sine waves typically transcribe as random words or nothing meaningful")

    else:
        print(f"[ERROR] Unknown test type: {test_type}")
        print("Available types: microphone, file, synthetic")
        sys.exit(1)

