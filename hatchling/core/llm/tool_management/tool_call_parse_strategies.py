"""OpenAI and Ollama-specific tool call parsing strategies.

This module provides the concrete implementations of the ToolCallParseStrategy
for both OpenAI and Ollama LLM providers, handling their different event formats.
"""

import json
import logging
import uuid
from typing import Dict, Any, Optional

from hatchling.core.llm.streaming_management.stream_subscribers import StreamEvent
from .tool_call_parse_registry import ToolCallParseRegistry, ToolCallParseStrategy
from .tool_call_parse_strategy import ToolCallParsedResult  # Import the dataclass
from hatchling.config.llm_settings import ELLMProvider


logger = logging.getLogger(__name__)

@ToolCallParseRegistry.register(ELLMProvider.OPENAI)
class OpenAIToolCallParseStrategy(ToolCallParseStrategy):
    """Parse OpenAI-specific tool call events.
    
    OpenAI tool calls may be split across multiple events, with the function name in the
    first event and arguments coming in fragments in subsequent events.
    """
    
    def __init__(self):
        """Initialize the OpenAI tool call parse strategy."""
        super().__init__(provider=ELLMProvider.OPENAI)
        # Buffer for accumulating partial tool call data across multiple events
        self._tool_call_buffers: Dict[int, Dict[str, Any]] = {}
    
    def parse_tool_call(self, event: StreamEvent) -> Optional[ToolCallParsedResult]:
        """Parse an OpenAI tool call event.

        Args:
            event (StreamEvent): The OpenAI tool call event.

        Returns:
            ToolCallParsedResult: Normalized tool call result.

        Raises:
            ValueError: If the event cannot be parsed as a valid OpenAI tool call.
        """
        if event.provider != self.provider:
            raise ValueError(f"Event provider {event.provider} does not match OpenAI strategy {self.provider}")

        try:
            data = event.data
            
            # Handle OpenAI's deprecated function_call format
            if "function_call" in data and data.get("deprecated", False):
                function_call = data["function_call"]
                parsedToolCall = ToolCallParsedResult(
                    tool_call_id="function_call",
                    function_name=function_call.get("name", ""),
                    arguments=self._parse_arguments(function_call.get("arguments", "{}"))
                )

                if "_partial" in parsedToolCall.arguments:
                    return None
                
                return parsedToolCall
            
            # Handle modern tool_calls format
            index = data.get("index", 0)
            
            # Check if this is a new tool call or a continuation
            if data.get("type") == "function" or data.get("function", {}).get("name"):
                # New tool call or first fragment
                tool_call = {
                    "id": data.get("id", f"unknown_{index}"),
                    "function": {
                        "name": data.get("function", {}).get("name", ""),
                        "arguments": data.get("function", {}).get("arguments", "")
                    }
                }
                # Store in buffer
                self._tool_call_buffers[index] = tool_call
            elif index in self._tool_call_buffers:
                # Continuation - append argument fragment
                args_fragment = data.get("function", {}).get("arguments", "")
                self._tool_call_buffers[index]["function"]["arguments"] += args_fragment
            else:
                raise ValueError(f"Received continuation for unknown tool call at index {index}")

            # Return current state (may be partial)
            tool_call = self._tool_call_buffers.get(index, {})
            parsedToolCall = ToolCallParsedResult(
                tool_call_id=tool_call.get("id", f"unknown_{index}"),
                function_name=tool_call.get("function", {}).get("name", ""),
                arguments=self._parse_arguments(tool_call.get("function", {}).get("arguments", "{}"))
            )

            # If arguments are still partial, return None to indicate more data is needed
            if "_partial" in parsedToolCall.arguments:
                return None
            return parsedToolCall
            
        except Exception as e:
            logger.error(f"Error parsing OpenAI tool call: {e}")
            raise ValueError(f"Failed to parse OpenAI tool call: {e}")
    
    def _parse_arguments(self, args_str: str) -> Dict[str, Any]:
        """Parse tool call arguments from JSON string to dictionary.
        
        Args:
            args_str (str): JSON string of arguments.
            
        Returns:
            Dict[str, Any]: Parsed arguments as a dictionary.
        """
        if not args_str:
            return {"_partial": ""}
            
        try:
            return json.loads(args_str)
        except json.JSONDecodeError:
            # Return as-is if not yet complete JSON
            return {"_partial": args_str}

@ToolCallParseRegistry.register(ELLMProvider.OLLAMA)
class OllamaToolCallParseStrategy(ToolCallParseStrategy):
    """Parse Ollama-specific tool call events.
    
    Ollama tool calls are typically delivered in a simpler format with the
    full function call in a single event.
    """
    def __init__(self):
        """Initialize the Ollama tool call parse strategy."""
        super().__init__(provider=ELLMProvider.OLLAMA)
    
    def parse_tool_call(self, event: StreamEvent) -> Optional[ToolCallParsedResult]:
        """Parse an Ollama tool call event.

        Args:
            event (StreamEvent): The Ollama tool call event.

        Returns:
            ToolCallParsedResult: Normalized tool call result.

        Raises:
            ValueError: If the event cannot be parsed as a valid Ollama tool call.
        """
        if event.provider != self.provider:
            raise ValueError(f"Event provider {event.provider} does not match Ollama strategy {self.provider}")

        try:
            tool_calls = event.data.get("tool_calls", [])
            if not tool_calls:
                raise ValueError("No tool calls found in Ollama event")
                
            # Process the first tool call (if multiple, we'd need to call parse_tool_call for each)
            tool_call = tool_calls[0]
            
            # Extract standard fields
            tool_id = tool_call.get("id", str(uuid.uuid4()))  # Use a UUID if no ID is provided
            function_name = tool_call.get("function", {}).get("name", "")
            arguments = tool_call.get("function", {}).get("arguments", {})
            
            # Ensure arguments is a dictionary
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                    #in fact
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse Ollama tool call arguments: {arguments}")
                    arguments = {"_raw": arguments}
            
            return ToolCallParsedResult(
                tool_call_id=tool_id,
                function_name=function_name,
                arguments=arguments
            )
            
        except Exception as e:
            logger.error(f"Error parsing Ollama tool call: {e}")
            raise ValueError(f"Failed to parse Ollama tool call: {e}")
