from __future__ import annotations

from datetime import datetime

from app.models.requests import ProcessRequest


def decide(request: ProcessRequest) -> dict[str, object]:
    """Bounded local decision loop used when cloud LLM/tooling is unavailable."""
    mode = request.mode
    text = (request.text or "").strip()
    lowered = text.lower()

    if not text:
        response = "Ready. Ask me about time, navigation, or campus assistance."
        return {"text": response, "mode": mode, "tool_calls": [], "intent": "idle"}

    if "what day" in lowered or "what date" in lowered:
        now = datetime.now()
        response = now.strftime("Today is %A, %B %d, %Y.")
        return {"text": response, "mode": mode, "tool_calls": [], "intent": "time_date"}

    if "what time" in lowered:
        now = datetime.now()
        response = now.strftime("The current time is %I:%M %p.")
        return {"text": response, "mode": mode, "tool_calls": [], "intent": "time_date"}

    nav_markers = ("take me", "navigate", "go to", "where is")
    if any(marker in lowered for marker in nav_markers):
        response = (
            "I can start navigation from the navigation endpoints. "
            "Tell me a destination like TA Office, Entrance, or Library."
        )
        return {"text": response, "mode": mode, "tool_calls": [], "intent": "navigation_hint"}

    if any(greeting in lowered for greeting in ("hello", "hi", "hey")):
        response = "Hello. I am online and ready to help with smart-glasses tasks."
        return {"text": response, "mode": mode, "tool_calls": [], "intent": "greeting"}

    if "help" in lowered:
        response = (
            "I can help with time/date queries, navigation intents, and general assistant prompts. "
            "For cloud-quality answers, set API_KEY in local settings."
        )
        return {"text": response, "mode": mode, "tool_calls": [], "intent": "help"}

    if mode == "thinking":
        response = (
            "Thinking mode is active. I am running in local fallback mode, "
            "so responses are deterministic until a cloud LLM key is configured."
        )
    else:
        response = (
            "I processed your request locally. For richer answers, configure the cloud LLM key. "
            f"Your request topic appears to be: {text[:80]}"
        )

    return {"text": response, "mode": mode, "tool_calls": []}
