# --- 3. IMPROVED AGENT LOOP (NO decide_tool) ---

async def agent_loop(
    client,
    initial_query: str,
    max_loops: int = MAX_LOOPS,
    max_history: int = 10
):
    query = initial_query
    history = []

    for loop_count in range(1, max_loops + 1):
        print(f"\n--- THINKING LOOP {loop_count} ---")

        # 1. Decide intent
        intent = await classify_intent(query)
        print(f"Intent: {intent}")

        # 2. If final → answer immediately
        if intent == "FINAL":
            return await generate_final_answer(query, history)

        # 3. Choose tool
        tool = await choose_tool(query, client)
        if not tool:
            history.append("No suitable tool found.")
            return await generate_final_answer(query, history)

        print(f"Action: Using tool `{tool}`")

        # 4. Extract arguments
        args = await extract_args(tool, query)

        # 5. Call tool safely
        try:
            result = await client.call_tool(name=tool, arguments=args)
        except Exception as e:
            history.append(f"Tool {tool} failed: {e}")
            return await generate_final_answer(query, history)

        # 6. Record tool result
        history.append(f"Tool {tool} returned: {result}")

        # Trim history
        if len(history) > max_history:
            history = history[-max_history:]

        # 7. Update query for next iteration
        query = f"""
Given the tool result below, decide the next step.

Tool result:
{result}

Original user request:
{initial_query}
"""

    # 8. Fallback if loops exhausted
    history.append("Max reasoning steps reached.")
    return await generate_final_answer(initial_query, history)
