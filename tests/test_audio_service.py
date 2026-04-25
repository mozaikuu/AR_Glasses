from __future__ import annotations

from app.services.audio_service import AudioService


def test_list_devices_and_default_selection() -> None:
    service = AudioService()
    devices = service.list_devices()

    assert len(devices) >= 1
    assert any(device["id"] == "default" for device in devices)
    assert service.get_selected_device() == "default"


def test_select_device_updates_selection_when_present() -> None:
    service = AudioService()

    assert service.select_device("usb_01") is True
    assert service.get_selected_device() == "usb_01"


def test_select_device_rejects_unknown_device() -> None:
    service = AudioService()

    assert service.select_device("missing-device") is False
    assert service.get_selected_device() == "default"


def test_wakeword_start_and_stop() -> None:
    service = AudioService()
    service.stop_wakeword()
    assert service.wakeword_status() is False

    service.start_wakeword()
    assert service.wakeword_status() is True
