"""API-based LLM model handling using Cerebras API."""
import sys
import json
import asyncio
import aiohttp
import os
from typing import List, Dict, Any
from config.settings import API_BASE_URL, API_KEY, MODEL_ID, MAX_RETRIES


# ================= MCP SAFETY =================
def log(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


# ================= API CLIENT =================
class CerebrasAPIClient:
    """Client for Cerebras API."""

    def __init__(self, base_url: str, api_key: str, model_id: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model_id = model_id
        self.session = None
        self.model_candidates = self._build_model_candidates(model_id)

    def _build_model_candidates(self, model_id: str) -> List[str]:
        candidates: List[str] = []

        def add(value: str):
            v = (value or "").strip()
            if v and v not in candidates:
                candidates.append(v)

        # Primary configured model.
        add(model_id)

        # Common normalization for typos like llama3.3-70b -> llama-3.3-70b.
        if model_id.startswith("llama") and not model_id.startswith("llama-"):
            add(model_id.replace("llama", "llama-", 1))

        # Optional overrides from env.
        raw_fallbacks = os.getenv("MODEL_FALLBACKS", "")
        for item in raw_fallbacks.split(","):
            add(item)

        # Conservative built-in fallbacks.
        add("llama-3.1-8b")
        add("llama-3.1-70b")

        return candidates

    @staticmethod
    def _looks_like_model_error(error_text: str) -> bool:
        t = (error_text or "").lower()
        return (
            "model_not_found" in t
            or "\"param\":\"model\"" in t
            or "does not exist" in t
            or "do not have access to it" in t
        )

    async def _discover_remote_models(self) -> List[str]:
        if not self.session:
            return []
        url = f"{self.base_url}/models"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    return []
                data = await response.json()
                models = data.get("data", []) if isinstance(data, dict) else []
                ids = []
                for model in models:
                    if isinstance(model, dict):
                        model_id = str(model.get("id", "")).strip()
                        if model_id:
                            ids.append(model_id)
                return ids
        except Exception:
            return []

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def chat_completion(self, messages: List[Dict[str, str]], max_tokens: int = 512, temperature: float = 0.1) -> str:
        """Make a chat completion request to Cerebras API."""
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        attempted: List[str] = []
        model_pool = list(self.model_candidates)
        discovered_added = False
        last_error = "Unknown API error"

        while model_pool:
            active_model = model_pool.pop(0)
            attempted.append(active_model)
            payload = {
                "model": active_model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            log(f"Making API request to {url} with model {active_model}")

            async with self.session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    # Promote working model for future calls.
                    self.model_id = active_model
                    self.model_candidates = [active_model] + [m for m in self.model_candidates if m != active_model]
                    return result["choices"][0]["message"]["content"]

                error_text = await response.text()
                last_error = f"API request failed with status {response.status}: {error_text}"

                # For model-specific errors, try fallbacks and discovered list.
                if self._looks_like_model_error(error_text):
                    if not discovered_added:
                        discovered = await self._discover_remote_models()
                        for m in discovered:
                            if m not in attempted and m not in model_pool:
                                model_pool.append(m)
                        discovered_added = True
                    continue

                # Non-model errors should stop early.
                raise RuntimeError(last_error)

        raise RuntimeError(last_error)


# Global API client instance
_api_client = None


async def get_api_client():
    """Get or create the global API client."""
    global _api_client
    if _api_client is None:
        if not API_KEY:
            raise ValueError("CEREBRAS_API_KEY environment variable is not set.")
        _api_client = CerebrasAPIClient(API_BASE_URL, API_KEY, MODEL_ID)
        await _api_client.__aenter__()
    return _api_client


# ================= LLM ====================
async def generate_chat(messages, max_tokens=512, temperature=0.1):
    """Generate chat response from messages using Cerebras API."""
    client = await get_api_client()
    return await client.chat_completion(messages, max_tokens, temperature)


# ============== JSON HANDLING =============
def extract_json(text: str) -> dict:
    """Extract JSON from model output."""
    import re
    text = text.strip()
    
    # Remove code blocks
    if "```" in text:
        text = re.sub(r"```(?:json)?", "", text)

    # Find JSON block
    match = re.search(r"<json>([\s\S]*?)</json>", text)
    if not match:
        raise ValueError("No <json> block found")

    raw = match.group(1)
    return json.loads(raw)


def normalize(data: dict) -> dict:
    """Normalize decision data."""
    return {
        "reasoning": str(data.get("reasoning", "")),
        "tool": data.get("tool"),
        "args": data.get("args") or {},
        "ask_user": data.get("ask_user") if isinstance(data.get("ask_user"), str) else None,
        "is_satisfied": bool(data.get("is_satisfied")),
        "answer": data.get("answer") if isinstance(data.get("answer"), str) else ""
    }


# ============== DECISION ==================
async def decide(query: str, history: list, used_tools: set, client, mode: str, image: str = None):
    """
    Make a decision based on query, history, and available tools.
    
    This is called by agent_loop for each iteration.
    """
    tools = await client.list_tools()
    tool_lines = []
    for t in tools.tools:
        input_schema = getattr(t, "inputSchema", None) or getattr(t, "input_schema", None)
        if input_schema:
            tool_lines.append(f"- {t.name}: {t.description}\n  input_schema: {json.dumps(input_schema, ensure_ascii=True)}")
        else:
            tool_lines.append(f"- {t.name}: {t.description}")
    tools_list = "\n".join(tool_lines)
    
    # Build history text
    history_text = "\n".join(history[-8:]) if history else "None"
    tool_count = sum(1 for h in history if h.startswith("Tool("))
    
    log(f"Available tools: {[t.name for t in tools.tools]}")
    log(f"History length: {len(history)}, Tool calls: {tool_count}")

    # User content
    user_content = query
    if image:
        user_content += f"\n[Image provided: {image[:50]}...]"

    # Tool instructions
    tool_usage_instructions = ""
    ql = query.lower()
    # Do not force tool use for basic local date/time questions.
    # Real-time external lookups are still valid for explicit web/news/price intent.
    if any(k in ql for k in ("news", "latest", "stock", "price", "weather", "search web")):
        tool_usage_instructions = "\n\nCRITICAL: Use search_web tool for real-time external info."
    if "use" in query.lower() and "tool" in query.lower():
        tool_usage_instructions = "\n\nCRITICAL: User asked for a tool - use it!"
    
    # Vision keywords
    vision_keywords = ["what do you see", "what is in front", "describe", "look at", "identify"]
    if any(kw in query.lower() for kw in vision_keywords):
        tool_usage_instructions = "\n\nCRITICAL: User wants vision - use VisionDetect tool."

    # Used tools warning
    used_tools_warning = ""
    if used_tools:
        used_tools_warning = f"\nNote: Already used: {[sig[0] for sig in used_tools]}"
    
    system_prompt = f"""
You are an intelligent agent in {mode} mode with access to tools.

Conversation history (last 4 exchanges):
{history_text}
{used_tools_warning}

Available tools:
{tools_list}
{tool_usage_instructions}

RULES:
- ONLY output JSON inside <json>
- If user asks for a tool, use it
- If satisfied, set is_satisfied=true and provide answer
- Avoid repeating the same tool call unless new evidence requires re-checking
- MAX {tool_count + 2} tool calls remaining

<json>
{{
  "reasoning": "",
  "tool": null,
  "args": {{}},
  "ask_user": null,
  "is_satisfied": false,
  "answer": ""
}}
</json>"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    for attempt in range(MAX_RETRIES + 1):
        try:
            raw = await generate_chat(messages)
            log("RAW MODEL OUTPUT:", raw)

            data = extract_json(raw)
            decision = normalize(data)

            return decision

        except Exception as e:
            log(f"Error in decide (attempt {attempt + 1}): {e}")
            if attempt == MAX_RETRIES:
                return {
                    "reasoning": "API error",
                    "tool": None,
                    "args": {},
                    "ask_user": None,
                    "is_satisfied": True,
                    "answer": "I encountered an issue. Please try again."
                }

            messages.append({
                "role": "system",
                "content": "FORMAT ERROR. OUTPUT VALID JSON ONLY."
            })
