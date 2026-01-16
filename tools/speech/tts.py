"""Text-to-speech using edge-tts."""
import asyncio
import os
import uuid
from pathlib import Path
from edge_tts import Communicate
from mutagen.mp3 import MP3
import pygame
from config.settings import TTS_OUTPUT_DIR, TTS_ENGLISH_VOICE, TTS_ARABIC_VOICE

# Ensure output directory exists
TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_voice_for_text(text: str) -> str:
    """Detect Arabic vs English text."""
    if any('\u0600' <= ch <= '\u06FF' for ch in text):
        return TTS_ARABIC_VOICE
    return TTS_ENGLISH_VOICE


async def text_to_speech(text: str):
    """Convert TEXT directly to speech and play it."""
    if not text or not text.strip():
        print("⚠️ TTS received empty text. Skipping.")
        return

    voice = get_voice_for_text(text)
    output_file = TTS_OUTPUT_DIR / f"tts_{uuid.uuid4().hex}.mp3"

    # Generate speech
    tts = Communicate(text=text, voice=voice)
    await tts.save(str(output_file))

    # Read duration (optional, just for info)
    audio = MP3(str(output_file))
    print(f"🔊 Duration: {audio.info.length:.2f}s")

    # Play audio
    if not pygame.mixer.get_init():
        pygame.mixer.init()

    pygame.mixer.music.load(str(output_file))
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)

    pygame.mixer.music.stop()
    pygame.mixer.quit()
    await asyncio.sleep(0.2)

    # Cleanup
    try:
        os.remove(output_file)
    except Exception as e:
        print("Cleanup error:", e)

