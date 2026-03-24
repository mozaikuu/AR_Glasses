from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.api.gateway import app


class GatewayContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")

    def test_process_text(self) -> None:
        response = self.client.post(
            "/process",
            json={"text": "hello", "mode": "quick", "client": "test-suite"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["text"], "hello")

    def test_navigation_start_next_cancel(self) -> None:
        start_resp = self.client.post("/navigation/start", json={"destination": "TA_Office"})
        self.assertEqual(start_resp.status_code, 200)
        session_id = start_resp.json()["session_id"]

        next_resp = self.client.post("/navigation/next", json={"session_id": session_id})
        self.assertEqual(next_resp.status_code, 200)

        cancel_resp = self.client.post("/navigation/cancel", json={"session_id": session_id})
        self.assertEqual(cancel_resp.status_code, 200)
        self.assertTrue(cancel_resp.json()["cancelled"])


if __name__ == "__main__":
    unittest.main()
