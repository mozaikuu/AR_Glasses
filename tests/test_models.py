from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.requests import (
    NavigationStartRequest,
    ProcessRequest,
    RecordRequest,
    TextRequest,
)
from app.models.responses import ProcessResponse


def test_text_request_requires_non_empty_text() -> None:
    with pytest.raises(ValidationError):
        TextRequest(text="", mode="quick", client="u")


def test_process_request_defaults_and_mode_validation() -> None:
    payload = ProcessRequest(text="hello", client="u")
    assert payload.mode == "quick"

    with pytest.raises(ValidationError):
        ProcessRequest(text="hello", mode="invalid", client="u")


def test_navigation_start_requires_destination() -> None:
    with pytest.raises(ValidationError):
        NavigationStartRequest(destination="")


def test_record_request_enforces_duration_bounds() -> None:
    assert RecordRequest(duration_seconds=2.5).duration_seconds == 2.5

    with pytest.raises(ValidationError):
        RecordRequest(duration_seconds=0.1)

    with pytest.raises(ValidationError):
        RecordRequest(duration_seconds=31)


def test_process_response_requires_core_fields() -> None:
    payload = ProcessResponse(text="ok", mode="quick", client="unit")
    assert payload.tool_calls == []
    assert payload.metadata == {}

    with pytest.raises(ValidationError):
        ProcessResponse(text="ok", mode="quick")
