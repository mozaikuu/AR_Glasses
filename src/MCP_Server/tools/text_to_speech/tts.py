import asyncio
import os
import uuid
from edge_tts import Communicate
from mutagen.mp3 import MP3
import pygame

# Voices
ENGLISH_VOICE = "en-US-AriaNeural"
ARABIC_VOICE = "ar-EG-SalmaNeural"


def get_voice_for_text(text: str) -> str:
    """Detect Arabic vs English text."""
    if any('\u0600' <= ch <= '\u06FF' for ch in text):
        return ARABIC_VOICE
    return ENGLISH_VOICE


async def text_to_speech(text: str):
    """Convert TEXT directly to speech and play it."""
    if not text.strip():
        print("⚠️ Empty text")
        return

    voice = get_voice_for_text(text)
    output_file = f"tts_{uuid.uuid4().hex}.mp3"

    # Generate speech
    tts = Communicate(text=text, voice=voice)
    await tts.save(output_file)

    # Read duration (optional, just for info)
    audio = MP3(output_file)
    print(f"🔊 Duration: {audio.info.length:.2f}s")

    # Play audio
    if not pygame.mixer.get_init():
        pygame.mixer.init()

    pygame.mixer.music.load(output_file)
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


# Standalone run
if __name__ == "__main__":
    text_to_speech("aaiz eeh yabaa")
    text_to_speech("What can you see around you?")
