"""TTS utilities using Piper (offline)."""
import asyncio
import os
import shutil
import subprocess
from pathlib import Path
from uuid import uuid4

from config.settings import (
    TTS_OUTPUT_DIR,
    TTS_PIPER_EXE,
    TTS_PIPER_EN_MODEL,
    TTS_PIPER_AR_MODEL,
)


TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

_pygame = None
_mixer_initialized = False
_warned_missing_ar_model = False
_tts_lock = asyncio.Lock()
_failed_models: set[str] = set()


def _detect_language(text: str) -> str:
    """
    Detect dominant language in text for TTS voice selection.
    Returns 'ar' or 'en' (default).
    """
    text = text or ""
    arabic_count = 0
    latin_count = 0
    for ch in text:
        if "\u0600" <= ch <= "\u06FF":
            arabic_count += 1
        elif ("A" <= ch <= "Z") or ("a" <= ch <= "z"):
            latin_count += 1

    # If Arabic script dominates, use Arabic voice/model.
    if arabic_count > latin_count and arabic_count > 0:
        return "ar"
    return "en"


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
    global _warned_missing_ar_model
    ar_path = Path(TTS_PIPER_AR_MODEL) if TTS_PIPER_AR_MODEL else None
    en_path = Path(TTS_PIPER_EN_MODEL) if TTS_PIPER_EN_MODEL else None

    detected_lang = _detect_language(text)
    if detected_lang == "ar":
        if ar_path and ar_path.exists():
            return ar_path
        if not _warned_missing_ar_model:
            print("[TTS] Arabic text detected, but TTS_PIPER_AR_MODEL is missing. Falling back to English model.")
            _warned_missing_ar_model = True
    if en_path and en_path.exists():
        return en_path
    if ar_path and ar_path.exists():
        return ar_path
    return None


def _model_candidates(text: str) -> list[Path]:
    """Return preferred model first, then compatible fallbacks."""
    candidates: list[Path] = []
    preferred = _resolve_model_path(text)
    if preferred is not None:
        candidates.append(preferred)

    # Known-safe fallback on this repo's current Piper binary.
    default_fallback = Path(TTS_PIPER_EN_MODEL).parent / "en_US-lessac-medium.onnx"
    if default_fallback.exists() and default_fallback not in candidates:
        candidates.append(default_fallback)

    return candidates


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

    model_paths = _model_candidates(text)
    if not model_paths:
        print("[TTS] Piper model not found. Set TTS_PIPER_EN_MODEL / TTS_PIPER_AR_MODEL to valid .onnx files.")
        return False

    exe_path = Path(piper_exe)
    env = dict(os.environ)
    env["PATH"] = str(exe_path.parent) + os.pathsep + env.get("PATH", "")

    last_error = ""
    for model_path in model_paths:
        model_key = str(model_path.resolve())
        if model_key in _failed_models:
            continue

        cmd = [
            piper_exe,
            "--model",
            str(model_path),
            "--output_file",
            str(output_wav),
        ]
        config_path = model_path.with_suffix(model_path.suffix + ".json")
        if config_path.exists():
            cmd.extend(["--config", str(config_path)])

        try:
            proc = subprocess.run(
                cmd,
                input=(text.strip() + "\n").encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                cwd=str(exe_path.parent),
                env=env,
            )
            if proc.returncode == 0 and output_wav.exists() and output_wav.stat().st_size > 0:
                _failed_models.discard(model_key)
                if model_path.name != Path(TTS_PIPER_EN_MODEL).name:
                    print(f"[TTS] Piper fallback model in use: {model_path.name}")
                return True
            err = proc.stderr.decode("utf-8", errors="ignore").strip()
            last_error = err or f"return code {proc.returncode}"
            print(f"[TTS] Piper synthesis failed with {model_path.name}: {last_error}")
            _failed_models.add(model_key)
        except Exception as e:
            last_error = str(e)
            print(f"[TTS] Piper invocation error with {model_path.name}: {last_error}")
            _failed_models.add(model_key)

    print(f"[TTS] All Piper model attempts failed: {last_error}")
    return False


def _synthesize_and_play_piper(text: str) -> None:
    temp_file = TTS_OUTPUT_DIR / f"tts_{os.getpid()}_{uuid4().hex}.wav"
    try:
        ok = _synthesize_piper_to_file(text, temp_file)
        if not ok:
            return
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
    try:
        async with _tts_lock:
            await asyncio.to_thread(_synthesize_and_play_piper, text)
    except Exception as e:
        print(f"[TTS] text_to_speech failed: {e}")


def text_to_speech_sync(text: str) -> None:
    """Synchronous wrapper."""
    if not text or not text.strip():
        return
    asyncio.run(text_to_speech(text))


def synthesize_to_wav_file(text: str, prefix: str = "esp_tts") -> Path | None:
    """Synthesize text to a WAV file and return the path without local playback."""
    if not text or not text.strip():
        return None

    out = TTS_OUTPUT_DIR / f"{prefix}_{uuid4().hex}.wav"
    ok = _synthesize_piper_to_file(text, out)
    if not ok:
        try:
            out.unlink(missing_ok=True)
        except Exception:
            pass
        return None
    return out


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
