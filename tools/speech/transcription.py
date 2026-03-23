from __future__ import annotations

import base64
import io
import wave

def transcribe_audio(audio_base64: str) -> str:
    """Transcribe base64 audio using Google SpeechRecognition backend.

    Expects a WAV container for best results (as produced by Streamlit audio_input).
    Returns empty string on failures so callers can decide fallback UX.
    """
    if not audio_base64:
        return ""

    try:
        import speech_recognition as sr
    except Exception:
        return ""

    try:
        audio_bytes = base64.b64decode(audio_base64)
    except Exception:
        return ""

    if not audio_bytes:
        return ""

    raw_pcm = b""
    sample_rate = 16000
    sample_width = 2

    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav_reader:
            sample_rate = int(wav_reader.getframerate())
            sample_width = int(wav_reader.getsampwidth())
            raw_pcm = wav_reader.readframes(wav_reader.getnframes())
    except Exception:
        # Fallback: assume raw PCM16 mono at 16k if container parsing fails.
        raw_pcm = audio_bytes
        sample_rate = 16000
        sample_width = 2

    if not raw_pcm:
        return ""

    try:
        recognizer = sr.Recognizer()
        audio_data = sr.AudioData(raw_pcm, sample_rate, sample_width)
        text = recognizer.recognize_google(audio_data, language="en-US")
        return (text or "").strip()
    except Exception:
        return ""
