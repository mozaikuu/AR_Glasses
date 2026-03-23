"""Application settings and configuration."""
import os
from pathlib import Path
from env import api_key

# Base paths
BASE_DIR = Path(__file__).parent.parent
SRC_DIR = BASE_DIR / "src"

# ================= MODEL CONFIGURATION =================
# API-based model configuration (Cerebras)
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.cerebras.ai/v1")
API_KEY = api_key
# API_KEY = os.getenv("CEREBRAS_API_KEY", "")  # Set your Cerebras API key
MODEL_ID = os.getenv("MODEL_ID", "llama3.3-70b")  # Cerebras model ID

# Legacy local model config (commented out)
# MODEL_ID = os.getenv(
#     "MODEL_ID",
#     "mistralai/mistral-7b-instruct-v0.2"
#     # "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
#     # "meta-llama/Meta-Llama-3.1-8B-Instruct"
# )

DEVICE = os.getenv(
    "DEVICE",
    "cuda" if os.getenv("CUDA_AVAILABLE") == "true" else "cpu"
)

MAX_LOOPS = int(os.getenv("MAX_LOOPS", "8"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))

# ================= API CONFIGURATION =================
# Unified server runs on port 8000 (gateway + web dashboard + API routes)
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
# API_URL is used by internal HTTP clients (Flask/web bridge), so it must be routable.
# Do not default to 0.0.0.0 for outbound requests.
API_URL = os.getenv("API_URL", f"http://127.0.0.1:{API_PORT}")

# ================= MCP SERVER =================
MCP_SERVER_PATH = BASE_DIR / "server" / "server.py"
MCP_TRANSPORT = "stdio"

# ================= TOOLS =================
TOOLS_DIR = BASE_DIR / "tools"

# Vision model configuration - now using Moondream for better scene understanding
# Moondream is a vision-language model that provides detailed descriptions
USE_MOONDREAM = True
VISION_MODEL_PATH = (
    BASE_DIR / "models" / "moondream"
)
MOONDREAM_MODEL_NAME = "vikhyatk/moondream2"
MOONDREAM_REVISION = "2025-01-09"

# ================= AUDIO =================
AUDIO_SAMPLE_RATE = 44100
AUDIO_CHUNK_SIZE = 1024
AUDIO_RECORD_SECONDS = 5

# ================= WAKE WORD =================
# Central configuration for wake words
# Using "Computer" as it is distinct and easy to detect
WAKE_WORDS = ["computer", "hey computer", "ok computer"]
# WAKE_WORDS = ["sandy", "hey sandy", "ok sandy"]
WAKE_WORD_SENSITIVITY = 0.6  # Slightly higher sensitivity for better accuracy

# ================= TTS =================
TTS_OUTPUT_DIR = BASE_DIR / "tools" / "speech" / "output"

# Piper TTS (local, offline)
TTS_PIPER_DIR = BASE_DIR / "models" / "piper"
TTS_PIPER_EXE = os.getenv(
    "TTS_PIPER_EXE",
    str(TTS_PIPER_DIR / ("piper.exe" if os.name == "nt" else "piper")),
)
TTS_PIPER_EN_MODEL = os.getenv(
    "TTS_PIPER_EN_MODEL",
    str(TTS_PIPER_DIR / "en_US-libritts-high.onnx"),
)
# Optional Arabic Piper model path; falls back to English model if not set/found.
TTS_PIPER_AR_MODEL = os.getenv(
    "TTS_PIPER_AR_MODEL",
    "",
)

# ================= LOGGING =================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
