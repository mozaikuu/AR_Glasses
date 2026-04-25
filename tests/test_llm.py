from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

import app.agent.api_llm as api_llm
import app.agent.llm as llm


class FakeResponse:
    def __init__(self, status: int, json_body: dict | None = None, text_body: str = "") -> None:
        self.status = status
        self._json_body = json_body or {}
        self._text_body = text_body

    async def __aenter__(self) -> "FakeResponse":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def text(self) -> str:
        return self._text_body

    async def json(self) -> dict:
        return self._json_body


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.captured: dict[str, object] = {}

    async def __aenter__(self) -> "FakeSession":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    def post(self, url: str, headers: dict, json: dict, timeout):
        self.captured = {
            "url": url,
            "headers": headers,
            "json": json,
            "timeout": timeout,
        }
        return self.response


def test_llm_complete_uses_cerebras_provider(monkeypatch) -> None:
    monkeypatch.setattr(llm, "settings", SimpleNamespace(model_provider="cerebras"))
    monkeypatch.setattr(llm, "complete_with_cerebras", lambda prompt, mode: "cloud answer")

    assert llm.complete("hello", mode="quick") == "cloud answer"


def test_llm_complete_returns_error_text_on_cerebras_failure(monkeypatch) -> None:
    monkeypatch.setattr(llm, "settings", SimpleNamespace(model_provider="cerebras"))

    def fail(prompt: str, mode: str = "quick") -> str:
        raise RuntimeError("boom")

    monkeypatch.setattr(llm, "complete_with_cerebras", fail)
    result = llm.complete("hello", mode="quick")
    assert "Cerebras request failed" in result
    assert "boom" in result


def test_llm_complete_falls_back_to_local_decide(monkeypatch) -> None:
    monkeypatch.setattr(llm, "settings", SimpleNamespace(model_provider="local"))
    monkeypatch.setattr(llm, "decide", lambda request: {"text": "local answer"})

    assert llm.complete("hello", mode="quick") == "local answer"


def test_complete_with_cerebras_requires_api_key(monkeypatch) -> None:
    monkeypatch.setattr(
        api_llm,
        "settings",
        SimpleNamespace(api_key="", api_base_url="https://api.example.com/v1", model_id="m", max_agent_loops=3),
    )

    with pytest.raises(RuntimeError, match="API key"):
        api_llm.complete_with_cerebras("hello", mode="quick")


def test_complete_with_cerebras_uses_asyncio_run(monkeypatch) -> None:
    monkeypatch.setattr(
        api_llm,
        "settings",
        SimpleNamespace(api_key="k", api_base_url="https://api.example.com/v1", model_id="m", max_agent_loops=3),
    )

    def fake_run(coro):
        try:
            return "async-result"
        finally:
            coro.close()

    monkeypatch.setattr(api_llm.asyncio, "run", fake_run)
    assert api_llm.complete_with_cerebras("hello", mode="quick") == "async-result"


def test_cerebras_api_client_complete_success(monkeypatch) -> None:
    monkeypatch.setattr(api_llm, "settings", SimpleNamespace(max_agent_loops=3))
    response = FakeResponse(
        200,
        json_body={"choices": [{"message": {"content": "Cloud reply"}}]},
    )
    session = FakeSession(response)
    monkeypatch.setattr(api_llm.aiohttp, "ClientSession", lambda: session)

    client = api_llm.CerebrasAPIClient("https://api.example.com/v1", "token", "llama")
    result = asyncio.run(client.complete("hello", mode="thinking"))

    assert result == "Cloud reply"
    assert session.captured["url"] == "https://api.example.com/v1/chat/completions"
    assert session.captured["json"]["model"] == "llama"
    assert session.captured["json"]["temperature"] == 0.6


def test_cerebras_api_client_complete_raises_on_http_error(monkeypatch) -> None:
    monkeypatch.setattr(api_llm, "settings", SimpleNamespace(max_agent_loops=3))
    response = FakeResponse(429, text_body="rate limited")
    session = FakeSession(response)
    monkeypatch.setattr(api_llm.aiohttp, "ClientSession", lambda: session)

    client = api_llm.CerebrasAPIClient("https://api.example.com/v1", "token", "llama")

    with pytest.raises(RuntimeError, match="429"):
        asyncio.run(client.complete("hello", mode="quick"))
