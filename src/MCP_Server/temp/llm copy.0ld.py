import torch
import json
import re
import asyncio
from transformers import AutoModelForCausalLM, AutoTokenizer

# --- CONFIGURATION (At the top as requested) ---
MAX_LOOPS = 1
MODEL_ID = "google/gemma-3-4b-it"  # Updated to Gemma 3 Instruct
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# --- 1. INITIALIZATION (Global scope to fix your error) ---
print(f"[*] Loading {MODEL_ID} on {DEVICE}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    dtype=torch.bfloat16 if DEVICE == "cuda" else torch.float32,
    device_map="auto" if DEVICE == "cuda" else None
)
if DEVICE == "cpu":
    model.to(DEVICE)
model.eval()


def generate(prompt, max_tokens=64, temperature=0.1):
    inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True
        )
    return tokenizer.decode(out[0], skip_special_tokens=True).strip()

# # --- 2. THE DECISION ENGINE ---
async def classify_intent(query: str) -> str:
    prompt = f"""
Decide intent.

Reply with ONE word only:
TOOL
FINAL

User query:
{query}
"""
    out = generate(prompt, max_tokens=3)
    return "TOOL" if "TOOL" in out else "FINAL"

async def choose_tool(query: str, client) -> str:
    tools = await client.list_tools()
    tool_names = ", ".join(t.name for t in tools)

    prompt = f"""
Choose the best tool.

Available tools:
{tool_names}

Reply with the tool name ONLY.
User query:
{query}
"""
    out = generate(prompt, max_tokens=10)
    for t in tools:
        if t.name.lower() in out.lower():
            return t.name
    return None


async def extract_args(tool_name: str, query: str) -> dict:
    prompt = f"""
Extract arguments for tool `{tool_name}`.

Write each argument on its own line:
key=value

User query:
{query}
"""
    out = generate(prompt, max_tokens=128)

    args = {}
    for line in out.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            args[k.strip()] = v.strip()

    return args


async def generate_final_answer(query: str, history: list) -> str:
    context = "\n".join(history[-5:])

    prompt = f"""
Answer the user clearly and concisely.

Context:
{context}

User:
{query}
"""
    return generate(prompt, max_tokens=256, temperature=0.3)

async def run_agent(client, query: str):
    history = []

    intent = await classify_intent(query)

    if intent == "FINAL":
        answer = await generate_final_answer(query, history)
        return answer

    tool = await choose_tool(query, client)
    if not tool:
        return "I couldn't decide which tool to use."

    args = await extract_args(tool, query)

    result = await client.call_tool(name=tool, arguments=args)
    history.append(f"Tool {tool} returned: {result}")

    # After tool use, always finish with a final answer
    answer = await generate_final_answer(query, history)
    return answer

