"""Tool result collector subscriber for gathering tool execution results from MCPToolExecution events.

This subscriber listens to tool execution events and collects the results for
processing in tool calling chains and response formatting.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple, Union
from collections import deque

from hatchling.core.logging.logging_manager import logging_manager

from hatchling.core.llm.streaming_management.event_subscriber import EventSubscriber
from hatchling.core.llm.streaming_management.stream_data import StreamEvent, StreamEventType

from hatchling.core.llm.data_structures import ToolCallParsedResult
from hatchling.mcp_utils.mcp_tool_execution import ToolCallExecutionResult

@dataclass
class ToolCallExecutionResultLight:
    """Data class to hold a lightweight representation of a tool call execution result.
    This is typically the structure that will be injected in the message history with
    the LLM.
    """
    tool_call_id: str
    result: str
    role: str = "MCP_TOOL_CALL_RESULT"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the parse result to a dictionary."""
        return {
            "role": self.role,
            "tool_call_id": self.tool_call_id,
            "result": self.result
        }
    
    @classmethod
    def from_execution_result(cls, execution_result: ToolCallExecutionResult) -> 'ToolCallExecutionResultLight':
        """Create a parse result from a ToolCallExecutionResult."""
        return cls(
            tool_call_id=execution_result.tool_call_id,
            result=str(execution_result.result.content[0].text) if execution_result.result and execution_result.result.content else ""
        )



class ToolResultCollectorSubscriber(EventSubscriber):
    """Collects tool execution results from MCPToolExecution events.
    
    This subscriber accumulates tool call results until reset.
    """
    
    def __init__(self):
        """Initialize the tool result collector with FIFO queue and result buffer."""
        # FIFO queue for tool call dispatches: (tool_call_id, timestamp, ToolCallParsedResult)
        self.tool_call_queue = deque()  # Type: deque[Tuple[str, float, ToolCallParsedResult]]
        
        # Buffer for tool results by tool_call_id: tool_call_id -> ToolCallExecutionResult or error marker
        self.tool_result_buffer: Dict[str, ToolCallExecutionResult] = {}

        self.logger = logging_manager.get_session("ToolResultCollectorSubscriber")
    
    def on_event(self, event: StreamEvent) -> None:
        """Handle tool execution events.
        
        Args:
            event (StreamEvent): The event received. The `event.data` must be a dictionary
            matching the data structure of either ToolCallParsedResult or ToolCallExecutionResult:
              - with `event.type` being `StreamEventType.MCP_TOOL_CALL_DISPATCHED`, the `event.data`
              should match the ToolCallParsedResult structure
              - with `event.type` being `StreamEventType.MCP_TOOL_CALL_RESULT`, the `event.data` should
              match the ToolCallExecutionResult structure.
        """        
        try:
            if event.type == StreamEventType.MCP_TOOL_CALL_DISPATCHED:
                # We expect `data` to match the ToolCallParsedResult structure
                toolCallParsedRes = ToolCallParsedResult(**event.data)
                self.logger.debug(f"Tool call dispatched received: {toolCallParsedRes} with request ID {event.request_id}")
                
                # Add to FIFO queue with timestamp
                self.tool_call_queue.append((toolCallParsedRes.tool_call_id, event.timestamp, toolCallParsedRes))
                self.logger.debug(f"Added to FIFO queue. Queue length: {len(self.tool_call_queue)}")

            elif event.type == StreamEventType.MCP_TOOL_CALL_RESULT:
                toolCallExecRes = ToolCallExecutionResult(**event.data)
                self.logger.debug(f"Tool call result received: {toolCallExecRes}")
                
                # if toolCallExecRes ID already in the buffer, log a warning
                if toolCallExecRes.tool_call_id in self.tool_result_buffer:
                    self.logger.warning(f"Tool call result for ID {toolCallExecRes.tool_call_id} already exists in buffer. "
                                        f"Overwriting previous result.")
                # if toolCallExecRes ID is not already in the tool calls, log a warning
                if toolCallExecRes.tool_call_id not in [call.tool_call_id for _, _, call in self.tool_call_queue]:
                    self.logger.warning(f"Tool call result for ID {toolCallExecRes.tool_call_id} received without a matching tool call in the queue. "
                                        f"This may indicate a mismatch in tool call dispatch and result handling.")

                # Store in result buffer
                self.tool_result_buffer[toolCallExecRes.tool_call_id] = toolCallExecRes
                self.logger.debug(f"Added to result buffer. Buffer size: {len(self.tool_result_buffer)}")

            elif event.type == StreamEventType.MCP_TOOL_CALL_ERROR:
                # Handle tool execution error

                error_result = ToolCallExecutionResult(**event.data)
                self.logger.error(f"Tool call error received: {error_result}")
                self.tool_result_buffer[event.data["tool_call_id"]] = error_result
                self.logger.debug(f"Added error to result buffer for tool_call_id: {event.data['tool_call_id']}")
                
        except Exception as e:
            # Don't let subscriber errors break the event system
            pass
    
    def get_next_ready_pair(self) -> Optional[Tuple[ToolCallParsedResult, Union[ToolCallExecutionResult, Dict[str, Any]]]]:
        """Get the next ready (call, result) pair in FIFO order.
        
        Returns the next tool call and its result if available, maintaining strict FIFO order.
        Only the oldest tool call that has a result is returned.
        
        Returns:
            Optional[Tuple[ToolCallParsedResult, Union[ToolCallExecutionResult, Dict[str, Any]]]]: 
            The next ready pair or None if no pair is ready.
        """
        while self.tool_call_queue:
            tool_call_id, timestamp, call = self.tool_call_queue[0]  # Peek at head
            
            if tool_call_id in self.tool_result_buffer:
                # Found a matching result, pop both and return
                result = self.tool_result_buffer.pop(tool_call_id)
                self.tool_call_queue.popleft()
                
                self.logger.debug(f"Returning ready pair for tool_call_id: {tool_call_id} "
                                f"(dispatch timestamp: {timestamp})")
                return (call, result)
            else:
                # Head of queue doesn't have a result yet, nothing is ready
                self.logger.debug(f"Head of queue (tool_call_id: {tool_call_id}) not ready yet. "
                                f"Queue length: {len(self.tool_call_queue)}, "
                                f"Buffer size: {len(self.tool_result_buffer)}")
                break
        
        return None
    
    def get_subscribed_events(self) -> List[StreamEventType]:
        """Get the list of events this subscriber is interested in.
        
        Returns:
            List[StreamEventType]: List of event types to subscribe to.
        """
        return [
            StreamEventType.MCP_TOOL_CALL_DISPATCHED,
            StreamEventType.MCP_TOOL_CALL_RESULT,
            StreamEventType.MCP_TOOL_CALL_ERROR
        ]

    def reset(self) -> None:
        """Reset the collector for a new tool calling session."""
        # Clear new FIFO structures
        self.tool_call_queue.clear()
        self.tool_result_buffer.clear()
        
        self.logger.debug("Reset FIFO queue and result buffer")
   
    @property
    def has_pending_tool_calls(self) -> bool:
        """Check if there are any pending tool calls in the queue.
        
        Returns:
            bool: True if there are pending tool calls, False otherwise.
        """
        return len(self.tool_call_queue) > 0
