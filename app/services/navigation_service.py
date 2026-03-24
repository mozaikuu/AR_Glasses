from __future__ import annotations

import json
import uuid
from pathlib import Path


class NavigationService:
    def __init__(self) -> None:
        self._locations = [
            "Entrance",
            "TA_Office",
            "Stairs_G",
            "Elevator",
            "Lab_A",
            "Library",
        ]
        self._location_meta: dict[str, dict[str, object]] = {}
        self._legacy_aliases = {
            "ta_office": "TA_Office",
            "ta office": "TA_Office",
            "ta_office_1": "TA_Office",
            "entrance": "Entrance",
            "stairs_g": "Stairs_G",
            "elevator": "Elevator",
            "lab_a": "Lab_A",
            "library": "Library",
        }
        self._sessions: dict[str, dict[str, object]] = {}
        self._load_navigation_json()

    def _normalize_key(self, value: str) -> str:
        return value.strip().lower().replace("-", "_").replace(" ", "_")

    def _load_navigation_json(self) -> None:
        nav_path = Path(__file__).resolve().parents[2] / "navigation.json"
        if not nav_path.exists():
            return

        try:
            data = json.loads(nav_path.read_text(encoding="utf-8"))
        except Exception:
            return

        locations = data.get("locations") if isinstance(data, dict) else None
        if not isinstance(locations, list):
            return

        for entry in locations:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("name") or "").strip()
            if not name:
                continue
            if name not in self._locations:
                self._locations.append(name)

            key = self._normalize_key(name)
            self._location_meta[key] = {
                "name": name,
                "floor": entry.get("floor"),
                "coordinates": entry.get("coordinates") if isinstance(entry.get("coordinates"), dict) else {},
                "description": entry.get("description"),
            }

            loc_id = str(entry.get("id") or "").strip()
            if loc_id:
                self._location_meta[self._normalize_key(loc_id)] = self._location_meta[key]

    def list_locations(self) -> list[str]:
        return self._locations

    def normalize_destination(self, destination: str) -> str:
        lowered_raw = destination.strip().lower()
        if lowered_raw in self._legacy_aliases:
            return self._legacy_aliases[lowered_raw]

        compact = destination.strip().replace(" ", "_")
        for location in self._locations:
            if location.lower() == compact.lower() or location.lower() == destination.strip().lower():
                return location

        key = self._normalize_key(destination)
        if key in self._legacy_aliases:
            return self._legacy_aliases[key]
        meta = self._location_meta.get(key)
        if isinstance(meta, dict):
            resolved_name = meta.get("name")
            if isinstance(resolved_name, str) and resolved_name:
                return resolved_name
        return compact

    def start(self, destination: str, start: str | None = None) -> dict[str, object]:
        normalized = self.normalize_destination(destination)
        meta = self._location_meta.get(self._normalize_key(normalized), {})
        floor = meta.get("floor") if isinstance(meta, dict) else None
        coords = meta.get("coordinates") if isinstance(meta, dict) else {}
        coord_text = ""
        if isinstance(coords, dict) and {"x", "y"}.issubset(coords.keys()):
            coord_text = f" Coordinates: x={coords.get('x')}, y={coords.get('y')}."

        session_id = str(uuid.uuid4())
        steps = [
            f"Start from {start or 'your current position'}.",
            "Go straight for 15 meters.",
            "Turn right at the next corridor.",
            f"You have arrived at {normalized}."
            + (f" Floor: {floor}." if floor is not None else "")
            + coord_text,
        ]
        self._sessions[session_id] = {
            "destination": normalized,
            "step_index": 0,
            "steps": steps,
            "done": False,
        }
        return self._build_status(session_id)

    def next_step(self, session_id: str) -> dict[str, object] | None:
        session = self._sessions.get(session_id)
        if not session:
            return None
        if not session["done"]:
            session["step_index"] = min(session["step_index"] + 1, len(session["steps"]) - 1)
            if session["step_index"] == len(session["steps"]) - 1:
                session["done"] = True
        return self._build_status(session_id)

    def status(self, session_id: str) -> dict[str, object] | None:
        if session_id not in self._sessions:
            return None
        return self._build_status(session_id)

    def cancel(self, session_id: str) -> bool:
        if session_id not in self._sessions:
            return False
        del self._sessions[session_id]
        return True

    def _build_status(self, session_id: str) -> dict[str, object]:
        session = self._sessions[session_id]
        steps = session["steps"]
        step_index = session["step_index"]
        return {
            "session_id": session_id,
            "destination": session["destination"],
            "current_step": int(step_index),
            "total_steps": len(steps),
            "next_instruction": steps[step_index],
            "done": bool(session["done"]),
        }


navigation_service = NavigationService()
