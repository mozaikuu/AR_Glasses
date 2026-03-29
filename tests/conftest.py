from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api import gateway


@pytest.fixture(autouse=True)
def isolate_shared_state(monkeypatch: pytest.MonkeyPatch):
    # Reset mutable singletons between tests to keep cases deterministic.
    gateway.navigation_service._sessions.clear()
    gateway.qr_service._active.clear()
    gateway.qr_service._telemetry.clear()

    # Prevent external LLM and TTS side effects during API tests.
    monkeypatch.setattr(
        gateway.assistant_service,
        "compose_answer",
        lambda text, mode: ((text or "").strip() or "Ready."),
    )
    monkeypatch.setattr(gateway, "synthesize_to_wav", lambda text: b"")

    yield

    gateway.navigation_service._sessions.clear()
    gateway.qr_service._active.clear()
    gateway.qr_service._telemetry.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(gateway.app)