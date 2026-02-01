"""Text-to-speech using Piper TTS (offline, open source)."""
import asyncio
import os
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import pygame
from config.settings import (
    BASE_DIR,
    TTS_OUTPUT_DIR,
    PIPER_ENGLISH_VOICE,
    PIPER_ARABIC_VOICE,
)

# Ensure output directory exists
TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Thread pool for synchronous Piper synthesis
_executor = ThreadPoolExecutor(max_workers=2)

# Track mixer initialization state
_mixer_initialized = False


def _get_voice_for_text(text: str) -> Path:
    """Get the appropriate Piper voice model for the text language."""
    # Check for Arabic characters
    is_arabic = any('\u0600' <= ch <= '\u06FF' for ch in text)

    voice_path = Path(PIPER_ARABIC_VOICE if is_arabic else PIPER_ENGLISH_VOICE)

    if not voice_path.exists():
        # Fall back to English if Arabic not available
        if is_arabic:
            voice_path = Path(PIPER_ENGLISH_VOICE)
        # Fall back to a default if needed
        if not voice_path.exists():
            raise FileNotFoundError(
                f"Piper voice not found at {voice_path}. "
                "Please download Piper voices using scripts/download_piper_models.py"
            )

    return voice_path


def _synthesize_and_play(text: str) -> None:
    """Synchronous wrapper for Piper TTS synthesis and playback."""
    import piper

    voice_path = _get_voice_for_text(text)
    voice = piper.PiperVoice.load(str(voice_path))

    # Generate audio to temp file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_file = f.name

    try:
        # Synthesize speech
        with voice.synthesize_async(text) as synth:
            synth.forward(temp_file)

        # Initialize pygame mixer once and keep it
        global _mixer_initialized
        if not _mixer_initialized:
            pygame.mixer.init(frequency=44100, size=-16, channels=2)
            _mixer_initialized = True

        # Play audio
        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()

        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

    finally:
        # Cleanup
        try:
            pygame.mixer.music.unload()
        except:
            pass
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except:
            pass


async def text_to_speech(text: str) -> None:
    """Convert text to speech and play it asynchronously."""
    if not text or not text.strip():
        print("TTS received empty text. Skipping.")
        return

    print(f"🔊 TTS: {text[:50]}..." if len(text) > 50 else f"🔊 TTS: {text}")

    # Run synthesis in thread pool to not block event loop
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_executor, _synthesize_and_play, text)


def text_to_speech_sync(text: str) -> None:
    """Synchronous version of text_to_speech for non-async callers."""
    if not text or not text.strip():
        print("TTS received empty text. Skipping.")
        return

    _synthesize_and_play(text)


def cleanup_tts() -> None:
    """Cleanup TTS resources."""
    global _mixer_initialized
    try:
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        _mixer_initialized = False
    except:
        pass
    _executor.shutdown(wait=False)