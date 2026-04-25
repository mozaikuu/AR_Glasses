from __future__ import annotations

from fastapi.testclient import TestClient

from app.api import gateway


def test_health(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_wakeword_scope_forces_streamlit_clients() -> None:
    effective, reason = gateway._resolve_wakeword_always_listen(
        "streamlit-only",
        "streamlit-main",
        {"source": "streamlit_webrtc"},
        requested=True,
    )

    assert effective is True
    assert reason == "streamlit_requested"


def test_wakeword_scope_honors_streamlit_toggle_off() -> None:
    effective, reason = gateway._resolve_wakeword_always_listen(
        "streamlit-only",
        "streamlit-main",
        {"source": "streamlit_webrtc"},
        requested=False,
    )

    assert effective is False
    assert reason == "streamlit_disabled"


def test_wakeword_scope_defers_non_streamlit_clients() -> None:
    effective, reason = gateway._resolve_wakeword_always_listen(
        "streamlit-only",
        "unity_quest",
        {"source": "unity_router"},
        requested=True,
    )

    assert effective is False
    assert reason == "outside_scope_deferred"


def test_process_text(client: TestClient) -> None:
    response = client.post(
        "/process",
        json={"text": "hello", "mode": "quick", "client": "test-suite"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "hello"
    assert body["mode"] == "quick"
    assert body["client"] == "test-suite"


def test_navigation_start_next_cancel(client: TestClient) -> None:
    destination = "TA_Office"
    if not gateway.navigation_service.is_authoritative_destination_id(destination):
        locations = gateway.navigation_service.list_locations()
        assert locations
        first = locations[0]
        destination = str(first.get("id") if isinstance(first, dict) else first)

    start_resp = client.post("/navigation/start", json={"destination": destination})
    assert start_resp.status_code == 200
    session_id = start_resp.json()["session_id"]

    next_resp = client.post("/navigation/next", json={"session_id": session_id})
    assert next_resp.status_code == 200
    assert next_resp.json()["session_id"] == session_id

    cancel_resp = client.post("/navigation/cancel", json={"session_id": session_id})
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["cancelled"] is True


def test_navigation_status_unknown_session(client: TestClient) -> None:
    response = client.get("/navigation/status", params={"session_id": "missing"})
    assert response.status_code == 404


def test_esp_process_basic(client: TestClient) -> None:
    response = client.post("/esp/process", json={"text": "ping", "wants_audio": False})
    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "ping"
    assert body["response"] == "ping"
    assert "tts_url" not in body


def test_qr_visible_hidden_and_telemetry(client: TestClient) -> None:
    visible = client.post("/qr/visible", json={"qr_id": "A1", "payload": "door"})
    assert visible.status_code == 200
    assert visible.json()["active_count"] == 1

    active = client.get("/qr/active")
    assert active.status_code == 200
    assert len(active.json()["active"]) == 1
    assert active.json()["active"][0]["qr_id"] == "A1"

    telemetry = client.post(
        "/qr/telemetry",
        json={"qr_id": "A1", "event": "seen", "metadata": {"confidence": 0.9}},
    )
    assert telemetry.status_code == 200
    assert telemetry.json()["telemetry_count"] == 1

    hidden = client.post("/qr/hidden", json={"qr_id": "A1"})
    assert hidden.status_code == 200
    assert hidden.json()["active_count"] == 0
