"""Pydantic models for API requests."""
from pydantic import BaseModel
from typing import Optional


class TextRequest(BaseModel):
    """Simple text request."""
    text: str


class MultimodalRequest(BaseModel):
    """Multimodal request supporting text, image, and audio."""
    text: Optional[str] = None
    image: Optional[str] = None  # base64 encoded image
    audio: Optional[str] = None  # base64 encoded audio bytes (as string for JSON)
    audio_dtype: Optional[str] = "float32"  # Audio data type (int16, int32, float32)
    mode: Optional[str] = "thinking"  # "quick" or "thinking"

