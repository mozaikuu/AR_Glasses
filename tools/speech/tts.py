"""TTS utilities using Piper (offline)."""
import asyncio
import os
import shutil
import subprocess
from pathlib import Path

from config.settings import (
    TTS_OUTPUT_DIR,
    TTS_PIPER_EXE,
    TTS_PIPER_EN_MODEL,
    TTS_PIPER_AR_MODEL,
)


TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

_pygame = None
_mixer_initialized = False


def _is_arabic(text: str) -> bool:
    return any("\u0600" <= ch <= "\u06FF" for ch in text or "")


def _resolve_piper_executable() -> str | None:
    configured = (TTS_PIPER_EXE or "").strip()
    if configured:
        p = Path(configured)
        if p.exists():
            return str(p)

    auto = shutil.which("piper")
    if auto:
        return auto
    return None


def _resolve_model_path(text: str) -> Path | None:
    ar_path = Path(TTS_PIPER_AR_MODEL) if TTS_PIPER_AR_MODEL else None
    en_path = Path(TTS_PIPER_EN_MODEL) if TTS_PIPER_EN_MODEL else None

    if _is_arabic(text) and ar_path and ar_path.exists():
        return ar_path
    if en_path and en_path.exists():
        return en_path
    if ar_path and ar_path.exists():
        return ar_path
    return None


def _ensure_mixer() -> bool:
    global _pygame, _mixer_initialized
    if _mixer_initialized:
        return True

    try:
        import pygame  # type: ignore

        _pygame = pygame
        _pygame.mixer.init(frequency=22050, size=-16, channels=1)
        _mixer_initialized = True
        return True
    except Exception as e:
        print(f"[TTS] pygame audio unavailable: {e}")
        return False


def _play_file(path: Path) -> None:
    if not _ensure_mixer():
        return

    try:
        _pygame.mixer.music.load(str(path))
        _pygame.mixer.music.play()
        while _pygame.mixer.music.get_busy():
            _pygame.time.Clock().tick(10)
    finally:
        try:
            _pygame.mixer.music.unload()
        except Exception:
            pass


def _synthesize_piper_to_file(text: str, output_wav: Path) -> bool:
    piper_exe = _resolve_piper_executable()
    if not piper_exe:
        print("[TTS] Piper executable not found. Set TTS_PIPER_EXE or install `piper`.")
        return False

    model_path = _resolve_model_path(text)
    if model_path is None:
        print("[TTS] Piper model not found. Set TTS_PIPER_EN_MODEL / TTS_PIPER_AR_MODEL to valid .onnx files.")
        return False

    cmd = [
        piper_exe,
        "--model",
        str(model_path),
        "--output_file",
        str(output_wav),
    ]

    try:
        proc = subprocess.run(
            cmd,
            input=(text.strip() + "\n").encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode != 0:
            err = proc.stderr.decode("utf-8", errors="ignore").strip()
            print(f"[TTS] Piper synthesis failed: {err or f'return code {proc.returncode}'}")
            return False
        return output_wav.exists() and output_wav.stat().st_size > 0
    except Exception as e:
        print(f"[TTS] Piper invocation error: {e}")
        return False


def _synthesize_and_play_piper(text: str) -> None:
    temp_file = TTS_OUTPUT_DIR / f"tts_{os.getpid()}.wav"
    try:
        ok = _synthesize_piper_to_file(text, temp_file)
        if not ok:
            raise RuntimeError("Piper synthesis failed")
        _play_file(temp_file)
    finally:
        try:
            temp_file.unlink(missing_ok=True)
        except Exception:
            pass


async def text_to_speech(text: str) -> None:
    """Convert text to speech and play it asynchronously via Piper."""
    if not text or not text.strip():
        return
    await asyncio.to_thread(_synthesize_and_play_piper, text)


def text_to_speech_sync(text: str) -> None:
    """Synchronous wrapper."""
    if not text or not text.strip():
        return
    asyncio.run(text_to_speech(text))


def cleanup_tts() -> None:
    """Release TTS resources."""
    global _mixer_initialized
    try:
        if _pygame and _mixer_initialized:
            _pygame.mixer.music.stop()
            _pygame.mixer.quit()
    except Exception:
        pass
    _mixer_initialized = False
