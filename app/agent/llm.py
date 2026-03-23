from __future__ import annotations

from app.agent.agent_loop import decide
from app.agent.api_llm import complete_with_cerebras
from app.config.settings import settings
from app.models.requests import ProcessRequest


def complete(prompt: str, mode: str = "quick") -> str:
    if settings.model_provider.lower() == "cerebras":
        try:
            return complete_with_cerebras(prompt=prompt, mode=mode)
        except Exception as exc:
            return f"Cerebras request failed: {exc}"
    local = decide(ProcessRequest(text=prompt, mode=mode, client="local-llm-fallback"))
    return str(local.get("text") or "Ready.")
