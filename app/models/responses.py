from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ProcessResponse(BaseModel):
    text: str
    mode: str
    client: str
    tool_calls: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class NavigationSessionResponse(BaseModel):
    session_id: str
    destination: str
    current_step: int
    total_steps: int
    next_instruction: str
    done: bool
