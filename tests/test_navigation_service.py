from __future__ import annotations

from app.services.navigation_service import NavigationService


def test_normalize_destination_supports_legacy_alias() -> None:
    service = NavigationService()
    assert service.normalize_destination("ta office") == "TA_Office"


def test_normalize_destination_resolves_json_location_id() -> None:
    service = NavigationService()
    assert service.normalize_destination("lecture_hall_a") == "Lecture Hall A"


def test_normalize_destination_returns_compact_unknown_value() -> None:
    service = NavigationService()
    assert service.normalize_destination("Dean Office") == "Dean_Office"


def test_start_creates_session_with_initial_step() -> None:
    service = NavigationService()
    status = service.start(destination="Library", start="Entrance")
    assert status["current_step"] == 0
    assert status["done"] is False
    assert status["destination"] == "Library"
    assert "Start from Entrance" in status["next_instruction"]


def test_next_step_marks_done_on_last_instruction() -> None:
    service = NavigationService()
    status = service.start(destination="Library")
    session_id = str(status["session_id"])

    for _ in range(3):
        status = service.next_step(session_id)

    assert status is not None
    assert status["current_step"] == 3
    assert status["done"] is True
    assert "You have arrived at Library." in status["next_instruction"]
    assert "Floor: 2." in status["next_instruction"]
    assert "Coordinates: x=20, y=10." in status["next_instruction"]


def test_status_and_cancel_for_unknown_session() -> None:
    service = NavigationService()
    assert service.status("missing") is None
    assert service.cancel("missing") is False


def test_cancel_existing_session() -> None:
    service = NavigationService()
    status = service.start(destination="TA_Office")
    session_id = str(status["session_id"])

    assert service.cancel(session_id) is True
    assert service.status(session_id) is None


def test_list_locations_includes_default_seed_locations() -> None:
    service = NavigationService()
    locations = service.list_locations()
    assert "Entrance" in locations
    assert "Library" in locations
