# --- 3. THE RECURSIVE AGENT LOOP (IMPROVED) ---

async def agent_loop(
    client,
    initial_text: str,
    mode: str = "thinking",
    max_loops: int = MAX_LOOPS,
    max_history: int = 20,
):
    """
    Recursive agent loop with tool use and self-refinement.

    Args:
        client: MCP / tool-calling client
        initial_text (str): User prompt or starting context
        mode (str): "thinking" | "quick"
        max_loops (int): Hard recursion limit
        max_history (int): Cap history to avoid prompt bloat
    """

    current_text = initial_text
    history = []

    for loop_count in range(1, max_loops + 1):
        print(f"\n--- {mode.upper()} LOOP {loop_count}/{max_loops} ---")

        # 1. Ask the model what to do
        decision = await decide_tool(current_text, history, mode) or {}

        reasoning = decision.get("reasoning", "").strip()
        answer = decision.get("answer")
        is_satisfied = bool(decision.get("is_satisfied"))
        tool_name = decision.get("tool")
        tool_args = decision.get("args", {})
        refined_prompt = decision.get("refined_prompt")

        if reasoning:
            print(f"Thought: {reasoning}")
            history.append({"role": "thought", "content": reasoning})

        # Trim history if needed
        if len(history) > max_history:
            history = history[-max_history:]

        # 2. Exit conditions
        if is_satisfied or mode == "quick":
            return answer or "No final answer was produced."

        # 3. Tool usage
        if tool_name:
            print(f"Action: Using tool → {tool_name}")
            try:
                result = await client.call_tool(
                    name=tool_name,
                    arguments=tool_args
                )
                history.append({
                    "role": "tool_output",
                    "tool": tool_name,
                    "content": str(result)
                })
            except Exception as e:
                error_msg = f"Tool `{tool_name}` failed: {e}"
                print(f"⚠️ {error_msg}")
                history.append({
                    "role": "tool_error",
                    "tool": tool_name,
                    "content": error_msg
                })

        # 4. Refine prompt for next loop
        if refined_prompt:
            current_text = refined_prompt.strip()

    # 5. Hard stop fallback
    return (
        "I've reached my maximum thinking limit. "
        "Here is the best answer I can provide:\n"
        + (answer or "No conclusive answer.")
    )
