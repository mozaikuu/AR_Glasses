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

# DEVICE = os.getenv(
#     "DEVICE",
#     "cuda" if os.getenv("CUDA_AVAILABLE") == "true" else "cpu"
# )

MAX_LOOPS = int(os.getenv("MAX_LOOPS", "8"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))

# ================= API CONFIGURATION =================
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_URL = f"http://{API_HOST}:{API_PORT}"

# ================= MCP SERVER =================
MCP_SERVER_PATH = BASE_DIR / "server" / "server.py"
MCP_TRANSPORT = "stdio"

# ================= TOOLS =================
TOOLS_DIR = BASE_DIR / "tools"
VISION_MODEL_PATH = (
    SRC_DIR / "mcp_server" / "tools" / "computer_vision" / "yolo11n.pt"
)

# ================= AUDIO =================
AUDIO_SAMPLE_RATE = 44100
AUDIO_CHUNK_SIZE = 1024
AUDIO_RECORD_SECONDS = 5

# ================= TTS =================
TTS_OUTPUT_DIR = BASE_DIR / "tools" / "speech" / "output"
TTS_ENGLISH_VOICE = "en-US-AriaNeural"
TTS_ARABIC_VOICE = "ar-EG-SalmaNeural"

# ================= LOGGING =================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
