from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class TextRequest(BaseModel):
    text: str = Field(..., min_length=1)
    mode: Literal["quick", "thinking"] = "quick"
    client: str = "unknown"


class ProcessRequest(BaseModel):
    text: str | None = None
    image_base64: str | None = None
    audio_base64: str | None = None
    mode: Literal["quick", "thinking"] = "quick"
    client: str = "unknown"
    metadata: dict[str, Any] = Field(default_factory=dict)


class AudioSelectRequest(BaseModel):
    device_id: str


class NavigationStartRequest(BaseModel):
    destination: str = Field(..., min_length=1)
    start: str | None = None


class NavigationNextRequest(BaseModel):
    session_id: str


class NavigationCancelRequest(BaseModel):
    session_id: str


class UnityVoiceCommandRequest(BaseModel):
    command: str = Field(..., min_length=1)
    mode: Literal["quick", "thinking"] = "quick"


class EspProcessRequest(BaseModel):
    text: str = Field(..., min_length=1)
    wants_audio: bool = False


class QrVisibleRequest(BaseModel):
    qr_id: str
    payload: str | None = None


class QrHiddenRequest(BaseModel):
    qr_id: str


class QrTelemetryRequest(BaseModel):
    qr_id: str
    event: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RecordRequest(BaseModel):
    duration_seconds: float = Field(default=2.0, ge=0.2, le=30.0)
