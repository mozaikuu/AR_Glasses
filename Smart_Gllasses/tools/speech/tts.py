"""Text-to-speech using Coqui TTS (open source, cross-platform)."""
import asyncio
import os
import sys
import subprocess
from pathlib import Path
from config.settings import BASE_DIR, TTS_OUTPUT_DIR, USE_PIPER_TTS

# Ensure output directory exists
TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def is_package_installed(package_name: str) -> bool:
    """Check if a Python package is installed."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", package_name],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def ensure_tts_package():
    """Ensure TTS package is installed."""
    if not is_package_installed("TTS"):
        print("Installing TTS (Coqui)...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "TTS"],
            check=True
        )


async def text_to_speech(text: str) -> None:
    """Convert text to speech and play it asynchronously."""
    if not text or not text.strip():
        print("TTS received empty text. Skipping.")
        return

    text_to_speech_sync(text)


def text_to_speech_sync(text: str) -> None:
    """Synchronous version of text-to-speech."""
    if not text or not text.strip():
        print("TTS received empty text. Skipping.")
        return

    print(f"🔊 TTS: {text[:50]}..." if len(text) > 50 else f"🔊 TTS: {text}")

    # Try Piper first if enabled
    if USE_PIPER_TTS:
        try:
            ensure_tts_package()
            from TTS.api import TTS

            # Use a lightweight English model
            tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False)

            output_path = TTS_OUTPUT_DIR / f"tts_{hash(text)}.wav"
            tts.tts_to_file(text, str(output_path))

            # Play audio using pygame
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(str(output_path))
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            pygame.mixer.music.stop()
            pygame.mixer.quit()

            # Cleanup
            try:
                os.remove(output_path)
            except:
                pass

            return
        except Exception as e:
            print(f"Piper/TTS failed: {e}, trying Edge-TTS...")

    # Fallback to Edge-TTS (works everywhere, needs internet)
    try:
        import edge_tts
        import uuid

        voice = "en-US-AriaNeural" if not any('\u0600' <= ch <= '\u06FF' for ch in text) else "ar-EG-SalmaNeural"
        output_file = TTS_OUTPUT_DIR / f"tts_{uuid.uuid4().hex}.mp3"

        asyncio.run(edge_tts.Communicate(text=text, voice=voice).save(str(output_file)))

        # Play with pygame
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(str(output_file))
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            asyncio.run(asyncio.sleep(0.1))

        pygame.mixer.music.stop()
        pygame.mixer.quit()

        # Cleanup
        try:
            os.remove(output_file)
        except:
            pass

    except Exception as e:
        print(f"Edge-TTS also failed: {e}")
        print("Text:", text)


def cleanup_tts() -> None:
    """Cleanup TTS resources."""
    try:
        import pygame
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.quit()
    except:
        pass


if __name__ == "__main__":
    # Test TTS
    test_text = "Hello, I am Nova, your smart glasses assistant."
    print(f"Testing TTS with: {test_text}")
    text_to_speech_sync(test_text)