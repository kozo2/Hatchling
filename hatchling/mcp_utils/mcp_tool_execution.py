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

from hatchling.mcp_utils.manager import mcp_manager
from hatchling.core.logging.logging_manager import logging_manager
from hatchling.config.settings import AppSettings
from hatchling.core.llm.streaming_management import StreamPublisher, StreamEventType
from hatchling.core.llm.tool_management import ToolCallParsedResult

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
        self._stream_publisher = StreamPublisher()
        
        # Tool calling control properties
        self.current_tool_call_iteration = 0
        self.tool_call_start_time = None
        self.root_tool_query = None  # Track the original user query that started the tool sequence
    
    @property
    def stream_publisher(self) -> StreamPublisher:
        """Get the stream publisher for this tool execution manager.
        
        Returns:
            StreamPublisher: The stream publisher instance.
        """
        return self._stream_publisher

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
        self._stream_publisher.publish(StreamEventType.MCP_TOOL_CALL_DISPATCHED, parsed_tool_call.to_dict())

        # Publish tool call progress event
        self._stream_publisher.publish(StreamEventType.MCP_TOOL_CALL_PROGRESS, parsed_tool_call.to_dict())

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
                self._stream_publisher.publish(StreamEventType.MCP_TOOL_CALL_RESULT, result_obj.to_dict())
            else:
                result_obj = ToolCallExecutionResult(
                    **parsed_tool_call.to_dict(),
                    result=tool_response,
                    error="Tool execution failed or returned no valid response"
                )
                self._stream_publisher.publish(StreamEventType.MCP_TOOL_CALL_ERROR, result_obj.to_dict())

        except Exception as e:
            self.logger.error(f"Error executing tool: {e}")
            result_obj = ToolCallExecutionResult(
                **parsed_tool_call.to_dict(),
                result=None,
                error=str(e)
            )
            self._stream_publisher.publish(StreamEventType.MCP_TOOL_CALL_ERROR, result_obj.to_dict())

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

    async def handle_tool_calling_chain(self,
                    session,
                    api_manager,
                    history,
                    full_response: str,
                    message_tool_calls: List[Dict[str, Any]],
                    tool_results: List[Dict[str, Any]]
                    ) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        .. deprecated:: 2025.07.21
            This method is deprecated and will be removed in a future release.
        
        Handle the response from the LLM API and manage tool calling chains.
        
        Args:
            session: The http session to use for API requests.
            api_manager: The API manager for making API calls.
            history: The message history.
            full_response (str): The latest response from the LLM.
            message_tool_calls (List[Dict[str, Any]]): List of tool calls from the response.
            tool_results (List[Dict[str, Any]]): List of tool execution results.
                        
        Returns:
            Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]: A tuple containing:
                - str: The full response text
                - List[Dict[str, Any]]: The message tool calls
                - List[Dict[str, Any]]: The tool execution results
        """
        _full_response, _message_tool_calls, _tool_results = full_response, message_tool_calls, tool_results
        
        elapsed_time = time.time() - self.tool_call_start_time
        
        # Check if we've hit limits
        reached_max_iterations = self.current_tool_call_iteration >= self.settings.tool_calling.max_iterations
        reached_time_limit = elapsed_time >= self.settings.tool_calling.max_working_time

        if reached_max_iterations or reached_time_limit:
            # We've reached a limit, return what we have
            limit_reason = "maximum iterations" if reached_max_iterations else "time limit"
            self.logger.warning(f"Reached {limit_reason} for tool calling ({self.current_tool_call_iteration} iterations, {elapsed_time:.1f}s)")
            return _full_response, _message_tool_calls, _tool_results
        
        # Continue with sequential tool calling - prepare new payload with updated messages
        self.logger.debug("Preparing next payload for sequential tool calling")
        history.add_user_message(f"Given the tool results: {tool_results}, do you have enough information to answer the original query: `{self.root_tool_query}`? If not, please ask for more information or continue using tools.")
        
        # Prepare the next payload
        payload = api_manager.prepare_request_payload(history.get_messages())
        
        payload = api_manager.add_tools_to_payload(payload, self.get_tools_for_payload())
    
        __full_response, __message_tool_calls, __tool_results = await api_manager.stream_response(
                session, payload, history, self, print_output=False, update_history=True
            )

        if __tool_results:
            # Process the next step (recursive call)
            self.logger.info(f"Continuing with tool calling iteration {self.current_tool_call_iteration}/{self.settings.tool_calling.max_iterations} ({elapsed_time:.1f}s elapsed)")
            _full_response, _message_tool_calls, _tool_results = await self.handle_tool_calling_chain(
                                                            session,
                                                            api_manager, 
                                                            history,
                                                            _full_response+"\n\n"+__full_response,
                                                            _message_tool_calls+__message_tool_calls,
                                                            _tool_results+__tool_results)

        # Return the original response if it was a direct LLM response with no tool usage
        return _full_response, _message_tool_calls, _tool_results
