# --- 3. IMPROVED RECURSIVE AGENT LOOP ---

async def agent_loop(client, initial_text, mode="thinking", max_loops=MAX_LOOPS, max_history=20):
    current_text = initial_text
    history = []
    decision = {}
    
    for loop_count in range(1, max_loops + 1):
        print(f"\n--- {mode.upper()} LOOP {loop_count} ---")

        # 1. Ask the model what to do
        decision = await decide_tool(current_text, history, mode)

        reasoning = decision.get("reasoning", "")
        print(f"Thought: {reasoning}")

        # 2. Record reasoning
        history.append({"role": "thought", "content": reasoning})

        # Trim history to avoid context explosion
        if len(history) > max_history:
            history = history[-max_history:]

        # 3. Exit conditions
        if decision.get("is_satisfied", False):
            return decision.get("answer", "")

        if mode == "quick":
            return decision.get("answer", "")

        # 4. Tool execution
        tool_name = decision.get("tool")
        if tool_name:
            print(f"Action: Using {tool_name}...")
            try:
                result = await client.call_tool(
                    name=tool_name,
                    arguments=decision.get("args", {})
                )
                history.append({
                    "role": "tool_output",
                    "tool": tool_name,
                    "content": str(result)
                })
            except Exception as e:
                history.append({
                    "role": "tool_output",
                    "tool": tool_name,
                    "content": f"Tool error: {e}"
                })
                print(f"Tool error: {e}")

        # 5. Update prompt if refined
        refined_prompt = decision.get("refined_prompt")
        if refined_prompt:
            current_text = refined_prompt

    # 6. Fallback if max loops reached
    return (
        "I've reached my maximum reasoning limit. "
        + (decision.get("answer") or "Here is my best conclusion so far.")
    )
