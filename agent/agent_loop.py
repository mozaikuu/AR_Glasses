"""Main agent reasoning loop - Single LLM call with tool execution."""
import sys
import json
import asyncio
from typing import Set, Tuple, List, Optional
from agent.llm import decide, log
from agent.modes import get_mode_continuation_check
from config.settings import MAX_LOOPS
from tools.speech.tts import text_to_speech


async def agent_loop(client, user_input: str, mode: str = "thinking", image: str = None, speak: bool = True):
    """
    Main agent loop that processes user input with a SINGLE LLM call,
    then executes tools as needed.

    Flow:
    1. Call LLM ONCE with user query
    2. Execute tool if requested
    3. Feed tool result back to LLM
    4. Repeat until satisfied OR max iterations reached

    Args:
        client: MCP client for tool calls
        user_input: User query text
        mode: "quick" or "thinking"
        image: Optional base64 encoded image

    Returns:
        Final answer string
    """
    current_input = user_input
    iteration = 0
    max_iterations = MAX_LOOPS

    log(f"--- STARTING AGENT LOOP (mode={mode}) ---")
    log(f"User query: {user_input[:100]}...")

    while iteration < max_iterations:
        iteration += 1
        log(f"\n{'='*50}")
        log(f"ITERATION {iteration}/{max_iterations}")
        log(f"{'='*50}")

        # Step 1: Make DECISION (LLM call)
        decision = await decide(current_input, iteration, max_iterations, mode, image)
        log(f"LLM Reasoning: {decision['reasoning'][:200]}...")
        log(f"Tool requested: {decision['tool']}")
        log(f"Is satisfied: {decision['is_satisfied']}")
        log(f"Answer: {decision['answer'][:100] if decision['answer'] else 'None'}...")

        # Step 2: If satisfied, return answer
        if decision["is_satisfied"]:
            answer = decision["answer"] or decision["reasoning"] or "I've completed the task."
            if speak:
                asyncio.create_task(text_to_speech(answer))
            log(f"✅ Done! Final answer: {answer[:100]}...")
            return answer

        # Step 3: If no tool requested, we're done
        if not decision["tool"]:
            answer = decision["answer"] or decision["reasoning"] or "I don't have enough information."
            if speak:
                asyncio.create_task(text_to_speech(answer))
            log(f"✅ Done! No tool needed. Answer: {answer[:100]}...")
            return answer

        # Step 4: Execute tool
        tool_name = decision["tool"]
        tool_args = decision["args"] or {}

        log(f"🔧 Executing tool: {tool_name}")
        log(f"   Args: {json.dumps(tool_args)}")

        try:
            # Call the tool
            result = await client.call_tool(
                name=tool_name,
                arguments=tool_args
            )

            # Extract text from result
            result_text = str(result)
            if hasattr(result, 'content') and result.content:
                result_text = str(result.content[0].text) if result.content else str(result)

            # Truncate for logging
            result_preview = result_text[:200] + "..." if len(result_text) > 200 else result_text
            log(f"   Result: {result_preview}")

            # Step 5: Feed result back to LLM for next iteration
            current_input = f"Previous tool result from {tool_name}: {result_text}\n\nWhat is your final answer or do you need another tool?"
            log(f"🔄 Feeding result back to LLM...")

        except Exception as e:
            error_msg = f"Tool error: {str(e)}"
            log(f"❌ {error_msg}")
            current_input = f"ERROR: {error_msg}. How should I proceed?"

        # Continue loop for next iteration

    # Max iterations reached
    log(f"⚠️ Max iterations ({max_iterations}) reached")
    answer = decision.get("answer") or decision.get("reasoning") or "I need more information to complete this task."
    if speak:
        asyncio.create_task(text_to_speech(answer))
    return answer
