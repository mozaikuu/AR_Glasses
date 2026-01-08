"""Application settings and configuration."""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
SRC_DIR = BASE_DIR / "src"

# Model Configuration
# MODEL_ID = os.getenv("MODEL_ID", "google/gemma-3-4b-it")
MODEL_ID = os.getenv("MODEL_ID", "mistralai/mistral-7b-instruct-v0.2")
DEVICE = os.getenv("DEVICE", "cuda" if os.getenv("CUDA_AVAILABLE") == "true" else "cpu")
MAX_LOOPS = int(os.getenv("MAX_LOOPS", "8"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))

# API Configuration
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_URL = f"http://{API_HOST}:{API_PORT}"

# MCP Server Configuration
MCP_SERVER_PATH = BASE_DIR / "server" / "server.py"
MCP_TRANSPORT = "stdio"

# Tool Paths
TOOLS_DIR = BASE_DIR / "tools"
VISION_MODEL_PATH = SRC_DIR / "mcp_server" / "tools" / "computer_vision" / "yolo11n.pt"

# Audio Configuration
AUDIO_SAMPLE_RATE = 44100
AUDIO_CHUNK_SIZE = 1024
AUDIO_RECORD_SECONDS = 5

# TTS Configuration
TTS_OUTPUT_DIR = BASE_DIR / "tools" / "speech" / "output"
TTS_ENGLISH_VOICE = "en-US-AriaNeural"
TTS_ARABIC_VOICE = "ar-EG-SalmaNeural"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

