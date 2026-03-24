from __future__ import annotations

from app.config.settings import settings


class AudioService:
    def __init__(self) -> None:
        self._devices = [
            {"id": "default", "name": "System Default Mic", "is_default": True},
            {"id": "usb_01", "name": "USB Microphone", "is_default": False},
            {"id": "bt_quest", "name": "Quest Bluetooth Mic", "is_default": False},
        ]
        self._selected_device_id = "default"
        self._wakeword_running = settings.auto_start_wakeword

    def list_devices(self) -> list[dict[str, object]]:
        return self._devices

    def select_device(self, device_id: str) -> bool:
        exists = any(device["id"] == device_id for device in self._devices)
        if not exists:
            return False
        self._selected_device_id = device_id
        return True

    def get_selected_device(self) -> str:
        return self._selected_device_id

    def start_wakeword(self) -> None:
        self._wakeword_running = True

    def stop_wakeword(self) -> None:
        self._wakeword_running = False

    def wakeword_status(self) -> bool:
        return self._wakeword_running


audio_service = AudioService()
