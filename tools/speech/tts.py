from __future__ import annotations

import subprocess
import tempfile
import wave
from io import BytesIO
from pathlib import Path

from app.config.settings import settings


def _fallback_wav() -> bytes:
    # Return a short valid WAV clip so ESP clients can still fetch audio.
    sample_rate = 16000
    duration_seconds = 0.25
    frame_count = int(sample_rate * duration_seconds)
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * frame_count)
    return buffer.getvalue()


def synthesize_to_wav(text: str) -> bytes:
    if not text:
        text = "Ready"

    piper_exe = Path(settings.piper_exe).resolve()
    if not piper_exe.exists():
        bundled = Path("Smart_Glasses/models/piper/piper.exe").resolve()
        if bundled.exists():
            piper_exe = bundled
        else:
            return _fallback_wav()

    model_path = Path(settings.piper_model_path).resolve()
    config_path = Path(settings.piper_config_path).resolve()
    if not model_path.exists():
        return _fallback_wav()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = Path(tmp.name)

    cmd = [
        str(piper_exe),
        "--model",
        str(model_path),
        "--output_file",
        str(wav_path),
    ]
    if config_path.exists():
        cmd.extend(["--config", str(config_path)])

    try:
        proc = subprocess.run(
            cmd,
            input=(text.strip() + "\n").encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=25,
        )
        if proc.returncode != 0:
            return _fallback_wav()
        if not wav_path.exists() or wav_path.stat().st_size <= 44:
            return _fallback_wav()
        return wav_path.read_bytes()
    except Exception:
        return _fallback_wav()
    finally:
        try:
            wav_path.unlink(missing_ok=True)
        except Exception:
            pass
