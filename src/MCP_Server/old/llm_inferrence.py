import torch
import json
from transformers import AutoModelForCausalLM, AutoTokenizer

# --- Configuration ---
model_id = "google/gemma-2-2b-it"
device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading model on device: {device}")

# --- Load Model and Tokenizer ---
tokenizer = AutoTokenizer.from_pretrained(model_id)

# Load model without device_map to avoid accelerate dependency
if device == "cuda":
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        dtype=torch.bfloat16,
        low_cpu_mem_usage=True
    )
else:
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        dtype=torch.float32,
        low_cpu_mem_usage=True
    )

model.to(device)
model.eval()  # Set to evaluation mode


# --- Tool Selection with LLM ---
async def decide_tool(user_text: str) -> dict:
    """
    Uses LLM to intelligently select the appropriate tool based on user input.
    """
    
    # Define available tools and their descriptions
    tools_description = """
Available Tools:
1. VisionDetect - Use when user wants to see something, identify objects, or asks "what is this/that"
2. Navigate - Use when user wants to go somewhere or navigate to a location
3. TTS (Text-to-Speech) - Default tool for general responses, reading text, or when no other tool applies

Examples:
- "What do you see?" -> VisionDetect
- "Go to the office" -> Navigate (from: entrance, to: office)
- "Tell me a joke" -> TTS
- "Navigate to the kitchen" -> Navigate
- "What is that object?" -> VisionDetect
"""

    prompt = f"""You are a smart assistant that selects the appropriate tool based on user commands.

{tools_description}

User Command: "{user_text}"

Analyze the command and respond with ONLY a JSON object in this exact format:
{{
    "tool": "ToolName",
    "args": {{}}
}}

For Navigate tool, include "current" and "destination" in args.
For VisionDetect and TTS, args should be empty {{}}.

JSON Response:"""

    # Format the prompt for the model
    chat = [{"role": "user", "content": prompt}]
    input_ids = tokenizer.apply_chat_template(
        chat, 
        tokenize=True, 
        add_generation_prompt=True, 
        return_tensors="pt"
    ).to(device)
    
    # Generate the output
    outputs = model.generate(
        input_ids,
        max_new_tokens=150,
        do_sample=True,
        temperature=0.3,  # Lower temperature for more deterministic tool selection
        pad_token_id=tokenizer.eos_token_id
    )
    
    # Decode the output
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Show the full model response for debugging
    print(f"\n{'='*60}")
    print(f"USER INPUT: {user_text}")
    print(f"{'='*60}")
    print(f"FULL MODEL RESPONSE:\n{response}")
    print(f"{'='*60}\n")
    
    # Extract the model's response (after the prompt)
    response_start = response.rfind("model")
    if response_start != -1:
        response_text = response[response_start + len("model"):].lstrip(': \n')
    else:
        response_text = response
    
    print(f"EXTRACTED TEXT:\n{response_text}")
    print(f"{'='*60}\n")
    
    # Parse JSON from response
    try:
        # Try to find JSON in the response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            print(f"EXTRACTED JSON STRING:\n{json_str}")
            print(f"{'='*60}\n")
            
            tool_decision = json.loads(json_str)
            
            # Validate the response structure
            if "tool" in tool_decision and "args" in tool_decision:
                # Set default args if Navigate tool is selected but args are empty
                if tool_decision["tool"] == "Navigate" and not tool_decision["args"]:
                    tool_decision["args"] = {"current": "entrance", "destination": "office"}
                
                print(f"✅ FINAL DECISION:\n{json.dumps(tool_decision, indent=2)}")
                print(f"{'='*60}\n")
                return tool_decision
        else:
            print(f"❌ No JSON found in response")
            print(f"{'='*60}\n")
    
    except (json.JSONDecodeError, ValueError) as e:
        print(f"❌ ERROR parsing LLM response: {e}")
        print(f"Raw response: {response_text}")
        print(f"{'='*60}\n")
    
    # Fallback to TTS if parsing fails
    print(f"⚠️ FALLBACK: Using TTS tool")
    print(f"{'='*60}\n")
    return {"tool": "TTS", "args": {}}


# --- Synchronous version (if needed) ---
def decide_tool_sync(user_text: str) -> dict:
    """
    Synchronous version of decide_tool for non-async contexts.
    """
    import asyncio
    return asyncio.run(decide_tool(user_text))


# --- Test the Tool Selection ---
async def test_tool_selection():
    test_cases = [
        "What do you see in front of me?",
        "Go to the office",
        "Navigate to the kitchen",
        "What is that object?",
        "Tell me a joke",
        "Can you see what's on the table?",
        "Take me to the conference room"
    ]
    
    print("\n=== Testing Tool Selection ===\n")
    for test_text in test_cases:
        result = await decide_tool(test_text)
        print(f"Input: '{test_text}'")
        print(f"Selected Tool: {json.dumps(result, indent=2)}\n")


# --- Run Tests ---
if __name__ == "__main__":
    import asyncio
    asyncio.run(test_tool_selection())
