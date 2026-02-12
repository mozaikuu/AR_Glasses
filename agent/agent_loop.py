"""Original agent loop with proper tool execution."""
import sys
import json
import asyncio
from typing import Set, Tuple
from agent.llm import decide, log
from agent.modes import get_mode_continuation_check
from config.settings import MAX_LOOPS


async def agent_loop(client, user_input: str, mode: str = "thinking", image: str = None):
    """
    Original agent loop that processes user input and executes tools.
    
    Returns:
        Final answer string
    """
    history = []
    used_tools: Set[Tuple] = set()
    current_input = user_input
    
    MAX_HISTORY = 4
    CLEAR_TOOLS_AFTER = 3
    should_continue = get_mode_continuation_check(mode)

    for i in range(1, MAX_LOOPS + 1):
        log(f"--- {mode.upper()} LOOP {i} ---")

        decision = await decide(current_input, history, used_tools, client, mode, image)
        log("Thought:", decision["reasoning"])

        # Add to history
        history.append(f"User: {current_input}")
        history.append(f"Agent: {decision['reasoning']}")
        if len(history) > MAX_HISTORY * 2:
            history = history[-MAX_HISTORY * 2:]

        # Check if done
        if decision["ask_user"]:
            return decision["ask_user"]

        if decision["is_satisfied"]:
            return decision["answer"] or decision["reasoning"] or "Done."

        if not should_continue(decision, i, MAX_LOOPS, history, used_tools):
            return decision["answer"] or decision["reasoning"] or "Need more info."

        # Clear tools periodically
        if i % CLEAR_TOOLS_AFTER == 0:
            used_tools.clear()

        # Execute tool
        if decision["tool"]:
            sig = (decision["tool"], json.dumps(decision["args"], sort_keys=True))
            
            if sig in used_tools:
                return "Already checked that. What else?"
            
            used_tools.add(sig)

            try:
                result = await client.call_tool(
                    name=decision["tool"],
                    arguments=decision["args"]
                )
                
                result_text = str(result)
                if hasattr(result, 'content') and result.content:
                    result_text = str(result.content[0].text) if result.content else str(result)
                
                # Truncate
                if len(result_text) > 500:
                    result_text = result_text[:500] + "..."
                
                history.append(f"Tool({decision['tool']}): {result_text}")
                current_input = f"Tool result: {result_text}"
                log(f"Tool result: {result_text[:100]}")
                
            except Exception as e:
                error_msg = f"Tool error: {str(e)}"
                history.append(f"Error: {error_msg}")
                current_input = f"Error: {error_msg}"

    return decision.get("answer") or decision.get("reasoning") or "Max loops reached."
