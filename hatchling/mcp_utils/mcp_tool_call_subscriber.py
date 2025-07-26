"""MCP Tool Call Subscriber for handling TOOL_CALL events from LLM streams.

This module provides a subscriber that listens for TOOL_CALL events from LLM providers
and dispatches them to MCPToolExecution for processing.
"""

import logging
from json import dumps as json_dumps
from typing import Dict, Any

from hatchling.core.llm.streaming_management import StreamSubscriber, StreamEvent, StreamEventType
from hatchling.core.llm.tool_management import ToolCallParseRegistry, ToolCallParsedResult
from hatchling.core.logging.logging_manager import logging_manager
from .mcp_tool_execution import MCPToolExecution


class MCPToolCallSubscriber(StreamSubscriber):
    """Subscriber that handles TOOL_CALL events and dispatches them for execution."""
    
    def __init__(self, tool_execution: MCPToolExecution):
        """Initialize the MCP tool call subscriber.
        
        Args:
            tool_execution (MCPToolExecution): The tool execution manager to dispatch calls to.
        """
        self.tool_execution = tool_execution
        self.logger = logging.getLogger(f"MCPToolCallSubscriber")
        
    def get_subscribed_events(self):
        """Get the list of event types this subscriber handles.
        
        Returns:
            List[StreamEventType]: List of event types this subscriber handles.
        """
        return [StreamEventType.LLM_TOOL_CALL_REQUEST]
    
    def on_event(self, event: StreamEvent) -> None:
        """Handle incoming events.
        
        Args:
            event (StreamEvent): The event to handle.
        """
        if event.type == StreamEventType.LLM_TOOL_CALL_REQUEST:
            try:
                parsed_tool_call = ToolCallParseRegistry.get_strategy(event.provider).parse_tool_call(event)
            except Exception as e:
                self.logger.error(f"Error parsing tool call event: {e}")
                return

            if parsed_tool_call:
                self.logger.info(f"\nParsed tool call: {json_dumps(parsed_tool_call.to_dict(), indent=2)}\n")
                self.tool_execution.stream_publisher.set_request_id(event.request_id)
                self._handle_tool_call_event(parsed_tool_call)
        else:
            self.logger.warning(f"Received unexpected event type: {event.type}")

    def _handle_tool_call_event(self, parsed_tool_call: ToolCallParsedResult) -> None:
        """Handle TOOL_CALL events by dispatching to tool execution.
        
        Args:
            event (StreamEvent): The TOOL_CALL event to handle.
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
