import sys
import torch
import json
import re
import asyncio
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer

# ================= MCP SAFETY =================
def log(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

logging.basicConfig(level=logging.ERROR, stream=sys.stderr)

# ================= CONFIG =================
MAX_LOOPS = 8
MAX_RETRIES = 2
MODEL_ID = "google/gemma-3-4b-it"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ================= MODEL ==================
log(f"[*] Loading {MODEL_ID} on {DEVICE}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.bfloat16 if DEVICE == "cuda" else torch.float32,
    device_map="auto" if DEVICE == "cuda" else None
)
if DEVICE == "cpu":
    model.to(DEVICE)
model.eval()

# ================= LLM ====================
def generate_chat(messages, max_tokens=512, temperature=0.1):
    input_ids = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(DEVICE)

    with torch.no_grad():
        output = model.generate(
            input_ids,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True
        )

    new_tokens = output[0][len(input_ids[0]):]
    return tokenizer.decode(new_tokens, skip_special_tokens=True)

# ============== JSON HANDLING =============
def extract_json(text: str) -> dict:
    text = text.strip()
    if "```" in text:
        text = re.sub(r"```(?:json)?", "", text)

    match = re.search(r"<json>([\s\S]*?)</json>", text)
    if not match:
        raise ValueError("No <json> block found")

    raw = match.group(1)
    raw = raw.replace("“", '"').replace("”", '"').replace("’", "'")
    return json.loads(raw)

def normalize(data: dict) -> dict:
    return {
        "reasoning": str(data.get("reasoning", "")),
        "tool": data.get("tool"),
        "args": data.get("args") or {},
        "ask_user": data.get("ask_user") if isinstance(data.get("ask_user"), str) else None,
        "is_satisfied": bool(data.get("is_satisfied")),
        "answer": data.get("answer") if isinstance(data.get("answer"), str) else ""
    }

# ============== DECISION ==================
async def decide(query, history, used_tools, client, mode):
    tools = await client.list_tools()
    tools_list = "\n".join(f"- {t.name}: {t.description}" for t in tools)
    history_text = "\n".join(history[-6:]) if history else "None"

    system_prompt = f"""
You are an intelligent agent running in {mode} mode.

Conversation history:
{history_text}

Available tools:
{tools_list}

RULES:
- ONLY output JSON inside <json>
- No text outside JSON

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
        {"role": "user", "content": query}
    ]

    for attempt in range(MAX_RETRIES + 1):
        try:
            raw = generate_chat(messages)
            log("RAW MODEL OUTPUT:", raw)

            data = extract_json(raw)
            decision = normalize(data)

            if decision["tool"]:
                sig = (decision["tool"], json.dumps(decision["args"], sort_keys=True))
                if sig in used_tools:
                    decision["tool"] = None
                    decision["is_satisfied"] = True
                    decision["answer"] = decision["answer"] or "Action already taken."

            return decision

        except Exception:
            if attempt == MAX_RETRIES:
                return {
                    "reasoning": "Malformed output",
                    "tool": None,
                    "args": {},
                    "ask_user": None,
                    "is_satisfied": True,
                    "answer": "Internal formatting issue."
                }

            messages.append({
                "role": "system",
                "content": "FORMAT ERROR. OUTPUT VALID JSON ONLY."
            })

# ============== AGENT LOOP ================
async def agent_loop(client, user_input, mode="thinking"):
    history = []
    used_tools = set()
    current_input = user_input

    for i in range(1, MAX_LOOPS + 1):
        log(f"--- {mode.upper()} LOOP {i} ---")

        decision = await decide(current_input, history, used_tools, client, mode)
        log("Thought:", decision["reasoning"])

        history.append(f"User: {current_input}")
        history.append(f"Agent: {decision['reasoning']}")

        if decision["ask_user"]:
            return decision["ask_user"]

        if decision["is_satisfied"]:
            return decision["answer"]

        if decision["tool"]:
            sig = (decision["tool"], json.dumps(decision["args"], sort_keys=True))
            used_tools.add(sig)

            result = await client.call_tool(
                name=decision["tool"],
                arguments=decision["args"]
            )
            history.append(f"Tool({decision['tool']}): {result}")
            current_input = f"Tool result: {result}"

    return "I need more information."

# ================= MAIN ===================
async def main(client):
    log("[!] System Active. Waiting for input...")
    while True:
        user_input = input().strip()
        if not user_input:
            continue
        response = await agent_loop(client, user_input, mode="quick")
        log("Agent response ready")
