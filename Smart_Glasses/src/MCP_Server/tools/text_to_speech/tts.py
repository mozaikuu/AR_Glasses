"""MCP text-to-speech wrapper that reuses project Piper TTS."""
import asyncio
import sys
from pathlib import Path


project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tools.speech.tts import text_to_speech as _project_tts


async def text_to_speech(text: str):
    await _project_tts(text)


if __name__ == "__main__":
    asyncio.run(text_to_speech("Piper TTS test"))
