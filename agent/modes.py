"""Agent mode logic for quick and thinking modes."""
from typing import Dict, List, Set, Tuple
import json


def should_continue_quick_mode(
    decision: Dict,
    loop_count: int,
    max_loops: int,
    history: List[str] = None,
    used_tools: Set[Tuple] = None
) -> bool:
    """
    Determine if quick mode should continue.

    Quick mode:
    - Single pass through agent loop
    - Returns first satisfactory answer
    - No history looping
    """
    # Quick mode stops if we have an answer or hit max loops
    if decision.get("is_satisfied") or decision.get("answer"):
        return False
    if loop_count >= max_loops:
        return False
    # Continue only if we need to call a tool
    return decision.get("tool") is not None


def should_continue_thinking_mode(
    decision: Dict, 
    loop_count: int, 
    max_loops: int,
    history: List[str],
    used_tools: Set[Tuple]
) -> bool:
    """
    Determine if thinking mode should continue.
    
    Thinking mode:
    - Loops through history until is_satisfied=True
    - Can refine prompts based on tool results
    - Maximum loop limit
    - Better history management
    """
    # Stop if satisfied
    if decision.get("is_satisfied"):
        return False
    
    # Stop if we hit max loops
    if loop_count >= max_loops:
        return False
    
    # Continue if we have a tool to call
    if decision.get("tool"):
        # Check if we've already used this tool with these args
        sig = (decision["tool"], json.dumps(decision.get("args", {}), sort_keys=True))
        if sig in used_tools:
            # Already used this tool, stop to avoid infinite loop
            return False
        return True
    
    # Continue if we have reasoning but no answer yet
    if decision.get("reasoning") and not decision.get("answer"):
        return True
    
    return False


def get_mode_continuation_check(mode: str):
    """Get the appropriate continuation check function for the mode."""
    if mode == "quick":
        return should_continue_quick_mode
    elif mode == "thinking":
        return should_continue_thinking_mode
    else:
        # Default to thinking mode
        return should_continue_thinking_mode

