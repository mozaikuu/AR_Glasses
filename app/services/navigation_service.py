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
        self._authoritative_ids: list[str] = []
        self._destination_index: dict[str, str] = {}
        self._location_meta: dict[str, dict[str, object]] = {}
        self._legacy_aliases = {
            "ta_office": "ta_office_1",
            "ta office": "ta_office_1",
            "ta_office_1": "ta_office_1",
            "cs_department_ta_office": "ta_office_1",
            "math_ta_office": "ta_office_2",
            "ta_office_2": "ta_office_2",
            "entrance": "entrance",
            "main_entrance": "entrance",
            "stairs_g": "stairs_g",
            "elevator": "elevator",
            "lab_a": "lab1",
            "library": "library",
        }
        self._sessions: dict[str, dict[str, object]] = {}
        self._load_navigation_json()
        self._seed_fallback_ids()

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
            loc_id = str(entry.get("id") or "").strip()
            name = str(entry.get("name") or "").strip()
            if not loc_id or not name:
                continue
            if loc_id not in self._authoritative_ids:
                self._authoritative_ids.append(loc_id)
            self._destination_index[self._normalize_key(loc_id)] = loc_id
            self._destination_index[self._normalize_key(name)] = loc_id

            meta = {
                "id": loc_id,
                "name": name,
                "floor": entry.get("floor"),
                "coordinates": entry.get("coordinates") if isinstance(entry.get("coordinates"), dict) else {},
                "description": entry.get("description"),
            }
            self._location_meta[self._normalize_key(loc_id)] = meta
            self._location_meta[self._normalize_key(name)] = meta

    def _seed_fallback_ids(self) -> None:
        if self._authoritative_ids:
            return

        fallback_ids = ["entrance", "ta_office_1", "stairs_g", "elevator", "lab1", "library"]
        self._authoritative_ids.extend(fallback_ids)
        for loc_id in fallback_ids:
            self._destination_index[self._normalize_key(loc_id)] = loc_id

    def list_locations(self) -> list[str]:
        if self._authoritative_ids:
            return self._authoritative_ids
        return self._locations

    def is_authoritative_destination_id(self, destination_id: str) -> bool:
        candidate = destination_id.strip()
        return candidate in self._authoritative_ids

    def resolve_authoritative_destination_id(self, value: str) -> str:
        raw = value.strip()
        if not raw:
            return ""

        normalized = self._normalize_key(raw)
        direct = self._destination_index.get(normalized)
        if direct:
            return direct

        alias_target = self._legacy_aliases.get(normalized)
        if alias_target and self.is_authoritative_destination_id(alias_target):
            return alias_target

        lowered = raw.lower()
        if "math" in lowered and "ta" in lowered and self.is_authoritative_destination_id("ta_office_2"):
            return "ta_office_2"
        if (
            ("cs" in lowered or "computer science" in lowered)
            and "ta" in lowered
            and self.is_authoritative_destination_id("ta_office_1")
        ):
            return "ta_office_1"

        search_key = self._normalize_key(raw)
        for key, destination_id in sorted(self._destination_index.items(), key=lambda kv: len(kv[0]), reverse=True):
            if key and key in search_key:
                return destination_id

        return ""

    def normalize_destination(self, destination: str) -> str:
        resolved = self.resolve_authoritative_destination_id(destination)
        if resolved:
            return resolved
        return self._normalize_key(destination)

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
