from __future__ import annotations

from datetime import datetime, timezone


class QrService:
    def __init__(self) -> None:
        self._active: dict[str, dict[str, str]] = {}
        self._telemetry: list[dict[str, object]] = []

    def set_visible(self, qr_id: str, payload: str | None = None) -> None:
        self._active[qr_id] = {
            "qr_id": qr_id,
            "payload": payload or "",
            "visible_at": datetime.now(timezone.utc).isoformat(),
        }

    def set_hidden(self, qr_id: str) -> None:
        self._active.pop(qr_id, None)

    def active(self) -> list[dict[str, str]]:
        return list(self._active.values())

    def add_telemetry(self, qr_id: str, event: str, metadata: dict[str, object]) -> None:
        self._telemetry.append(
            {
                "qr_id": qr_id,
                "event": event,
                "metadata": metadata,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def telemetry_count(self) -> int:
        return len(self._telemetry)


qr_service = QrService()
