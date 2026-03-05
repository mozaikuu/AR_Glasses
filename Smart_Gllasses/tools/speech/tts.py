"""
Text-to-speech using Coqui TTS (open source, cross-platform).
Supports interrupt (wake word stop).
"""

import asyncio
import os
import sys
import subprocess
from pathlib import Path
from config.settings import BASE_DIR, TTS_OUTPUT_DIR, USE_PIPER_TTS

# ===============================
# GLOBAL STOP FLAG (IMPORTANT)
# ===============================
TTS_STOP_FLAG = False

def stop_tts():
    """Call this to immediately stop speaking."""
    global TTS_STOP_FLAG
    TTS_STOP_FLAG = True


# Ensure output directory exists
TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def is_package_installed(package_name: str) -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", package_name],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def ensure_tts_package():
    if not is_package_installed("TTS"):
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "TTS"],
            check=True
        )


async def text_to_speech(text: str) -> None:
    if not text or not text.strip():
        return
    text_to_speech_sync(text)


def text_to_speech_sync(text: str) -> None:
    global TTS_STOP_FLAG
    TTS_STOP_FLAG = False  # reset before speaking

    if not text or not text.strip():
        return

    print(f"🔊 Nova Speaking: {text[:50]}")

    # ===============================
    # TRY COQUI TTS FIRST
    # ===============================
    if USE_PIPER_TTS:
        try:
            ensure_tts_package()
            from TTS.api import TTS

            tts = TTS(
                model_name="tts_models/en/ljspeech/tacotron2-DDC",
                progress_bar=False
            )

            output_path = TTS_OUTPUT_DIR / f"tts_{hash(text)}.wav"
            tts.tts_to_file(text, str(output_path))

            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(str(output_path))
            pygame.mixer.music.play()

            #  INTERRUPT SUPPORT
            while pygame.mixer.music.get_busy():
                if TTS_STOP_FLAG:
                    print(" Nova interrupted!")
                    pygame.mixer.music.stop()
                    break
                pygame.time.Clock().tick(10)

            pygame.mixer.music.stop()
            pygame.mixer.quit()

            try:
                os.remove(output_path)
            except:
                pass

            return

        except Exception as e:
            print(f"TTS failed: {e}")

    # ===============================
    # FALLBACK TO EDGE TTS
    # ===============================
    try:
        import edge_tts
        import uuid

        voice = "en-US-AriaNeural"
        output_file = TTS_OUTPUT_DIR / f"tts_{uuid.uuid4().hex}.mp3"

        asyncio.run(
            edge_tts.Communicate(text=text, voice=voice).save(str(output_file))
        )

        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(str(output_file))
        pygame.mixer.music.play()

        #  INTERRUPT SUPPORT
        while pygame.mixer.music.get_busy():
            if TTS_STOP_FLAG:
                print(" Nova interrupted!")
                pygame.mixer.music.stop()
                break
            pygame.time.Clock().tick(10)

        pygame.mixer.music.stop()
        pygame.mixer.quit()

        try:
            os.remove(output_file)
        except:
            pass

    except Exception as e:
        print("Edge TTS failed:", e)


def cleanup_tts() -> None:
    try:
        import pygame
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.quit()
    except:
        pass


if __name__ == "__main__":
    text_to_speech_sync("Hello, I am Nova.")

Add TTS interrupt support 
