import torch
import json
import re
from transformers import AutoModelForCausalLM, AutoTokenizer

# --- Configuration ---
MAX_LOOPS = 3  # As requested, at the top
model_id = "google/gemma-2-2b-it" 
device = "cuda" if torch.cuda.is_available() else "cpu"

# ... (Assume model and tokenizer are loaded as per your previous snippet) ...

async def decide_tool(query: str, history: list = None, mode: str = "thinking") -> dict:
    """
    LLM orchestrator that decides on tools, evaluates satisfaction, 
    and refines prompts for the next iteration.
    """
    history = history or []
    
    # 1. Build context from history for the prompt
    history_context = ""
    if history:
        history_context = "\nPREVIOUS STEPS:\n" + "\n".join(
            [f"- {h['role'].upper()}: {h['content']}" for h in history]
        )

    # 2. Define the refined System Prompt
    system_instruction = f"""
You are an agent in '{mode}' mode. Your goal: Solve the user request.
Loop limit: {MAX_LOOPS}. Current loops completed: {len([h for h in history if h['role'] == 'thought'])}.

AVAILABLE TOOLS:
- VisionDetect: Identify objects/scenes.
- Navigate: Move (args: current, destination).
- WebSearch: Get info from the internet.
- TTS: Use this for the final answer to the user.

RULES:
1. If 'quick' mode: provide the answer/tool immediately and set is_satisfied: true.
2. If 'thinking' mode: 
   - If you have enough info, set is_satisfied: true and provide the 'answer'.
   - If you need more info, select a 'tool' and/or provide a 'refined_prompt' for the next loop.
   - If a tool failed previously, use 'refined_prompt' to try a different approach.

RESPONSE FORMAT (Strict JSON):
{{
    "reasoning": "thought process",
    "tool": "ToolName or null",
    "args": {{}},
    "is_satisfied": true/false,
    "answer": "Final response for TTS",
    "refined_prompt": "Improved prompt for next loop"
}}
"""

    full_prompt = f"{system_instruction}\n{history_context}\nUSER QUERY: {query}\n\nJSON Response:"

    # 3. Generate Inference
    chat = [{"role": "user", "content": full_prompt}]
    input_ids = tokenizer.apply_chat_template(chat, tokenize=True, add_generation_prompt=True, return_tensors="pt").to(device)
    
    outputs = model.generate(
        input_ids,
        max_new_tokens=256,
        do_sample=True,
        temperature=0.2, # Low temp for structured output
        pad_token_id=tokenizer.eos_token_id
    )
    
    response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # 4. Robust JSON Extraction
    try:
        # Look for the last JSON block in the output
        json_match = re.search(r'\{.*\}', response_text.split("model")[-1], re.DOTALL)
        if json_match:
            decision = json.loads(json_match.group())
            
            # Enforce 'quick' mode behavior if necessary
            if mode == "quick":
                decision["is_satisfied"] = True
                
            return decision
    except Exception as e:
        print(f"Parsing error: {e}")
        
    # Fallback
    return {
        "reasoning": "Fallback due to parsing error",
        "tool": "TTS",
        "args": {},
        "is_satisfied": True,
        "answer": "I'm having trouble processing that right now.",
        "refined_prompt": None
    }