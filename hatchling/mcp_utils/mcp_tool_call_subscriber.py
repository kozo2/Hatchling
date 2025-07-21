"""MCP Tool Call Subscriber for handling TOOL_CALL events from LLM streams.

This module provides a subscriber that listens for TOOL_CALL events from LLM providers
and dispatches them to MCPToolExecution for processing.
"""

import logging
from typing import Dict, Any

from hatchling.core.llm.providers.subscription import (
    StreamSubscriber,
    StreamEvent,
    StreamEventType
)
from hatchling.mcp_utils.mcp_tool_execution import MCPToolExecution


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
        return [StreamEventType.TOOL_CALL]
    
    def on_event(self, event: StreamEvent) -> None:
        """Handle incoming events.
        
        Args:
            event (StreamEvent): The event to handle.
        """
        if event.type == StreamEventType.TOOL_CALL:
            self._handle_tool_call_event(event)
        else:
            self.logger.warning(f"Received unexpected event type: {event.type}")
    
    def _handle_tool_call_event(self, event: StreamEvent) -> None:
        """Handle TOOL_CALL events by dispatching to tool execution.
        
        Args:
            event (StreamEvent): The TOOL_CALL event to handle.
        """
        try:
            # Extract tool call data from event
            tool_id = event.data.get("tool_id", "unknown")
            function_name = event.data.get("function_name", "")
            arguments = event.data.get("arguments", {})
            
            self.logger.info(f"Handling tool call: {function_name} (ID: {tool_id})")
            
            # Optionally publish TOOL_CALL_DISPATCHED event immediately
            if hasattr(self.tool_execution, 'stream_publisher'):
                try:
                    self.tool_execution.stream_publisher.publish(
                        StreamEventType.TOOL_CALL_DISPATCHED,
                        {
                            "tool_id": tool_id,
                            "function_name": function_name,
                            "arguments": arguments,
                            "dispatched_by": "MCPToolCallSubscriber"
                        }
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to publish TOOL_CALL_DISPATCHED event: {e}")
            
            # Note: In a real implementation, this would be an async call
            # For now, we log that the call would be dispatched
            self.logger.debug(f"Would dispatch tool call {function_name} to MCPToolExecution")
            
        except Exception as e:
            self.logger.error(f"Error handling tool call event: {e}")
            
            # Publish error event if possible
            if hasattr(self.tool_execution, 'stream_publisher'):
                try:
                    self.tool_execution.stream_publisher.publish(
                        StreamEventType.TOOL_CALL_ERROR,
                        {
                            "tool_id": event.data.get("tool_id", "unknown"),
                            "function_name": event.data.get("function_name", ""),
                            "error": str(e),
                            "status": "dispatch_error"
                        }
                    )
                except Exception as pub_error:
                    self.logger.error(f"Failed to publish tool call error: {pub_error}")
