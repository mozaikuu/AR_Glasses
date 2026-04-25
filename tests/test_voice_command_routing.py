from __future__ import annotations

from fastapi.testclient import TestClient


def test_navigation_command_returns_action_and_destination(client: TestClient) -> None:
    # The command should route to navigation with a normalized destination payload.
    response = client.post(
        "/unity/voice-command",
        json={"command": "take me to ta office", "mode": "quick"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["action"] == "navigate"
    assert payload["intent"] == "navigation_start"
    assert payload["destination"] == "TA_Office"


def test_cancel_command_routes_to_cancel_navigation(client: TestClient) -> None:
    # Cancel phrases should map to a deterministic cancel action.
    response = client.post(
        "/unity/voice-command",
        json={"command": "stop navigation", "mode": "quick"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["action"] == "cancel_navigation"
    assert payload["intent"] == "navigation_cancel"


def test_unknown_destination_returns_navigation_unknown(client: TestClient) -> None:
    # Unknown places should not start navigation and must provide a fallback intent.
    response = client.post(
        "/unity/voice-command",
        json={"command": "take me to mars office", "mode": "quick"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["action"] == "speak"
    assert payload["intent"] == "navigation_unknown_destination"
