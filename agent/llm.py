"""LLM model handling and generation - API-based implementation."""
import sys
from agent.api_llm import generate_chat, log

# Re-export functions for backward compatibility
__all__ = ['generate_chat', 'extract_json', 'normalize', 'decide', 'log']

# Import the rest from api_llm
from agent.api_llm import extract_json, normalize, decide