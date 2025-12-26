import sys
import os

class _StdoutHijack:
    def write(self, data):
        if data and not data.isspace():
            sys.stderr.write(data)
    def flush(self):
        sys.stderr.flush()

sys.stdout = _StdoutHijack()

import asyncio
import json
from fastmcp import Client
from fastmcp.client import StdioTransport

# Assuming these are your internal imports
# from decide_tool import decide_tool
# from llm import decide_tool
from llm import agent_loop
from tools.text_to_speech.tts import text_to_speech
from tools.speech_recognition.Audio_transcription import transcribe_audio

# --- CONFIGURATION ---
# MAX_LOOPS = 1
# ---------------------

# async def run_agent_loop(client, user_query, mode="thinking"):
#     """Handles the reasoning/tool loop for a single query."""
#     current_prompt = user_query
#     history = []
#     loop_count = 0
#     final_answer = ""

#     while loop_count < MAX_LOOPS:
#         loop_count += 1
#         # 1. LLM Evaluation
#         # The model/tokenizer are already loaded in 'decide_tool' (Global scope)
#         decision = await decide_tool(current_prompt, history, client=client, mode=mode)
        
#         if decision.get("answer"):
#             final_answer = decision["answer"]
            
#         if final_answer == "":
#             final_answer = "I couldn't generate a final answer."
#             return final_answer

#         history.append({"role": "thought", "content": decision.get("reasoning", "")})

#         # 2. Exit Early for Quick Mode or SatisfactionA silent story unfolds before my eyes, yet its name escapes me
#         if mode == "quick" or decision.get("is_satisfied"):
#             break

#         # 3. Execute MCP Tools
#         if decision.get("tool"):
#             try:
#                 tool_result = await client.call_tool(
#                     name=decision["tool"], 
#                     arguments=decision["args"]
#                 )
#                 history.append({
#                     "role": "tool_output", 
#                     "tool": decision["tool"], 
#                     "result": str(tool_result.content[0].text)
#                 })
#             except Exception as e:
#                 history.append({"role": "error", "content": str(e)})
        
#         if decision.get("refined_prompt"):
#             current_prompt = decision["refined_prompt"]

#     return final_answer

async def agent_service(json):
    """Main service loop that keeps the server and model alive."""
    transport = StdioTransport(
        command="fastmcp",
        args=["run", "src/mcp_server/server.py:mcp", "--transport", "stdio"]
    )
    
    print("[*] Initializing persistent MCP Client...")
    
    # Keeping the Client open in this block keeps the server running
    async with Client(transport=transport) as client:
        print("[!] System Active. Waiting for voice trigger...")
        
        while True:
            try:
                # 1. Listen for input (Replace with transcribe_audio() for voice)
                # print("\n[Listening...]")
                
                # print("press anything to continue (recursion avoidance)...")
                # input()
                
                # text = input("User (or press Enter to transcribe): ")
                # # text = "what is 2 + 2?"
                # if not text:
                #     print("listening via microphone...")
                #     try:
                #         text = transcribe_audio()
                #         if not text.strip():
                #             print("[WARN] No speech detected, retrying...")
                #             continue
                #     except Exception as e:
                #         print(f"[AUDIO ERROR] {e}")
                #         continue
                
                # if text.lower() in ["exit", "quit", "stop"]:
                #     print("[*] Shutting down...")
                #     break
                text = json.get("text", "")
                print(f"User: {text}")

                # 2. Determine Mode (Dynamic logic example)
                # You could use 'quick' for simple tasks and 'thinking' for complex ones
                mode = "thinking" if len(text.split()) > 10 else "quick"

                # 3. Run Inference
                # result_text = await run_agent_loop(client, text, mode=mode)
                result_text = await agent_loop(client, text, mode=mode)
                
                # 4. Feedback
                print(f"Agent ({mode}): {result_text}")
                await text_to_speech(result_text)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[ERROR] Loop iteration failed: {e}")

if __name__ == "__main__":
    # Ensure model loading is handled inside decide_tool's module 
    # so it happens ONCE when imported.
    asyncio.run(agent_service())