"""MCP Tool Call Subscriber for handling LLM_TOOL_CALL_REQUEST events from LLM streams.

This module provides a subscriber that listens for LLM_TOOL_CALL_REQUEST events from LLM providers
and dispatches them to MCPToolExecution for processing.
"""

from collections import deque
from json import dumps as json_dumps

from hatchling.core.llm.streaming_management import StreamSubscriber, StreamEvent, StreamEventType
from hatchling.core.llm.tool_management import ToolCallParseRegistry, ToolCallParsedResult
from hatchling.core.logging.logging_manager import logging_manager
from .mcp_tool_execution import MCPToolExecution


class MCPToolCallSubscriber(StreamSubscriber):
    """Subscriber that handles LLM_TOOL_CALL_REQUEST events and dispatches them for execution.

    This subscriber only processes one tool call per request ID, using a rolling buffer
    to avoid memory growth and ensure out-of-order tool calls are ignored.
    """
    
    def __init__(self, tool_execution: MCPToolExecution):
        """Initialize the MCP tool call subscriber.
        
        Args:
            tool_execution (MCPToolExecution): The tool execution manager to dispatch calls to.
        """
        self.tool_execution = tool_execution
        self.logger = logging_manager.get_session(f"MCPToolCallSubscriber")
        self._recent_request_ids = deque(maxlen=2)  # Rolling buffer for request IDs
        
    def get_subscribed_events(self):
        """Get the list of event types this subscriber handles.
        
        Returns:
            List[StreamEventType]: List of event types this subscriber handles.
        """
        return [StreamEventType.LLM_TOOL_CALL_REQUEST]
    
    def on_event(self, event: StreamEvent) -> None:
        """Handle incoming events.

        Only the first tool call for each request ID is processed. Subsequent tool calls
        for the same request ID are ignored. The buffer ensures only the last two request IDs
        are tracked, preventing memory growth.
        
        Args:
            event (StreamEvent): The event to handle.
        """
        if event.type == StreamEventType.LLM_TOOL_CALL_REQUEST:
            if event.request_id in self._recent_request_ids:
                self.logger.info(f"Skipping duplicate tool call for request_id: {event.request_id}")
                return
            
            try:
                self.logger.debug(f"Received LLM_TOOL_CALL_REQUEST event: {event}")
                parsed_tool_call = ToolCallParseRegistry.get_strategy(event.provider).parse_tool_call(event)
            except Exception as e:
                self.logger.error(f"Error parsing tool call event: {e}")
                return

            if parsed_tool_call:
                self.logger.info(f"\nParsed tool call: {json_dumps(parsed_tool_call.to_dict(), indent=2)}\n")
                self.tool_execution.stream_publisher.set_request_id(event.request_id)
                self._recent_request_ids.append(event.request_id)  # Add to rolling buffer
                self._handle_tool_call_event(parsed_tool_call)
        else:
            self.logger.warning(f"Received unexpected event type: {event.type}")

    def _handle_tool_call_event(self, parsed_tool_call: ToolCallParsedResult) -> None:
        """Handle LLM_TOOL_CALL_REQUEST events by dispatching to tool execution.
        
        Args:
            event (StreamEvent): The LLM_TOOL_CALL_REQUEST event to handle.
        """
        try:
            # Dispatch the tool call for execution
            self.tool_execution.execute_tool_sync(parsed_tool_call)

        except Exception as e:
            self.logger.error(f"Error handling tool call event: {e}")
            
            self.tool_execution.stream_publisher.publish(
                StreamEventType.MCP_TOOL_CALL_ERROR,
                {
                    "parsed_tool_call": parsed_tool_call.to_dict(),
                    "error": str(e)
                }
            )
