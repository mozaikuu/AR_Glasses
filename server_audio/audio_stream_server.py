#!/usr/bin/env python3
"""
WebSocket Audio Streaming Server for Smart Glasses Gateway.

Handles:
- PCM audio streaming from mobile apps (Android/iOS)
- Speech-to-text using Whisper
- Text-to-speech using Piper/ElevenLabs
- Response routing back to mobile device and BLE glasses

Author: Smart Glasses Project
"""

import asyncio
import json
import logging
import sys
import os
import base64
import struct
from pathlib import Path
from typing import Dict, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime

import websockets
from websockets.server import WebSocketServerProtocol
import numpy as np

try:
    import httpx
except ImportError:
    httpx = None

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import only existing settings from config
from config.settings import (
    API_BASE_URL
)

# WebSocket server configuration (not in config/settings.py)
WS_HOST = "0.0.0.0"
WS_PORT = 8765
WS_SSL = False

# STT/TTS configuration
STT_MODEL = "base"
TTS_ENGINE = "edge"  # edge-tts or piper
BLE_ENABLED = True

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Audio configuration
SAMPLE_RATE = 16000
CHANNELS = 1
BYTES_PER_SAMPLE = 2
AUDIO_FORMAT = np.int16


@dataclass
class ClientSession:
    """Represents a connected client (mobile app)."""
    websocket: WebSocketServerProtocol
    device_id: str = ""
    device_type: str = ""
    connected_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    audio_buffer: bytes = b""

    def update_activity(self):
        self.last_activity = datetime.now()


