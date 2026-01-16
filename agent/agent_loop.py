"""Main agent reasoning loop."""
import sys
import json
from typing import Set, Tuple
from agent.llm import decide, log
from agent.modes import get_mode_continuation_check
from config.settings import MAX_LOOPS


async def agent_loop(client, user_input: str, mode: str = "thinking", image: str = None):
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
    
    # Get the appropriate continuation check for the mode
    should_continue = get_mode_continuation_check(mode)

    for i in range(1, MAX_LOOPS + 1):
        log(f"--- {mode.upper()} LOOP {i} ---")

        decision = await decide(current_input, history, used_tools, client, mode, image)
        log("Thought:", decision["reasoning"])

        history.append(f"User: {current_input}")
        history.append(f"Agent: {decision['reasoning']}")

        # Check if we should ask the user
        if decision["ask_user"]:
            return decision["ask_user"]

        # Check if we're satisfied
        if decision["is_satisfied"]:
            answer = decision["answer"]
            if not answer:
                # If satisfied but no answer, try to construct one from reasoning
                answer = decision["reasoning"] or "I've completed the task."
            return answer

        # Check if we should continue
        if not should_continue(decision, i, MAX_LOOPS, history, used_tools):
            # Return what we have or a default message
            return decision["answer"] or decision["reasoning"] or "I need more information."

        # Execute tool if needed
        if decision["tool"]:
            sig = (decision["tool"], json.dumps(decision["args"], sort_keys=True))
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
    return decision.get("answer") or decision.get("reasoning") or "I need more information to complete this task."

