import torch
import json
import re
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")   
device = "cuda" if torch.cuda.is_available() else "cpu"

# Ensure these are the same objects you loaded at the top of your script
# If this is a separate file, you need to import them or define them here
# from your_main_file import model, tokenizer, device 

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

    Return ONLY a JSON object:
    {{
      "reasoning": "why you chose this",
      "tool": "ToolName" or null,
      "args": {{}},
      "is_satisfied": true/false,
      "answer": "response if satisfied"
    }}
    """

    messages = [
        {"role": "user", "content": f"{system_prompt}\n\nUser Query: {query}"}
    ]

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
                max_new_tokens=256, 
                temperature=0.1, 
                do_sample=True
            )

        response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # 3. Parse the JSON from the model's text output
        # Gemma often puts the response after "model\n"
        json_str = re.search(r'\{.*\}', response_text.split("model")[-1], re.DOTALL).group()
        return json.loads(json_str)

    except Exception as e:
        print(f"LLM Logic Error: {e}")
        return {"reasoning": "error", "tool": None, "is_satisfied": True, "answer": "I hit a snag in my logic."}