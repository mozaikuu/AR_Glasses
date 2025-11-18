import asyncio
import os
import time
from edge_tts import Communicate

BEST_FEMALE_VOICE = "en-US-AriaNeural"

async def text_to_speech(input_file):
    if not os.path.isfile(input_file):
        print("File not found:", input_file)
        return
    
    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()

    output_file = os.path.splitext(input_file)[0] + ".mp3"

    tts = Communicate(text, BEST_FEMALE_VOICE)

    print(f"Generating speech for: {input_file}")
    await tts.save(output_file)
    print(f"Playing audio: {output_file}")

    # Play audio (Windows)
    os.system(f'start "" "{output_file}"')

    file_duration = len(text.split()) / 2  # Approximate duration in seconds
    
    # Give the system time to release file lock
    time.sleep(file_duration)

    # Delete file
    os.remove(output_file)
    print(f"Deleted: {output_file}")


if __name__ == "__main__":
    file_path = input("Enter text file path: ").strip()
    asyncio.run(text_to_speech(file_path))
