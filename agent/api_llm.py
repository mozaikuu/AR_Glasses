"""API-based LLM model handling using Cerebras API."""
import sys
import json
import aiohttp
import asyncio
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
            raise ValueError("CEREBRAS_API_KEY environment variable is not set. Please set your Cerebras API key.")
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
    if "```" in text:
        text = re.sub(r"```(?:json)?", "", text)

    match = re.search(r"<json>([\s\S]*?)</json>", text)
    if not match:
        raise ValueError("No <json> block found")

    raw = match.group(1)
    raw = raw.replace(""", '"').replace(""", '"').replace("'", "'")
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

    Args:
        query: User query text
        history: Conversation history (will be limited to last 4 exchanges)
        used_tools: Set of (tool_name, args_json) tuples already used
        client: MCP client
        mode: "quick" or "thinking"
        image: Optional base64 encoded image

    Returns:
        Decision dictionary
    """
    tools = await client.list_tools()
    tools_list = "\n".join(f"- {t.name}: {t.description}" for t in tools.tools)
    
    # Limit history to last 4 exchanges to prevent context overflow
    # Each exchange is 2 items (User + Agent)
    history_text = "\n".join(history[-8:]) if history else "None"
    
    # Count how many tool results are in history
    tool_count = sum(1 for h in history if h.startswith("Tool("))
    
    log(f"Available tools: {[t.name for t in tools.tools]}")
    log(f"History length: {len(history)}, Tool calls: {tool_count}")

    # Build user content with optional image
    user_content = query
    if image:
        user_content += f"\n[Image provided: {image[:50]}...]"

    # Build explicit tool usage instructions
    tool_usage_instructions = ""
    if "search" in query.lower() or "time" in query.lower() or "current" in query.lower():
        tool_usage_instructions = "\n\nCRITICAL: The user is asking for real-time information (time, current events, web search). You MUST use the search_web tool to get this information. Set tool='search_web' with args={'query': 'user question here'}."
    if "use" in query.lower() and "tool" in query.lower():
        tool_usage_instructions = "\n\nCRITICAL: The user explicitly asked you to use a tool. You MUST use the tool they mentioned. Do not say you don't have access to tools - you do!"
    
    # Check if user explicitly asked for vision
    vision_keywords = ["what do you see", "what is in front", "describe the view", "look at", "identify"]
    if any(kw in query.lower() for kw in vision_keywords):
        tool_usage_instructions = "\n\nCRITICAL: The user wants to see/identify something. You MUST use VisionDetect tool to describe what you see. Set tool='VisionDetect' with args={}.".format(
            "{}" if mode == "quick" else "{}"
        )
    
    # Only show used tools warning if they've already been used
    used_tools_warning = ""
    if used_tools:
        used_tools_warning = f"\nNote: These tools have already been used in this session: {[sig[0] for sig in used_tools]}. Consider if you need to use them again with different parameters."
    
    system_prompt = f"""
You are an intelligent agent running in {mode} mode with access to tools.

Conversation history (last 4 exchanges):
{history_text}
{used_tools_warning}

Available tools:
{tools_list}
{tool_usage_instructions}

RULES:
- ONLY output JSON inside <json>
- No text outside JSON
- If the user asks you to use a tool, you MUST use that tool - DO NOT say you don't have it
- If you need real-time information, use the appropriate tool
- If you have a complete answer, set "is_satisfied" to true and provide it in "answer"
- If you need to use a tool, specify "tool" and "args" (tool name must match exactly: search_web or VisionDetect)
- In thinking mode, you can refine your approach based on tool results
- If a tool was already used, try a DIFFERENT approach or ask for clarification
- MAX {tool_count + 2} tool calls remaining before you must give an answer

<json>
{{
  "reasoning": "",
  "tool": null,
  "args": {{}},
  "ask_user": null,
  "is_satisfied": false,
  "answer": ""
}}
</json>
"""

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

            # If tool already used, try to proceed without it
            if decision["tool"]:
                sig = (decision["tool"], json.dumps(decision["args"], sort_keys=True))
                if sig in used_tools:
                    log(f"Tool {decision['tool']} already used, suggesting alternative approach")
                    # Instead of blocking, suggest the LLM try a different approach
                    decision["tool"] = None
                    decision["is_satisfied"] = True
                    if not decision["answer"]:
                        decision["answer"] = "I've already checked that. Is there something else you'd like to know?"

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
                    "answer": "I encountered an issue processing your request. Please try again."
                }

            messages.append({
                "role": "system",
                "content": "FORMAT ERROR. OUTPUT VALID JSON ONLY."
            })
