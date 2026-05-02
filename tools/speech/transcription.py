from __future__ import annotations

import base64
import io
import logging
import time
import wave
from collections.abc import Mapping
from typing import Any

from app.config.settings import settings


logger = logging.getLogger(__name__)


def _as_int(value: object, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _decode_audio_bytes(audio_base64: str) -> tuple[bytes, str | None]:
    payload = (audio_base64 or "").strip()
    if not payload:
        return b"", "empty_input"

    if payload.startswith("data:") and "," in payload:
        payload = payload.split(",", 1)[1]

    try:
        return base64.b64decode(payload), None
    except Exception:
        return b"", "base64_decode_failed"


def _is_retryable_error(exc: Exception) -> bool:
    message = str(exc).lower()
    retry_tokens = ("timeout", "timed out", "tempor", "unavailable", "connection")
    return any(token in message for token in retry_tokens)


def transcribe_audio_detailed(
    audio_base64: str,
    metadata: Mapping[str, Any] | None = None,
) -> tuple[str, dict[str, object]]:
    """Transcribe base64 audio and return transcript plus STT diagnostics."""
    stt_debug: dict[str, object] = {
        "provider": "google_speech_recognition",
        "audio_container": "unknown",
        "audio_format": "unknown",
        "sample_rate": 16000,
        "sample_width": 2,
        "retry_attempts_configured": max(1, int(settings.stt_retry_attempts)),
        "retry_backoff_ms": max(0, int(settings.stt_retry_backoff_ms)),
    }

    try:
        import speech_recognition as sr
    except Exception:
        stt_debug["error"] = "speech_recognition_unavailable"
        return "", stt_debug

    audio_bytes, decode_error = _decode_audio_bytes(audio_base64)
    if decode_error is not None:
        stt_debug["error"] = decode_error
        return "", stt_debug

    if not audio_bytes:
        stt_debug["error"] = "empty_audio_bytes"
        return "", stt_debug

    raw_pcm = b""
    sample_rate = 16000
    sample_width = 2
    decoded = False

    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav_reader:
            sample_rate = int(wav_reader.getframerate())
            sample_width = int(wav_reader.getsampwidth())
            raw_pcm = wav_reader.readframes(wav_reader.getnframes())
            stt_debug["audio_container"] = "wav"
            stt_debug["audio_format"] = "wav_pcm"
            decoded = True
    except Exception:
        pass

    if not decoded:
        try:
            from pydub import AudioSegment

            seg = AudioSegment.from_file(io.BytesIO(audio_bytes))
            raw_pcm = seg.raw_data
            sample_rate = max(8000, int(seg.frame_rate))
            sample_width = max(1, min(4, int(seg.sample_width)))
            stt_debug["audio_container"] = "compressed"
            stt_debug["audio_format"] = "pydub_decoded"
            decoded = bool(raw_pcm)
        except Exception as exc:
            stt_debug["pydub_error"] = str(exc)

    if not decoded:
        # Fallback: raw PCM16 mono at configured/default sample rate (Expo / legacy clients).
        raw_pcm = audio_bytes
        raw_meta = metadata if isinstance(metadata, Mapping) else {}
        sample_rate = max(8000, _as_int(raw_meta.get("sample_rate"), 16000))
        sample_width = max(1, min(4, _as_int(raw_meta.get("sample_width"), 2)))
        stt_debug["audio_container"] = "raw"
        stt_debug["audio_format"] = str(raw_meta.get("audio_format") or "pcm16")

    if sample_width > 1 and (len(raw_pcm) % sample_width) != 0:
        raw_pcm = raw_pcm[: len(raw_pcm) - (len(raw_pcm) % sample_width)]

    if not raw_pcm:
        stt_debug["error"] = "empty_pcm"
        return "", stt_debug

    stt_debug["sample_rate"] = sample_rate
    stt_debug["sample_width"] = sample_width
    stt_debug["pcm_bytes"] = len(raw_pcm)
    stt_debug["min_transcript_chars"] = max(1, int(settings.wake_min_transcript_chars))

    recognizer = sr.Recognizer()
    audio_data = sr.AudioData(raw_pcm, sample_rate, sample_width)
    max_attempts = max(1, int(settings.stt_retry_attempts))
    backoff_seconds = max(0, int(settings.stt_retry_backoff_ms)) / 1000.0
    retry_errors: list[str] = []

    for attempt in range(1, max_attempts + 1):
        stt_debug["attempt"] = attempt
        stt_debug["retry_count"] = attempt - 1
        try:
            text = recognizer.recognize_google(audio_data, language="en-US")
            cleaned = (text or "").strip()
            stt_debug["ok"] = bool(cleaned)
            if retry_errors:
                stt_debug["retry_errors"] = retry_errors
            return cleaned, stt_debug
        except sr.UnknownValueError:
            stt_debug["error"] = "stt_unknown_value"
            stt_debug["ok"] = False
            logger.info("STT could not understand audio (provider=google, bytes=%s)", len(raw_pcm))
            return "", stt_debug
        except sr.RequestError as exc:
            retry_errors.append(str(exc))
            if attempt < max_attempts:
                if backoff_seconds > 0:
                    time.sleep(backoff_seconds * attempt)
                continue
            stt_debug["error"] = "stt_request_error"
            stt_debug["error_detail"] = str(exc)
            stt_debug["ok"] = False
            stt_debug["retry_errors"] = retry_errors
            logger.warning("STT request failed after retries: %s", exc)
            return "", stt_debug
        except Exception as exc:
            retryable = _is_retryable_error(exc)
            if retryable and attempt < max_attempts:
                retry_errors.append(str(exc))
                if backoff_seconds > 0:
                    time.sleep(backoff_seconds * attempt)
                continue
            stt_debug["error"] = "stt_recognition_failed"
            stt_debug["error_detail"] = str(exc)
            stt_debug["ok"] = False
            if retry_errors:
                stt_debug["retry_errors"] = retry_errors
            logger.warning("STT recognition failed: %s", exc)
            return "", stt_debug

    stt_debug["error"] = "stt_exhausted_retries"
    stt_debug["ok"] = False
    if retry_errors:
        stt_debug["retry_errors"] = retry_errors
    return "", stt_debug

def transcribe_audio(audio_base64: str) -> str:
    """Transcribe base64 audio using Google SpeechRecognition backend.

    Expects a WAV container for best results (as produced by Streamlit audio_input).
    Returns empty string on failures so callers can decide fallback UX.
    """
    text, _stt_debug = transcribe_audio_detailed(audio_base64, metadata=None)
    return text
