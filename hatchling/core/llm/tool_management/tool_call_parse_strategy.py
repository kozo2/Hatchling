"""Tool Call Parse Strategy Pattern for provider-specific parsing.

This module defines a strategy pattern interface for parsing tool call events
from different LLM providers, ensuring a consistent normalized output format.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from hatchling.core.llm.streaming_management.stream_subscribers import StreamEvent
from hatchling.config.llm_settings import ELLMProvider


class ToolCallParseStrategy(ABC):
    """Abstract base class defining the interface for tool call parsing strategies."""

    def __init__(self, provider: ELLMProvider):
        """Initialize the tool call parse strategy.
        Args:
            provider (ELLMProvider): The LLM provider for which this strategy is applicable.
        """
        self.provider = provider

    @abstractmethod
    def parse_tool_call(self, event: StreamEvent) -> Dict[str, Any]:
        """Parse a tool call event into a standardized format.
        
        Args:
            event (StreamEvent): The raw tool call event from the LLM provider.
            
        Returns:
            Dict[str, Any]: A normalized tool call dictionary with the following keys:
                - tool_id (str): The unique ID of the tool call
                - function_name (str): The name of the function being called
                - arguments (Dict[str, Any]): The arguments to the function
                
        Raises:
            ValueError: If the event cannot be parsed as a valid tool call.
        """
        pass
