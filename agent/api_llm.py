"""API-based LLM model handling using Cerebras API."""
import sys
import json
import asyncio
import aiohttp
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

        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        log(f"Making API request to {url} with model {self.model_id}")

        async with self.session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"API request failed with status {response.status}: {error_text}")

            result = await response.json()
            return result["choices"][0]["message"]["content"]


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
async def decide(query: str, iteration: int = 1, max_iterations: int = 10, mode: str = "thinking", image: str = None):
    """
    Make a SINGLE decision based on user query.

    This is called ONCE per iteration of the agent loop.
    The agent loop handles multiple iterations by feeding tool results back.

    Args:
        query: User query OR tool result from previous iteration
        iteration: Current iteration number (1-based)
        max_iterations: Maximum iterations allowed
        mode: "quick" or "thinking"
        image: Optional base64 encoded image

    Returns:
        Decision dictionary with: reasoning, tool, args, is_satisfied, answer
    """
    # Tools description
    tools_description = """
Available tools:
- search_web: Search the web for information. Args: {"query": "search terms"}
- VisionDetect: Describe what you see in an image. Args: {}
- navigation_get_directions: Get navigation directions. Args: {"from": "location", "to": "destination"}
"""

    # Build user content
    user_content = query
    if image:
        user_content += f"\n[Image provided: {image[:100]}...]"

    # Check if this is a follow-up (iteration > 1)
    is_followup = iteration > 1

    if is_followup:
        prompt_instruction = """
This is a FOLLOW-UP iteration. Based on the previous tool result:
- If the result answers the user's question, set is_satisfied=true and provide your answer
- If you need MORE information, explain what and set is_satisfied=false
- If you need a DIFFERENT tool, specify which one
- Do NOT repeat tools that already failed
"""
    else:
        prompt_instruction = """
This is the FIRST iteration. Analyze the user's request:
- If you can answer directly, set is_satisfied=true with your answer
- If you need information from a tool, specify which tool and args
- Choose the RIGHT tool for the job
"""

    # Remaining iterations message
    remaining = max_iterations - iteration
    iterations_msg = f"You have {remaining} iteration(s) remaining."

    system_prompt = f"""You are Nova, an intelligent assistant for smart glasses.

{prompt_instruction}

{iterations_msg}

{tools_description}

OUTPUT REQUIREMENTS:
- You must output ONLY JSON inside <json> tags
- No text outside the JSON block
- Be concise - your reasoning should be brief
- If satisfied, provide a clear answer suitable for audio playback

<json>
{{
  "reasoning": "Brief explanation of your thought process",
  "tool": null OR "exact_tool_name",
  "args": {{}},
  "is_satisfied": true OR false,
  "answer": "Your answer OR null"
}}
</json>"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    log(f"LLM Call (iteration {iteration}/{max_iterations})")

    for attempt in range(MAX_RETRIES + 1):
        try:
            raw = await generate_chat(messages, max_tokens=512, temperature=0.1)
            log(f"Raw LLM output: {raw[:200]}...")

            data = extract_json(raw)
            decision = normalize(data)

            log(f"Decision: tool={decision['tool']}, satisfied={decision['is_satisfied']}")
            return decision

        except Exception as e:
            log(f"Error in decide (attempt {attempt + 1}): {e}")
            if attempt == MAX_RETRIES:
                return {
                    "reasoning": "API error or malformed output",
                    "tool": None,
                    "args": {},
                    "ask_user": None,
                    "is_satisfied": True,
                    "answer": "I encountered an issue. Please try again."
                }

            messages.append({
                "role": "system",
                "content": "FORMAT ERROR. Output must be valid JSON inside <json> tags."
            })
