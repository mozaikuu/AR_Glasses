from __future__ import annotations

import pytest

from app.models.requests import ProcessRequest, TextRequest
from app.services.assistant_service import AssistantService


@pytest.fixture
def service() -> AssistantService:
    return AssistantService()


def test_check_wakeword_extracts_command(service: AssistantService) -> None:
    matched, cleaned = service._check_wakeword("Hey computer, open library map")
    assert matched is True
    assert cleaned == "open library map"


def test_check_wakeword_returns_original_text_when_not_matched(service: AssistantService) -> None:
    matched, cleaned = service._check_wakeword("show me the next class")
    assert matched is False
    assert cleaned == "show me the next class"


def test_append_wake_context_keeps_rolling_tail(service: AssistantService) -> None:
    merged = service._append_wake_context("client-1", "a" * 300)
    assert len(merged) <= service._wake_context_chars
    assert service._wake_context_by_client["client-1"] == merged


def test_check_wakeword_matches_spacing_and_punctuation_variants(service: AssistantService) -> None:
    matched, cleaned = service._check_wakeword("hey---computer: open the lab")
    assert matched is True
    assert cleaned == "open the lab"


def test_postprocess_answer_strips_preambles_and_caps_sentences(service: AssistantService) -> None:
    raw = (
        "To help you quickly,\n"
        "First, I will think.\n"
        "Sentence one. Sentence two. Sentence three. Sentence four."
    )
    result = service._postprocess_answer(raw)
    assert result == "Sentence one. Sentence two. Sentence three."


def test_vision_intent_detection(service: AssistantService) -> None:
    assert service._vision_intent("Describe what you see") is True
    assert service._vision_intent("Tell me a joke") is False


def test_process_always_listen_without_wakeword(monkeypatch, service: AssistantService) -> None:
    monkeypatch.setattr(
        "app.services.assistant_service.transcribe_audio_detailed",
        lambda *_args, **_kwargs: ("random phrase", {"provider": "stub"}),
    )

    result = service.process(
        ProcessRequest(
            audio_base64="abc",
            metadata={"always_listen": True},
            client="esp",
            mode="quick",
        )
    )

    assert result["text"] == "Listening... say 'Computer' to trigger."
    assert result["metadata"]["ignored_audio"] is True
    assert result["metadata"]["wakeword_triggered"] is False


def test_process_always_listen_wakeword_without_command(monkeypatch, service: AssistantService) -> None:
    monkeypatch.setattr(
        "app.services.assistant_service.transcribe_audio_detailed",
        lambda *_args, **_kwargs: ("computer", {"provider": "stub"}),
    )

    result = service.process(
        ProcessRequest(
            audio_base64="abc",
            metadata={"always_listen": True},
            client="esp",
            mode="quick",
        )
    )

    assert result["text"] == "Wake word detected. Listening for your command."
    assert result["metadata"]["wakeword_triggered"] is True
    assert result["metadata"]["ignored_audio"] is True


def test_process_prefers_image_vision_result(monkeypatch, service: AssistantService) -> None:
    monkeypatch.setattr(service, "_run_mcp_vision_from_image", lambda image, prompt: "Detected a laptop on a desk.")

    result = service.process(
        ProcessRequest(
            text="what do you see",
            image_base64="base64-image",
            client="vision-test",
            mode="quick",
        )
    )

    assert result["text"] == "Detected a laptop on a desk."
    assert result["tool_calls"] == ["vision.analyze_image_moondream"]


def test_process_vision_intent_uses_camera_path(monkeypatch, service: AssistantService) -> None:
    monkeypatch.setattr(service, "_run_mcp_vision_from_camera", lambda prompt: "There is a corridor ahead.")

    result = service.process(
        ProcessRequest(
            text="describe what you see",
            client="vision-test",
            mode="quick",
        )
    )

    assert result["text"] == "There is a corridor ahead."
    assert result["tool_calls"] == ["vision.capture_moondream"]


def test_process_falls_back_to_compose_answer(monkeypatch, service: AssistantService) -> None:
    monkeypatch.setattr(service, "compose_answer", lambda text, mode: "fallback answer")

    result = service.process(ProcessRequest(text="hello", client="unit", mode="quick"))

    assert result["text"] == "fallback answer"
    assert result["tool_calls"] == []
    assert result["metadata"]["inputs"] == ["text"]


def test_run_text_uses_compose_answer(monkeypatch, service: AssistantService) -> None:
    monkeypatch.setattr(service, "compose_answer", lambda text, mode: "short answer")

    result = service.run_text(TextRequest(text="hello", mode="quick", client="unit"))
    assert result["text"] == "short answer"
    assert result["metadata"]["inputs"] == ["text"]


def test_route_unity_command_navigation_and_unknown(service: AssistantService) -> None:
    start = service.route_unity_command("take me to ta office")
    unknown = service.route_unity_command("take me to mars office")

    assert start["action"] == "navigate"
    assert "ta_office" in str(start["destination"]).lower()
    assert isinstance(unknown.get("intent"), str)
    assert isinstance(unknown.get("action"), str)


def test_compose_answer_short_circuits_time_queries(monkeypatch, service: AssistantService) -> None:
    def fail_complete(prompt: str, mode: str = "quick") -> str:
        raise AssertionError("complete() should not run for local time/day questions")

    monkeypatch.setattr("app.services.assistant_service.complete", fail_complete)
    answer = service.compose_answer("what day is it", mode="quick")
    assert answer.startswith("Today is")


def test_compose_answer_adds_runtime_context_and_postprocesses(monkeypatch, service: AssistantService) -> None:
    observed: dict[str, str] = {}

    def fake_complete(prompt: str, mode: str = "quick") -> str:
        observed["prompt"] = prompt
        observed["mode"] = mode
        return "Sentence one. Sentence two. Sentence three. Sentence four."

    monkeypatch.setattr("app.services.assistant_service.complete", fake_complete)
    answer = service.compose_answer("summarize this", mode="quick")

    assert answer == "Sentence one. Sentence two. Sentence three."
    assert observed["mode"] == "quick"
    assert "Runtime context for this request:" in observed["prompt"]
    assert "User request: summarize this" in observed["prompt"]