async def decide_tool(query, history, client, mode="thinking"):
    """
    Uses the local Gemma 3 model to decide which MCP tool to call.
    """
    # 1. Prepare the prompt for Gemma 3
    # Note: We use 'client' only to list tools, not to 'chat'
    tools = await client.list_tools()
    tools_list = "\n".join([f"- {t.name}: {t.description}" for t in tools])

    system_prompt = f"""
    You are an agent in {mode} mode. 
    Available Tools:
    {tools_list}
    """ + """

    Return your response inside these tags ONLY:

    <json>
    {
    "reasoning": "...",
    "tool": null,
    "args": {},
    "is_satisfied": true,
    "answer": "..."
    }
    </json>

    Rules:
    - No text outside <json> tags
    - No quotes inside string values
    - No newlines inside strings

    If and ONLY IF you are finished, set:
    "is_satisfied": true
    AND you MUST include a non-empty "answer".

    If you are calling a tool:
    "is_satisfied": false
    AND "answer" MUST be null.

    """

    messages = [
        {"role": "user", "content": f"{system_prompt}\n\nUser Query: {query}"}
    ]
    
    device = DEVICE

    # 2. LOCAL INFERENCE (Replace the broken client.chat call)
    try:
        # We use the global 'tokenizer' and 'model' variables
        input_ids = tokenizer.apply_chat_template(
            messages, 
            tokenize=True, 
            add_generation_prompt=True, 
            return_tensors="pt"
        ).to(device)

        with torch.no_grad():
            outputs = model.generate(
                input_ids, 
                max_new_tokens=512, 
                temperature=0.1, 
                do_sample=True
            )

        # FIX: Only decode the NEW tokens, not the prompt
        new_tokens = outputs[0][len(input_ids[0]):]
        response_text = tokenizer.decode(new_tokens, skip_special_tokens=True)
        
        print(f"DEBUG: Raw LLM Output: {response_text}") # Helpful for debugging

        data = extract_and_fix_json(response_text)

        # 🔒 Strict Contract Enforcement
        normalized = {
            "reasoning": data.get("reasoning", "Thinking..."),
            "tool": data.get("tool"),
            "args": data.get("args", {}),
            "is_satisfied": bool(data.get("is_satisfied")),
            "answer": data["answer"] if isinstance(data.get("answer"), str) else ""
        }

        # Ensure we ALWAYS have a string for the TTS
        if not normalized["answer"] and normalized["is_satisfied"]:
             normalized["answer"] = normalized["reasoning"] if normalized["reasoning"] else "I have finished the task."
        
        return normalized

    except Exception as e:
        print(f"LLM Logic Error: {e}")
        return {"reasoning": "error", "tool": None, "is_satisfied": True, "answer": "I encountered an error processing that request."}

# --- 3. IMPROVED RECURSIVE AGENT LOOP ---

async def agent_loop(client, initial_text, mode="thinking", max_loops=MAX_LOOPS, max_history=20):
    current_text = initial_text
    history = []
    decision = {}
    
    for loop_count in range(1, max_loops + 1):
        print(f"\n--- {mode.upper()} LOOP {loop_count} ---")

        # 1. Ask the model what to do
        decision = await decide_tool(current_text, history, client, mode)

        reasoning = decision.get("reasoning", "")
        print(f"Thought: {reasoning}")

        # 2. Record reasoning
        history.append({"role": "thought", "content": reasoning})

        # Trim history to avoid context explosion
        if len(history) > max_history:
            history = history[-max_history:]

        # 3. Exit conditions
        if decision.get("is_satisfied", False):
            return decision.get("answer", "")

        if mode == "quick":
            return decision.get("answer", "")

        # 4. Tool execution
        tool_name = decision.get("tool")
        if tool_name:
            print(f"Action: Using {tool_name}...")
            try:
                result = await client.call_tool(
                    name=tool_name,
                    arguments=decision.get("args", {})
                )
                history.append({
                    "role": "tool_output",
                    "tool": tool_name,
                    "content": str(result)
                })
            except Exception as e:
                history.append({
                    "role": "tool_output",
                    "tool": tool_name,
                    "content": f"Tool error: {e}"
                })
                print(f"Tool error: {e}")

        # 5. Update prompt if refined
        refined_prompt = decision.get("refined_prompt")
        if refined_prompt:
            current_text = refined_prompt

    # 6. Fallback if max loops reached
    return (
        "I've reached my maximum reasoning limit. "
        + (decision.get("answer") or "Here is my best conclusion so far.")
    )

def extract_and_fix_json(text: str) -> dict:
    match = re.search(r"<json>([\s\S]*?)</json>", text)
    if not match:
        raise ValueError("No JSON block found")

    json_str = match.group(1)

    # Repair common LLM breakage
    json_str = json_str.replace("\n", " ")
    json_str = json_str.replace("“", '"').replace("”", '"')
    json_str = json_str.replace("’", "'")

    return json.loads(json_str)

# --- 4. MAIN EXECUTION ---
async def main(client):
    # Placeholder for user interaction
    user_input = "A silent story unfolds before my eyes, yet its name escapes me"
    
    # Run the thinking agent
    final_response = await agent_loop(client, user_input, mode="thinking")
    print(f"\nFinal Answer: {final_response}")

if __name__ == "__main__":
    asyncio.run(main())