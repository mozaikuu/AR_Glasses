from __future__ import annotations

from datetime import datetime as real_datetime

import app.agent.agent_loop as agent_loop
from app.models.requests import ProcessRequest


class FixedDateTime:
    @classmethod
    def now(cls):
        return real_datetime(2026, 3, 28, 15, 4, 0)


def test_decide_idle_when_text_missing() -> None:
    result = agent_loop.decide(ProcessRequest(text="", mode="quick", client="test"))
    assert result["intent"] == "idle"
    assert "Ready." in result["text"]


def test_decide_time_date_for_day_query(monkeypatch) -> None:
    monkeypatch.setattr(agent_loop, "datetime", FixedDateTime)
    result = agent_loop.decide(ProcessRequest(text="what day is it", mode="quick", client="test"))
    assert result["intent"] == "time_date"
    assert result["text"] == "Today is Saturday, March 28, 2026."


def test_decide_time_date_for_time_query(monkeypatch) -> None:
    monkeypatch.setattr(agent_loop, "datetime", FixedDateTime)
    result = agent_loop.decide(ProcessRequest(text="what time is it", mode="quick", client="test"))
    assert result["intent"] == "time_date"
    assert result["text"] == "The current time is 03:04 PM."


def test_decide_navigation_hint_for_navigation_cues() -> None:
    result = agent_loop.decide(ProcessRequest(text="take me to TA office", mode="quick", client="test"))
    assert result["intent"] == "navigation_hint"
    assert "navigation endpoints" in result["text"]


def test_decide_greeting_intent() -> None:
    result = agent_loop.decide(ProcessRequest(text="hello assistant", mode="quick", client="test"))
    assert result["intent"] == "greeting"
    assert result["text"].startswith("Hello.")


def test_decide_help_intent() -> None:
    result = agent_loop.decide(ProcessRequest(text="help", mode="quick", client="test"))
    assert result["intent"] == "help"
    assert "time/date" in result["text"]


def test_decide_unknown_quick_mode_includes_topic() -> None:
    question = "summarize project design now"
    result = agent_loop.decide(ProcessRequest(text=question, mode="quick", client="test"))
    assert result["mode"] == "quick"
    assert "processed your request locally" in result["text"].lower()
    assert "project design" in result["text"].lower()


def test_decide_unknown_thinking_mode() -> None:
    result = agent_loop.decide(ProcessRequest(text="unknown request", mode="thinking", client="test"))
    assert result["mode"] == "thinking"
    assert "Thinking mode is active" in result["text"]
