from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api import gateway


@pytest.mark.integration
def test_system_smoke_cross_component_flow(client: TestClient) -> None:
    unity_headers: dict[str, str] = {}
    unity_api_key = gateway.settings.unity_api_key.strip()
    if unity_api_key:
        unity_headers["X-Unity-Api-Key"] = unity_api_key

    health = client.get("/")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    voice = client.post(
        "/unity/voice-command",
        json={"command": "take me to ta office", "mode": "quick"},
        headers=unity_headers,
    )
    assert voice.status_code == 200
    routed = voice.json()
    assert routed["action"] == "navigate"
    assert routed["intent"] == "navigation_start"

    nav_start = client.post(
        "/navigation/start",
        json={"destination": routed["destination"], "start": "Entrance"},
    )
    assert nav_start.status_code == 200
    nav_payload = nav_start.json()
    session_id = nav_payload["session_id"]
    assert nav_payload["destination"] == "TA_Office"
    assert nav_payload["done"] is False

    nav_status = client.get("/navigation/status", params={"session_id": session_id})
    assert nav_status.status_code == 200
    assert nav_status.json()["session_id"] == session_id

    nav_next = client.post("/navigation/next", json={"session_id": session_id})
    assert nav_next.status_code == 200
    assert nav_next.json()["current_step"] == 1

    qr_visible = client.post("/qr/visible", json={"qr_id": "qr-main", "payload": "door"})
    assert qr_visible.status_code == 200
    assert qr_visible.json()["active_count"] == 1

    qr_active = client.get("/qr/active")
    assert qr_active.status_code == 200
    assert len(qr_active.json()["active"]) == 1

    qr_telemetry = client.post(
        "/qr/telemetry",
        json={"qr_id": "qr-main", "event": "seen", "metadata": {"confidence": 0.91}},
    )
    assert qr_telemetry.status_code == 200
    assert qr_telemetry.json()["telemetry_count"] == 1

    debug = client.get("/debug")
    assert debug.status_code == 200
    assert debug.json()["active_qr_markers"] == 1

    process = client.post(
        "/process",
        json={"text": "integration hello", "mode": "quick", "client": "integration"},
    )
    assert process.status_code == 200
    assert process.json()["text"] == "integration hello"

    esp = client.post("/esp/process", json={"text": "status please", "wants_audio": True})
    assert esp.status_code == 200
    esp_payload = esp.json()
    assert esp_payload["text"] == "status please"
    assert esp_payload["response"] == "status please"
    assert esp_payload["tts_url"].startswith("/esp/tts/")

    tts = client.get(esp_payload["tts_url"])
    assert tts.status_code == 200
    assert tts.headers["content-type"].startswith("audio/wav")

    nav_cancel = client.post("/navigation/cancel", json={"session_id": session_id})
    assert nav_cancel.status_code == 200
    assert nav_cancel.json()["cancelled"] is True

    nav_status_missing = client.get("/navigation/status", params={"session_id": session_id})
    assert nav_status_missing.status_code == 404
