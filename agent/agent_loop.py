"""Main agent reasoning loop."""
import sys
import json
import asyncio
from typing import Set, Tuple
from agent.llm import decide, log
from agent.modes import get_mode_continuation_check
from config.settings import MAX_LOOPS
from tools.speech.tts import text_to_speech


async def agent_loop(client, user_input: str, mode: str = "thinking", image: str = None, speak: bool = True):
    """
    Main agent loop that processes user input and makes decisions.
    
    Args:
        client: MCP client for tool calls
        user_input: User query text
        mode: "quick" or "thinking"
        image: Optional base64 encoded image
        
    Returns:
        Final answer string
    """
    history = []
    used_tools: Set[Tuple] = set()
    current_input = user_input
    
    # Limit history to last 4 exchanges to prevent context overflow
    MAX_HISTORY = 4
    
    # Clear used_tools after this many iterations to allow retries
    CLEAR_TOOLS_AFTER = 2
    
    # Get the appropriate continuation check for the mode
    should_continue = get_mode_continuation_check(mode)

    for i in range(1, MAX_LOOPS + 1):
        log(f"--- {mode.upper()} LOOP {i} ---")

        decision = await decide(current_input, history, used_tools, client, mode, image)
        log("Thought:", decision["reasoning"])

        # Add to history (keep only last MAX_HISTORY exchanges)
        history.append(f"User: {current_input}")
        history.append(f"Agent: {decision['reasoning']}")
        if len(history) > MAX_HISTORY * 2:
            history = history[-MAX_HISTORY * 2:]

        # Check if we should ask the user
        if decision["ask_user"]:
            if speak:
                asyncio.create_task(text_to_speech(decision["ask_user"]))
            return decision["ask_user"]

        # Check if we're satisfied
        if decision["is_satisfied"]:
            answer = decision["answer"]
            if not answer:
                # If satisfied but no answer, try to construct one from reasoning
                answer = decision["reasoning"] or "I've completed the task."
            if speak:
                asyncio.create_task(text_to_speech(answer))
            return answer

        # Check if we should continue
        if not should_continue(decision, i, MAX_LOOPS, history, used_tools):
            # Return what we have or a default message
            answer = decision["answer"] or decision["reasoning"] or "I need more information."
            if speak:
                asyncio.create_task(text_to_speech(answer))
            return answer

        # Clear used_tools periodically to allow retrying
        if i % CLEAR_TOOLS_AFTER == 0:
            log(f"Clearing used_tools at iteration {i} to allow retries")
            used_tools.clear()

        # Execute tool if needed
        if decision["tool"]:
            sig = (decision["tool"], json.dumps(decision["args"], sort_keys=True))
            
            # If already used, skip and ask user for more info
            if sig in used_tools:
                log(f"Tool {decision['tool']} already used, asking for clarification")
                question = f"You've already used {decision['tool']}. What additional information do you need?"
                if speak:
                    asyncio.create_task(text_to_speech("I've already checked that. What else would you like to know?"))
                return "I've already checked that. Is there something specific you'd like me to look into further?"
            
            used_tools.add(sig)

            try:
                result = await client.call_tool(
                    name=decision["tool"],
                    arguments=decision["args"]
                )
                # Extract text from result
                result_text = str(result)
                if hasattr(result, 'content') and result.content:
                    result_text = str(result.content[0].text) if result.content else str(result)
                
                # Truncate very long results for history
                if len(result_text) > 500:
                    result_text = result_text[:500] + "..."
                
                history.append(f"Tool({decision['tool']}): {result_text}")
                current_input = f"Tool result: {result_text}"
                log(f"Tool {decision['tool']} result: {result_text[:100]}")
            except Exception as e:
                error_msg = f"Tool error: {str(e)}"
                log(error_msg)
                history.append(f"Error: {error_msg}")
                current_input = f"Tool error occurred: {error_msg}"
                # Continue loop to try again or provide answer

    # Max loops reached
    answer = decision.get("answer") or decision.get("reasoning") or "I need more information to complete this task."
    if speak:
        asyncio.create_task(text_to_speech(answer))
    return answer

