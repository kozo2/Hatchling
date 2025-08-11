"""Tool Call Parse Strategy Pattern for provider-specific parsing.

This module defines a strategy pattern interface for parsing tool call events
from different LLM providers, ensuring a consistent normalized output format.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json

from hatchling.core.llm.streaming_management.stream_subscribers import StreamEvent
from hatchling.config.llm_settings import ELLMProvider


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


class ToolCallParseStrategy(ABC):
    """Abstract base class defining the interface for tool call parsing strategies."""

    def __init__(self, provider: ELLMProvider):
        """Initialize the tool call parse strategy.
        Args:
            provider (ELLMProvider): The LLM provider for which this strategy is applicable.
        """
        self.provider = provider

    @abstractmethod
    def parse_tool_call(self, event: StreamEvent) -> Optional[ToolCallParsedResult]:
        """Parse a tool call event into a standardized format.
        
        Args:
            event (StreamEvent): The raw tool call event from the LLM provider.
            
        Returns:
            ToolCallParsedResult: A normalized representation of the tool call,
                                 including tool_call_id, function_name, and arguments.
                                 By default, the role is set to "tool_call".
                
        Raises:
            ValueError: If the event cannot be parsed as a valid tool call.
        """
        pass
