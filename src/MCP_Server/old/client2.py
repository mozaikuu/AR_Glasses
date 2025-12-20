import asyncio
import json
from fastmcp import Client
from fastmcp.client import StdioTransport

# Mocking your internal imports based on your snippet
# from llm_inferrence import decide_tool 
from mcp_server.decide_tool import decide_tool
from tools.text_to_speech.tts import text_to_speech
from tools.speech_recognition.Audio_transcription import transcribe_audio

# --- CONFIGURATION ---
MAX_LOOPS = 3
MODE = "thinking"  # Options: "quick" or "thinking"
# ---------------------

async def run_agent_loop(client, user_query):
    current_prompt = user_query
    history = []
    loop_count = 0
    final_answer = ""

    print(f"[*] Starting agent in {MODE} mode...")

    while loop_count < MAX_LOOPS:
        loop_count += 1
        print(f"\n[Loop {loop_count}/{MAX_LOOPS}] Analyzing: {current_prompt[:50]}...")

        # 1. LLM Evaluation & Decision
        # We expect decide_tool to return: 
        # { "tool": "name"|None, "args": {}, "is_satisfied": bool, "answer": "text", "refined_prompt": "text" }
        decision = await decide_tool(current_prompt, history, mode=MODE)
        
        # 2. Update the answer and history
        final_answer = decision.get("answer", "")
        history.append({"role": "thought", "content": decision.get("reasoning", "")})

        # 3. Check for completion
        # If quick mode: exit after 1st run. If thinking: check satisfaction.
        if MODE == "quick" or decision.get("is_satisfied") is True:
            print("[+] Target achieved or max loops reached.")
            break

        # 4. Tool Execution (if needed)
        if decision.get("tool"):
            print(f"[!] Executing tool: {decision['tool']}")
            try:
                tool_result = await client.call_tool(
                    name=decision["tool"],
                    arguments=decision["args"]
                )
                # Add tool output to context
                history.append({
                    "role": "tool_output", 
                    "tool": decision["tool"], 
                    "result": tool_result.content[0].text
                })
            except Exception as e:
                history.append({"role": "error", "content": str(e)})
        
        # 5. Model improves its own prompt for the next loop
        if decision.get("refined_prompt"):
            current_prompt = decision["refined_prompt"]

    return final_answer

async def agent():
    transport = StdioTransport(
        command="fastmcp",
        args=[
            "run",
            "src/mcp_server/server.py:mcp",
            "--transport",
            "stdio",
        ],
    )
    
    async with Client(transport=transport) as client:
        # 1. Input Phase
        # await text_to_speech("What do you need help with, sir?")
        
        # For testing, we use your specific query
        # text = transcribe_audio()
        text = "A silent story unfolds before my eyes, yet its name escapes me"
        
        # 2. Reasoning Phase
        result_text = await run_agent_loop(client, text)
        
        # 3. Output Phase
        print("\nFinal Agent Response:", result_text)
        await text_to_speech(result_text)

if __name__ == "__main__":
    asyncio.run(agent())