class AudioStreamServer:
    """
    WebSocket server for audio streaming from mobile gateway apps.

    Architecture:
    ┌─────────────┐     ┌─────────────────────┐     ┌─────────────┐
    │ Mobile App  │────▶│  WebSocket Server   │────▶│  STT/TTS    │
    │ (Audio In)  │     │  (audio_stream)      │     │  Pipeline   │
    └─────────────┘     └─────────────────────┘     └─────────────┘
                              │     │
                              ▼     ▼
                        ┌──────────────┐
                        │ BLE/Glasses  │
                        │ (Response)  │
                        └──────────────┘
    """

    def __init__(self, host: str = WS_HOST, port: int = WS_PORT):
        self.host = host
        self.port = port
        self.clients: Dict[str, ClientSession] = {}
        self.stt_model = None
        self.tts_engine = None

    async def start(self):
        """Start the WebSocket server."""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")

        # Load STT model
        await self.load_stt_model()

        # Load TTS engine
        await self.load_tts_engine()

        # Start WebSocket server
        async with websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10
        ):
            logger.info(f"WebSocket server running at ws://{self.host}:{self.port}")
            logger.info("Press Ctrl+C to stop")

            # Keep running
            await asyncio.Future()

    async def load_stt_model(self):
        """Load speech-to-text model."""
        try:
            # Try loading Whisper
            import whisper
            logger.info(f"Loading Whisper model: {STT_MODEL}")
            self.stt_model = whisper.load_model(STT_MODEL)
            logger.info("STT model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load Whisper: {e}")
            self.stt_model = None

    async def load_tts_engine(self):
        """Load text-to-speech engine."""
        try:
            # Try loading Piper
            from piper import PiperVoice
            logger.info("Loading Piper TTS...")
            # Piper will be loaded lazily when needed
            self.tts_engine = "piper"
            logger.info("TTS engine ready")
        except Exception as e:
            logger.warning(f"Piper not available: {e}")
            self.tts_engine = None

    async def handle_client(self, websocket: WebSocketServerProtocol):
        """Handle a new client connection."""
        # Create session
        client_id = str(id(websocket))
        session = ClientSession(websocket=websocket)
        self.clients[client_id] = session

        logger.info(f"Client connected: {client_id}")

        try:
            async for message in websocket:
                await self.handle_message(session, message)
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"Client disconnected: {client_id} - {e}")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]

    async def handle_message(self, session: ClientSession, message):
        """Handle incoming message from client."""
        session.update_activity()

        # Check if message is binary (audio) or text
        if isinstance(message, bytes):
            await self.process_audio(session, message)
        else:
            await self.process_text(session, message)

    async def process_audio(self, session: ClientSession, audio_data: bytes):
        """
        Process incoming PCM audio data.

        Args:
            session: Client session
            audio_data: Raw PCM audio bytes (16kHz, mono, 16-bit)
        """
        # Accumulate audio buffer
        session.audio_buffer += audio_data

        # Process when we have enough audio (~1 second)
        if len(session.audio_buffer) >= SAMPLE_RATE * BYTES_PER_SAMPLE:
            audio_to_process = session.audio_buffer
            session.audio_buffer = b""  # Clear buffer

            # Transcribe
            text = await self.transcribe(audio_to_process)

            if text.strip():
                logger.info(f"Transcribed: {text}")

                # Process with LLM and generate response
                response = await self.process_command(text)

                # Send response back
                await self.send_response(session, response)

    async def transcribe(self, audio_data: bytes) -> str:
        """
        Transcribe audio to text using Whisper.

        Args:
            audio_data: Raw PCM audio bytes

        Returns:
            Transcribed text
        """
        if self.stt_model is None:
            # Fallback to simple silence detection
            return self.simple_vad(audio_data)

        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

            # Transcribe
            result = self.stt_model.transcribe(audio_array, language="en")
            text = result["text"].strip()

            return text
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""

    async def transcribe_with_api(self, audio_data: bytes) -> str:
        """
        Transcribe using external API (OpenAI Whisper).

        Falls back when local model is not available.
        """
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/v2/voice/transcribe",
                    files={"audio": ("audio.wav", audio_data, "audio/wav")},
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("transcribed", "")
                else:
                    logger.error(f"API transcription failed: {response.status_code}")
                    return ""
        except Exception as e:
            logger.error(f"API transcription error: {e}")
            return ""

    async def process_command(self, text: str) -> dict:
        """
        Process transcribed text with LLM and generate response.

        Args:
            text: Transcribed user command

        Returns:
            Response dictionary with text and audio
        """
        try:
            # Import agent for command processing
            from agent.llm import generate_chat

            messages = [
                {"role": "system", "content": "You are Nova, a voice assistant for smart glasses. Keep responses concise (under 50 words) for audio playback."},
                {"role": "user", "content": text}
            ]

            response_text = await generate_chat(messages)

            # Generate TTS audio on SERVER
            audio_bytes = await self.generate_tts(response_text)
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8') if audio_bytes else ""

            return {
                "type": "response",
                "text": response_text,
                "audio": audio_base64
            }
        except Exception as e:
            logger.error(f"Command processing error: {e}")
            return {
                "type": "error",
                "text": "I couldn't process that. Please try again."
            }

    async def text_to_speech(self, text: str) -> str:
        """
        Convert text to speech.

        Args:
            text: Text to convert

        Returns:
            Base64-encoded audio
        """
        try:
            if self.tts_engine == "piper":
                return await self.tts_piper(text)
            else:
                # Use API fallback
                return await self.tts_api(text)
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return ""

    async def tts_piper(self, text: str) -> str:
        """Piper TTS backend."""
        try:
            from piper import PiperVoice

            # This would use a local Piper model
            # For prototype, we return empty
            logger.debug("Piper TTS called (prototype)")
            return ""
        except Exception as e:
            logger.error(f"Piper TTS error: {e}")
            return ""

    async def tts_api(self, text: str) -> str:
        """External TTS API (ElevenLabs, etc.)."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/v2/voice/synthesize",
                    json={"text": text},
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("audio", "")
                else:
                    return ""
        except Exception as e:
            logger.error(f"TTS API error: {e}")
            return ""

    async def process_text(self, session: ClientSession, message: str):
        """
        Handle text messages from client (commands, configuration).

        Expected formats:
        - {"type": "config", "server_url": "..."}
        - {"type": "status"} -> sends status response
        """
        try:
            data = json.loads(message)

            if data.get("type") == "config":
                # Update client configuration
                session.device_id = data.get("device_id", "")
                session.device_type = data.get("device_type", "")
                logger.info(f"Client {session.device_id} configured as {session.device_type}")

            elif data.get("type") == "status":
                # Send status
                status = {
                    "type": "status",
                    "connected_clients": len(self.clients),
                    "server_time": datetime.now().isoformat()
                }
                await session.websocket.send(json.dumps(status))

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from client: {message[:100]}")

    async def send_response(self, session: ClientSession, response: dict):
        """
        Send response to client.

        Args:
            session: Target client session
            response: Response dictionary
        """
        try:
            # Send as JSON first
            await session.websocket.send(json.dumps(response))

            # If audio is included, also send binary
            if response.get("audio"):
                audio_bytes = base64.b64decode(response["audio"])
                await session.websocket.send(audio_bytes)

        except Exception as e:
            logger.error(f"Failed to send response: {e}")

    async def generate_tts(self, text: str) -> bytes:
        """
        Generate TTS audio on server.

        Args:
            text: Text to convert to speech

        Returns:
            Audio bytes (WAV format)
        """
        try:
            # Use Edge-TTS or Piper to generate audio
            import edge_tts
            import io

            voice = "en-US-AriaNeural"
            communicate = edge_tts.Communicate(text, voice)

            # Generate to memory
            audio_buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])

            return audio_buffer.getvalue()

        except Exception as e:
            logger.error(f"TTS generation error: {e}")
            return b""

    async def broadcast_to_glasses(self, data: dict):
        """
        Broadcast data to connected BLE glasses.

        This would integrate with the glasses BLE API.
        """
        # This would send data to glasses via BLE bridge
        logger.info(f"Broadcasting to glasses: {data}")

    def simple_vad(self, audio_data: bytes) -> str:
        """
        Simple Voice Activity Detection.

        Returns empty string if audio is mostly silence.
        """
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            energy = np.abs(audio_array).mean()

            # Threshold for speech (adjust based on testing)
            if energy < 500:
                return ""  # Silence

            return "[Speech detected - API needed for transcription]"
        except Exception:
            return ""

    def get_status(self) -> dict:
        """Get server status."""
        return {
            "connected_clients": len(self.clients),
            "clients": [
                {
                    "id": id,
                    "device_type": session.device_type,
                    "connected_at": session.connected_at.isoformat()
                }
                for id, session in self.clients.items()
            ]
        }


async def main():
    """Main entry point."""
    server = AudioStreamServer()

    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")


if __name__ == "__main__":
    asyncio.run(main())
