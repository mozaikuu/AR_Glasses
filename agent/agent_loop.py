"""Main agent reasoning loop with bounded repeated tool calls."""
import json
from typing import Dict, Set, Tuple
from agent.llm import decide, log
from agent.modes import get_mode_continuation_check
from config.settings import MAX_LOOPS


async def agent_loop(client, user_input: str, mode: str = "thinking", image: str = None):
    """
    Run the agent self-loop and return structured output.

    Returns:
        dict with:
        - answer: final response text
        - iterations: number of loops executed
        - tool_calls: list of called tools with args
        - stop_reason: why the loop stopped
        - ask_user: optional clarification prompt
    """
    history = []
    used_tools: Set[Tuple] = set()
    tool_call_counts: Dict[Tuple, int] = {}
    tool_calls = []
    current_input = user_input
    
    MAX_HISTORY = 4
    MAX_REPEAT_SAME_TOOL_ARGS = 2
    should_continue = get_mode_continuation_check(mode)
    last_decision = {"answer": "", "reasoning": ""}

    for i in range(1, MAX_LOOPS + 1):
        log(f"--- {mode.upper()} LOOP {i} ---")

        decision = await decide(current_input, history, used_tools, client, mode, image)
        last_decision = decision
        log("Thought:", decision["reasoning"])

        # Add to history
        history.append(f"User: {current_input}")
        history.append(f"Agent: {decision['reasoning']}")
        if len(history) > MAX_HISTORY * 2:
            history = history[-MAX_HISTORY * 2:]

        # Check if done
        if decision["ask_user"]:
            return {
                "answer": decision["ask_user"],
                "iterations": i,
                "tool_calls": tool_calls,
                "stop_reason": "ask_user",
                "ask_user": decision["ask_user"],
            }

        if decision["is_satisfied"]:
            return {
                "answer": decision["answer"] or decision["reasoning"] or "Done.",
                "iterations": i,
                "tool_calls": tool_calls,
                "stop_reason": "satisfied",
                "ask_user": None,
            }

        if not should_continue(decision, i, MAX_LOOPS, history, used_tools):
            return {
                "answer": decision["answer"] or decision["reasoning"] or "Need more info.",
                "iterations": i,
                "tool_calls": tool_calls,
                "stop_reason": "mode_stop",
                "ask_user": None,
            }

        # Execute tool
        if decision["tool"]:
            sig = (decision["tool"], json.dumps(decision["args"], sort_keys=True))
            call_count = tool_call_counts.get(sig, 0)

            if call_count >= MAX_REPEAT_SAME_TOOL_ARGS:
                history.append("Guard: repeated identical tool call blocked after bounded retries.")
                current_input = (
                    "Previous tool call was repeated with identical args too many times. "
                    "Use existing tool results to answer, or ask user for more specific input."
                )
                continue

            tool_call_counts[sig] = call_count + 1
            used_tools.add(sig)
            tool_calls.append({"tool": decision["tool"], "args": decision["args"]})

            try:
                result = await client.call_tool(
                    name=decision["tool"],
                    arguments=decision["args"]
                )
                
                result_text = str(result)
                if hasattr(result, 'content') and result.content:
                    result_text = str(result.content[0].text) if result.content else str(result)

                # Guard: do not let the model pretend search succeeded when it returned no docs.
                if decision["tool"] == "search_web":
                    parsed = None
                    try:
                        parsed = json.loads(result_text)
                    except Exception:
                        parsed = None
                    if isinstance(parsed, dict):
                        result_count = int(parsed.get("result_count", 0) or 0)
                        docs = parsed.get("documents") or []
                        search_unavailable = any(
                            isinstance(d, dict) and d.get("error") == "search_unavailable"
                            for d in docs
                        )
                        if result_count == 0 or search_unavailable:
                            return {
                                "answer": (
                                    "I could not retrieve reliable web results right now, so I cannot verify "
                                    "recent buffs accurately. Please retry in a moment or include a specific patch "
                                    "version (for example, 26.3) and I will summarize it."
                                ),
                                "iterations": i,
                                "tool_calls": tool_calls,
                                "stop_reason": "search_unavailable",
                                "ask_user": None,
                            }
                
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

    return {
        "answer": last_decision.get("answer") or last_decision.get("reasoning") or "Max loops reached.",
        "iterations": MAX_LOOPS,
        "tool_calls": tool_calls,
        "stop_reason": "max_loops",
        "ask_user": None,
    }
