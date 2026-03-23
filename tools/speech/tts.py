from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from app.config.settings import settings


def synthesize_to_wav(text: str) -> bytes:
    if not text:
        text = "Ready"

    piper_exe = Path(settings.piper_exe).resolve()
    if not piper_exe.exists():
        bundled = Path("Smart_Glasses/models/piper/piper.exe").resolve()
        if bundled.exists():
            piper_exe = bundled
        else:
            return b"RIFF....WAVEfmt "

    model_path = Path(settings.piper_model_path).resolve()
    config_path = Path(settings.piper_config_path).resolve()
    if not model_path.exists():
        return b"RIFF....WAVEfmt "

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
            return b"RIFF....WAVEfmt "
        if not wav_path.exists() or wav_path.stat().st_size <= 44:
            return b"RIFF....WAVEfmt "
        return wav_path.read_bytes()
    except Exception:
        return b"RIFF....WAVEfmt "
    finally:
        try:
            wav_path.unlink(missing_ok=True)
        except Exception:
            pass
