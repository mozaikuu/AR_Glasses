import asyncio
import os
from edge_tts import Communicate
from mutagen.mp3 import MP3
import pygame

# Define the voices for each language
ENGLISH_VOICE = "en-US-AriaNeural"
ARABIC_VOICE = "ar-EG-SalmaNeural" # A common female Arabic voice (Egyptian)

def get_voice_for_text(text):
    """
    Checks if the text contains Arabic characters and selects the appropriate voice.
    """
    # A simple way to check for Arabic characters (U+0600 to U+06FF range)
    if any('\u0600' <= char <= '\u06FF' for char in text):
        print("💡 Detected Arabic text, using Arabic voice.")
        return ARABIC_VOICE
    else:
        print("💡 Detected non-Arabic text, using English voice.")
        return ENGLISH_VOICE

async def text_to_speech(input_file):
    if not os.path.isfile(input_file):
        print("File not found:", input_file)
        return
    
    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()

    # --- THE KEY CHANGE IS HERE ---
    selected_voice = get_voice_for_text(text) 
    
    output_file = os.path.splitext(input_file)[0] + ".mp3"

    # Use the dynamically selected voice
    tts = Communicate(text, selected_voice) 

    print(f"Generating speech for: {input_file} using {selected_voice}")
    await tts.save(output_file)
    print(f"Playing audio: {output_file}")

    # ... (Rest of your original playback and cleanup code remains the same) ...

    # Get actual audio duration
    audio = MP3(output_file)
    file_duration = audio.info.length
    seconds_padding = 0 
    print(f"Audio duration: {file_duration:.2f} seconds")
    print(f"Adding {seconds_padding} seconds Padding")
    
    # Initialize pygame mixer
    pygame.mixer.init()
    
    # Play audio in background
    pygame.mixer.music.load(output_file)
    pygame.mixer.music.play()

    # Wait for audio to finish playing
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)

    # cleanup
    pygame.mixer.quit()
    print("Audio playback finished.")
    # Delete file
    try:
        os.remove(output_file)
        print(f"Deleted: {output_file}")
    except PermissionError:
        print(f"Could not delete {output_file} - file may still be in use... trying again in 3 seconds")
        await asyncio.sleep(3)
        try:
            os.remove(output_file)
            print(f"Deleted: {output_file}")
        except Exception as e:
            print(f"Failed to delete {output_file}: {e}")

if __name__ == "__main__":
    file_path = input("Enter text file path: ").strip()
    asyncio.run(text_to_speech(file_path))