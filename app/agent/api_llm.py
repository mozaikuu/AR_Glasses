from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from app.config.settings import settings


class CerebrasAPIClient:
    def __init__(self, base_url: str, api_key: str, model_id: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_id = model_id

    async def complete(self, prompt: str, mode: str = "quick") -> str:
        temperature = 0.2 if mode == "quick" else 0.6
        style = (
            "You are a smart-glasses assistant. Reply with final answer only. "
            "Be direct and on-point. No chain-of-thought, no planning narration, no unnecessary steps. "
            "Use at most 3 short sentences unless the user explicitly asks for detail. "
            f"Do not exceed {settings.max_agent_loops} internal reasoning/tool passes."
        )
        payload: dict[str, Any] = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": style},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": 220,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with aiohttp.ClientSession() as session:
            timeout = aiohttp.ClientTimeout(total=12)
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=timeout,
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(f"Cerebras API error: {response.status} {text}")
                data = await response.json()
                return str(data["choices"][0]["message"]["content"])


def complete_with_cerebras(prompt: str, mode: str = "quick") -> str:
    if not settings.api_key:
        raise RuntimeError("Cerebras API key is not configured. Set API_KEY in local.settings.json or environment.")
    client = CerebrasAPIClient(settings.api_base_url, settings.api_key, settings.model_id)
    return asyncio.run(client.complete(prompt=prompt, mode=mode))
