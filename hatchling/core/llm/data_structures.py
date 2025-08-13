"""Core data structures for LLM functionality.

This module contains common data structures used across the LLM system
to avoid circular import dependencies.
"""

from typing import Dict, Any
from dataclasses import dataclass
import json

# TODO: Standardize of dataclasses usage. Where to put them?
# What to name them? Do we keep them as dataclasses or up to pydantic?
# This "todo" stands for all the dataclasses in this project. This
# must be tackled globally
@dataclass
class ToolCallParsedResult:
    """Normalized representation of a tool call event."""
    tool_call_id: str
    function_name: str
    arguments: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the parse result to a dictionary."""
        return {
            "tool_call_id": self.tool_call_id,
            "function_name": self.function_name,
            "arguments": self.arguments
        }
    
    def to_ollama_dict(self) -> Dict[str, Any]:
        """Convert the parse result to Ollama format."""
        return {
            "type": "function",
            "id": self.tool_call_id,
            "function": {
                "name": self.function_name,
                "arguments": self.arguments
            }
        }
    
    def to_openai_dict(self) -> Dict[str, Any]:
        """Convert the parse result to OpenAI format."""
        return {
            "type": "function",
            "id": self.tool_call_id,
            "function": {
                "name": self.function_name,
                "arguments": json.dumps(self.arguments)
            }
        }
