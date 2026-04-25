from __future__ import annotations

from app.services.qr_service import QrService


def test_set_visible_adds_active_qr() -> None:
    service = QrService()
    service.set_visible("qr-1", "door")
    active = service.active()

    assert len(active) == 1
    assert active[0]["qr_id"] == "qr-1"
    assert active[0]["payload"] == "door"
    assert "visible_at" in active[0]


def test_set_hidden_removes_qr_without_error() -> None:
    service = QrService()
    service.set_visible("qr-1", "door")
    service.set_hidden("qr-1")
    service.set_hidden("qr-1")

    assert service.active() == []


def test_add_telemetry_tracks_count() -> None:
    service = QrService()
    service.add_telemetry("qr-1", "seen", {"confidence": 0.8})
    service.add_telemetry("qr-1", "hidden", {"reason": "out_of_view"})

    assert service.telemetry_count() == 2
