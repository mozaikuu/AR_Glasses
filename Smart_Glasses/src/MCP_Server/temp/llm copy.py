import torch
import json
import re
import asyncio
from transformers import AutoModelForCausalLM, AutoTokenizer

# ================= CONFIG =================
MAX_LOOPS = 8
MAX_RETRIES = 2
MODEL_ID = "google/gemma-3-4b-it"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ================= MODEL ==================
print(f"[*] Loading {MODEL_ID} on {DEVICE}...")
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

    # Remove ```json fences if present
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

RULES (VERY IMPORTANT):
- ONLY use tools if the user explicitly needs real-world or live data
- DO NOT use tools for math, definitions, opinions, or advice
- NEVER repeat the same tool call with the same arguments
- Return ONLY valid JSON inside <json> tags
- No text outside <json>
- No markdown, no explanations outside JSON
- answer MUST always be a string (empty allowed)

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
            print(f"DEBUG RAW OUTPUT:\n{raw}\n")

            data = extract_json(raw)
            decision = normalize(data)

            # Tool deduplication
            if decision["tool"]:
                signature = (decision["tool"], json.dumps(decision["args"], sort_keys=True))
                if signature in used_tools:
                    decision["tool"] = None
                    decision["is_satisfied"] = True
                    decision["answer"] = decision["answer"] or "I already performed that action."

            return decision

        except Exception as e:
            if attempt == MAX_RETRIES:
                return {
                    "reasoning": "Malformed output after retries",
                    "tool": None,
                    "args": {},
                    "ask_user": None,
                    "is_satisfied": True,
                    "answer": "I ran into an internal formatting issue. Please rephrase your request."
                }

            messages.append({
                "role": "system",
                "content": "FORMAT ERROR. You MUST output valid <json> only."
            })

# ============== AGENT LOOP ================
async def agent_loop(client, user_input, mode="thinking"):
    history = []
    used_tools = set()
    current_input = user_input

    for i in range(1, MAX_LOOPS + 1):
        print(f"\n--- {mode.upper()} LOOP {i} ---")

        decision = await decide(current_input, history, used_tools, client, mode)
        print(f"Thought: {decision['reasoning']}")

        history.append(f"User: {current_input}")
        history.append(f"Agent: {decision['reasoning']}")

        # ASK USER
        if decision["ask_user"]:
            return decision["ask_user"]

        # FINAL ANSWER
        if decision["is_satisfied"]:
            return decision["answer"]

        # TOOL CALL
        if decision["tool"]:
            sig = (decision["tool"], json.dumps(decision["args"], sort_keys=True))
            used_tools.add(sig)

            try:
                result = await client.call_tool(
                    name=decision["tool"],
                    arguments=decision["args"]
                )
                history.append(f"Tool({decision['tool']}): {result}")
                current_input = f"Tool result: {result}"
            except Exception as e:
                history.append(f"Tool error: {e}")
                return "A tool failed while processing your request."

    return "I need more information to continue."

# ================= MAIN ===================
async def main(client):
    print("[!] System Active. Waiting for input...")
    while True:
        user_input = input("User: ").strip()
        if not user_input:
            continue
        response = await agent_loop(client, user_input, mode="quick")
        print(f"Agent: {response}")
