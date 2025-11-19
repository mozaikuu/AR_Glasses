import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# --- Configuration ---
# You can change the model to another small, open-source model like 'TinyLlama/TinyLlama-1.1B-Chat-v1.0'
model_id = "google/gemma-2-2b-it"

# Check for a GPU (recommended for speed) and set the device
device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading model on device: {device}")

# --- Load Model and Tokenizer ---
# The model will be downloaded once and then loaded from your local cache (making it offline)
tokenizer = AutoTokenizer.from_pretrained(model_id)

# Use 'low_cpu_mem_usage=True' to manage memory better
# If using a GPU, you can use 'torch.bfloat16' for better performance
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map=device,
    torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
    low_cpu_mem_usage=True
)
# Ensure the model is moved to the determined device
model.to(device)


# --- Inference (Generating Text) ---
def generate_response(prompt: str, max_new_tokens: int = 100):
    # Format the prompt for the model
    # (Gemma uses a specific chat template, which is handled by the tokenizer's apply_chat_template)
    chat = [{"role": "user", "content": prompt}]
    input_ids = tokenizer.apply_chat_template(chat, tokenize=True, add_generation_prompt=True, return_tensors="pt").to(device)
    
    # Generate the output
    outputs = model.generate(
        input_ids,
        max_new_tokens=max_new_tokens,
        do_sample=True, # Use sampling for more creative responses
        temperature=0.7,
        pad_token_id=tokenizer.eos_token_id # Important for batching, but good practice
    )
    
    # Decode the output, skipping the input tokens
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Post-process the response to remove the user prompt and system text
    # The response starts with the user prompt, so we find the start of the model's reply
    # We find the *last* instance of the user prompt/system structure.
    response_start = response.rfind("model")
    if response_start != -1:
        # Get the text after the 'model' role identifier and strip leading/trailing whitespace
        response_text = response[response_start + len("model"):]
        response_text = response_text.lstrip(': \n')
        return response_text
    
    return response


# --- Run the Model ---
user_prompt = "Explain the concept of a black hole in simple terms."
print(f"\n--- User Prompt ---\n{user_prompt}")
print("\n--- Model Response ---")
response = generate_response(user_prompt)
print(response)

# The model and tokenizer files are now stored locally. You can disable your internet
# and the script will still run because it loads them from your cache directory.