"""LLM model handling - API-based implementation."""
import sys
from agent.api_llm import generate_chat, extract_json, normalize, decide, log

# Re-export functions for backward compatibility
__all__ = ['generate_chat', 'extract_json', 'normalize', 'decide', 'log']
