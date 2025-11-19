from llama_cpp import Llama

# --- Configuration ---
# **CHANGE THIS** to the path of your downloaded GGUF file
model_path = "./mistral-7b-instruct-v0.2.Q4_K_M.gguf"

# --- Load Model ---
# n_gpu_layers=0 means running entirely on the CPU (change to >0 if you have a powerful NVIDIA GPU)
# n_ctx is the context window size (max tokens for prompt + response)
llm = Llama(
    model_path=model_path,
    n_gpu_layers=0,
    n_ctx=4096,
    verbose=False
)

# --- Inference (Generating Text) ---
user_prompt = "Why is the sky blue?"
# Add instruction template for Mistral
prompt_template = f"<s>[INST] {user_prompt} [/INST]"

print(f"\n--- User Prompt ---\n{user_prompt}")
print("\n--- Model Response ---")

# Run the inference
output = llm(
    prompt_template,
    max_tokens=150,  # Max length of the model's response
    temperature=0.7,
    stop=["</s>", "[/INST]"], # Tokens to stop generation
    echo=False  # Do not echo the prompt in the output
)

# Extract and print the response text
response_text = output["choices"][0]["text"]
print(response_text)