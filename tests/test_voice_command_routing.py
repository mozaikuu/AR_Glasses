from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.api.gateway import app


class VoiceCommandRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_navigation_command_returns_action_and_destination(self) -> None:
        # The command should route to navigation with a normalized destination payload.
        response = self.client.post(
            "/unity/voice-command",
            json={"command": "take me to ta office", "mode": "quick"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["action"], "navigate")
        self.assertEqual(payload["intent"], "navigation_start")
        self.assertEqual(payload["destination"], "TA_Office")

    def test_cancel_command_routes_to_cancel_navigation(self) -> None:
        # Cancel phrases should map to a deterministic cancel action.
        response = self.client.post(
            "/unity/voice-command",
            json={"command": "stop navigation", "mode": "quick"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["action"], "cancel_navigation")
        self.assertEqual(payload["intent"], "navigation_cancel")

    def test_unknown_destination_returns_navigation_unknown(self) -> None:
        # Unknown places should not start navigation and must provide a fallback intent.
        response = self.client.post(
            "/unity/voice-command",
            json={"command": "take me to mars office", "mode": "quick"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["action"], "speak")
        self.assertEqual(payload["intent"], "navigation_unknown_destination")


if __name__ == "__main__":
    unittest.main()
