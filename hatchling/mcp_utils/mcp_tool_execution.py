"""MCP tool execution management with event publishing.

This module provides enhanced functionality for handling tool execution requests from LLMs,
managing tool calling chains, and processing tool results with event-driven architecture.
"""

import json
import logging
import time
import asyncio
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass
from mcp.types import CallToolResult

from hatchling.mcp_utils.manager import mcp_manager
from hatchling.core.logging.logging_manager import logging_manager
from hatchling.config.settings import AppSettings
from hatchling.core.llm.event_system import EventPublisher, EventType
from hatchling.core.llm.data_structures import ToolCallParsedResult

@dataclass
class ToolCallExecutionResult:
    """Data class to hold the result of a tool call execution."""
    tool_call_id: str
    function_name: str
    arguments: Dict[str, Any]
    result: Any
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "tool_call_id": self.tool_call_id,
            "function_name": self.function_name,
            "arguments": self.arguments,
            "result": self.result,
            "error": self.error
        }
    
    def to_openai_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary suitable for OpenAI API."""
        return {
            "tool_call_id": self.tool_call_id,
            "content": str(self.result.content[0].text) if self.result.content[0].text else "No result",
        }

    def to_ollama_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary suitable for Ollama API."""
        return {
            "content": str(self.result.content[0].text) if self.result.content[0].text else "No result",
            "tool_name": self.function_name
        }

class MCPToolExecution:
    """Manages tool execution and tool calling chains with event publishing."""
    
    def __init__(self, settings: AppSettings = None):
        """Initialize the MCP tool execution manager.
        
        Args:
            settings (AppSettings, optional): The application settings.
                                            If None, uses the singleton instance.
        """
        self.settings = settings or AppSettings.get_instance()
        self.logger = logging_manager.get_session("MCPToolExecution")
        logging_manager.set_log_level(logging.DEBUG)
        
        # Initialize event publisher
        self._event_publisher = EventPublisher()
        
        # Tool calling control properties
        self.current_tool_call_iteration = 0
        self.tool_call_start_time = None
        self.root_tool_query = None  # Track the original user query that started the tool sequence
    
    @property
    def stream_publisher(self) -> EventPublisher:
        """Get the stream publisher for this tool execution manager.
        
        Returns:
            EventPublisher: The stream publisher instance.
        """
        return self._event_publisher

    def reset_for_new_query(self, query: str) -> None:
        """Reset tool execution state for a new user query.
        
        Args:
            query (str): The user's query that's starting a new conversation.
        """
        self.current_tool_call_iteration = 0
        self.tool_call_start_time = time.time()
        self.root_tool_query = query
    
    async def execute_tool(self, parsed_tool_call: ToolCallParsedResult) -> None:
        """Execute a tool and return its result.

        Sends the tool call to the MCPManager for execution and publishes events
        for tool call dispatched, progress, result, and error handling.
        You can subscribe to `stream_publisher` of this class to receive
        MCP_TOOL_CALL_DISPATCHED, MCP_TOOL_CALL_PROGRESS, MCP_TOOL_CALL_RESULT, and MCP_TOOL_CALL_ERROR events.
        That will allow you to react to tool calls in real-time and handle them accordingly.

        Args:
            parsed_tool_call (ToolCallParsedResult): The parsed tool call containing
                tool_id, function_name, and arguments.
        """
        self.logger.debug(
            f"Redirecting to tool execution for (tool_call_id: {parsed_tool_call.tool_call_id}; "
            f"function: {parsed_tool_call.function_name}; arguments: {parsed_tool_call.arguments})"
        )

        self.current_tool_call_iteration += 1

        # Publish tool call dispatched event
        self._event_publisher.publish(EventType.MCP_TOOL_CALL_DISPATCHED, parsed_tool_call.to_dict())

        try:
            # Process the tool call using MCPManager
            tool_response = await mcp_manager.execute_tool(
                tool_name=parsed_tool_call.function_name,
                arguments=parsed_tool_call.arguments
            )
            self.logger.debug(f"Tool {parsed_tool_call.function_name} executed with responses: {tool_response}")

            if tool_response and not tool_response.isError:
                result_obj = ToolCallExecutionResult(
                    **parsed_tool_call.to_dict(),
                    result=tool_response,
                    error=None
                )
                self._event_publisher.publish(EventType.MCP_TOOL_CALL_RESULT, result_obj.to_dict())
            else:
                result_obj = ToolCallExecutionResult(
                    **parsed_tool_call.to_dict(),
                    result=tool_response,
                    error="Tool execution failed or returned no valid response"
                )
                self._event_publisher.publish(EventType.MCP_TOOL_CALL_ERROR, result_obj.to_dict())

        except Exception as e:
            self.logger.error(f"Error executing tool: {e}")
            result_obj = ToolCallExecutionResult(
                **parsed_tool_call.to_dict(),
                result=CallToolResult(
                    content=[{"type": "text", "text": f"{e}"}],
                    isError=True,
                ),
                error=str(e)
            )
            self._event_publisher.publish(EventType.MCP_TOOL_CALL_ERROR, result_obj.to_dict())

    def execute_tool_sync(self, parsed_tool_call: ToolCallParsedResult) -> None:
        """Synchronous wrapper for execute_tool that handles async execution internally.
        
        This method creates a task to execute the tool asynchronously without blocking
        the caller. It's designed for use in synchronous contexts where you want to
        dispatch tool execution but don't need to wait for the result.
        
        Args:
            parsed_tool_call (ToolCallParsedResult): The parsed tool call containing
                tool_id, function_name, and arguments.
        """
        try:
            # Try to create a task in the current event loop
            asyncio.create_task(self.execute_tool(parsed_tool_call))
        except RuntimeError:
            # No event loop running, create one for this execution
            try:
                asyncio.run(self.execute_tool(parsed_tool_call))
            except Exception as e:
                self.logger.warning(f"Failed to execute tool synchronously: {e}")

