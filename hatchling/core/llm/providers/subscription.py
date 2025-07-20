"""Publisher-Subscriber pattern for LLM streaming responses.

This module provides a flexible publish-subscribe system that allows different
components to subscribe to specific events from LLM streaming responses.
"""

import logging
from typing import Dict, Any, Callable, List, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class StreamEventType(Enum):
    """Types of events that can be published during streaming."""
    
    # LLM Response Events
    CONTENT = "content"              # Text content from the model
    ROLE = "role"                   # Role assignment (assistant, user, etc.)
    TOOL_CALL = "tool_call"         # Tool/function call
    FINISH = "finish"               # Stream completion with reason
    USAGE = "usage"                 # Token usage statistics
    ERROR = "error"                 # Error occurred during streaming
    REFUSAL = "refusal"            # Model refused to answer
    THINKING = "thinking"          # Model thinking process (for reasoning models)
    METADATA = "metadata"          # Additional metadata (fingerprint, etc.)
    
    # MCP Lifecycle Events
    MCP_SERVER_UP = "mcp_server_up"                    # MCP server connection established
    MCP_SERVER_DOWN = "mcp_server_down"                # MCP server connection lost
    MCP_SERVER_UNREACHABLE = "mcp_server_unreachable"  # MCP server cannot be reached
    MCP_SERVER_REACHABLE = "mcp_server_reachable"      # MCP server became reachable again
    MCP_TOOL_ENABLED = "mcp_tool_enabled"              # MCP tool was enabled
    MCP_TOOL_DISABLED = "mcp_tool_disabled"            # MCP tool was disabled
    
    # Tool Execution Events
    TOOL_CALL_DISPATCHED = "tool_call_dispatched"      # Tool call was dispatched for execution
    TOOL_CALL_RESULT = "tool_call_result"              # Tool call completed with result
    TOOL_CALL_PROGRESS = "tool_call_progress"          # Tool call progress update
    TOOL_CALL_ERROR = "tool_call_error"                # Tool call failed with error


class MCPToolStatus(Enum):
    """Status of an MCP tool in the lifecycle management system."""
    
    ENABLED = "enabled"      # Tool is available for use
    DISABLED = "disabled"    # Tool is not available for use


class MCPToolStatusReason(Enum):
    """Reasons why an MCP tool has a particular status."""
    
    # Enabled reasons
    FROM_SERVER_UP = "server_up"              # Tool enabled because server came online
    FROM_USER_ENABLED = "user_enabled"        # Tool explicitly enabled by user
    FROM_SERVER_REACHABLE = "server_reachable"  # Tool enabled because server became reachable
    
    # Disabled reasons  
    FROM_SERVER_DOWN = "server_down"          # Tool disabled because server went down
    FROM_SERVER_UNREACHABLE = "unreachable"  # Tool disabled because server is unreachable
    FROM_USER_DISABLED = "user_disabled"     # Tool explicitly disabled by user
    FROM_SYSTEM_ERROR = "system_error"       # Tool disabled due to system error


@dataclass
class MCPToolInfo:
    """Information about an MCP tool in the lifecycle management system."""
    
    name: str                           # Tool name
    description: str                    # Tool description  
    schema: Dict[str, Any]             # Tool schema/definition
    server_path: str                   # Path to the MCP server providing this tool
    status: MCPToolStatus              # Current status (enabled/disabled)
    reason: MCPToolStatusReason        # Reason for current status
    provider_format: Optional[Dict[str, Any]] = None  # Cached provider-specific format
    last_updated: Optional[float] = None              # Timestamp of last status update
    
    def __post_init__(self):
        """Set last_updated timestamp if not provided."""
        if self.last_updated is None:
            import time
            self.last_updated = time.time()


@dataclass
class StreamEvent:
    """Represents an event in the streaming response.
    
    This standardized event format allows different LLM providers to publish
    events in a consistent way, regardless of their native response format.
    """
    
    type: StreamEventType
    data: Dict[str, Any]
    provider: str
    request_id: Optional[str] = None
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            import time
            self.timestamp = time.time()


class StreamSubscriber(ABC):
    """Abstract base class for stream event subscribers."""
    
    @abstractmethod
    def on_event(self, event: StreamEvent) -> None:
        """Handle a stream event.
        
        Args:
            event (StreamEvent): The event to handle.
        """
        pass
    
    @abstractmethod
    def get_subscribed_events(self) -> List[StreamEventType]:
        """Return list of event types this subscriber is interested in.
        
        Returns:
            List[StreamEventType]: Event types to subscribe to.
        """
        pass


class CallableSubscriber(StreamSubscriber):
    """A subscriber that wraps a callable function."""
    
    def __init__(self, callback: Callable[[StreamEvent], None], event_types: List[StreamEventType]):
        """Initialize callable subscriber.
        
        Args:
            callback (Callable[[StreamEvent], None]): Function to call on events.
            event_types (List[StreamEventType]): Event types to subscribe to.
        """
        self.callback = callback
        self.event_types = event_types
    
    def on_event(self, event: StreamEvent) -> None:
        """Handle event by calling the callback function.
        
        Args:
            event (StreamEvent): The event to handle.
        """
        try:
            self.callback(event)
        except Exception as e:
            logger.error(f"Error in callback subscriber: {e}")
    
    def get_subscribed_events(self) -> List[StreamEventType]:
        """Return subscribed event types.
        
        Returns:
            List[StreamEventType]: Event types to subscribe to.
        """
        return self.event_types


class StreamPublisher:
    """Publisher for streaming events using the observer pattern."""
    
    def __init__(self, provider_name: str):
        """Initialize the publisher.
        
        Args:
            provider_name (str): Name of the LLM provider publishing events.
        """
        self.provider_name = provider_name
        self._subscribers: List[StreamSubscriber] = []
        self._active_request_id: Optional[str] = None
    
    def subscribe(self, subscriber: StreamSubscriber) -> None:
        """Subscribe to stream events.
        
        Args:
            subscriber (StreamSubscriber): Subscriber to add.
        """
        if subscriber not in self._subscribers:
            self._subscribers.append(subscriber)
            logger.debug(f"Added subscriber for events: {subscriber.get_subscribed_events()}")
    
    def unsubscribe(self, subscriber: StreamSubscriber) -> None:
        """Unsubscribe from stream events.
        
        Args:
            subscriber (StreamSubscriber): Subscriber to remove.
        """
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)
            logger.debug("Removed subscriber")
    
    def clear_subscribers(self) -> None:
        """Remove all subscribers."""
        self._subscribers.clear()
        logger.debug("Cleared all subscribers")
    
    def set_request_id(self, request_id: str) -> None:
        """Set the current request ID for published events.
        
        Args:
            request_id (str): ID for the current request.
        """
        self._active_request_id = request_id
    
    def publish(self, event_type: StreamEventType, data: Dict[str, Any]) -> None:
        """Publish an event to all interested subscribers.
        
        Args:
            event_type (StreamEventType): Type of event to publish.
            data (Dict[str, Any]): Event data.
        """
        event = StreamEvent(
            type=event_type,
            data=data,
            provider=self.provider_name,
            request_id=self._active_request_id
        )
        
        for subscriber in self._subscribers:
            if event_type in subscriber.get_subscribed_events():
                try:
                    subscriber.on_event(event)
                except Exception as e:
                    logger.error(f"Error notifying subscriber: {e}")


# Common subscriber implementations

class ContentPrinterSubscriber(StreamSubscriber):
    """Subscriber that prints content to console as it arrives."""
    
    def __init__(self, include_role: bool = False):
        """Initialize content printer.
        
        Args:
            include_role (bool): Whether to print role information.
        """
        self.include_role = include_role
        self._first_content = True
    
    def on_event(self, event: StreamEvent) -> None:
        """Handle content and role events.
        
        Args:
            event (StreamEvent): The event to handle.
        """
        if event.type == StreamEventType.CONTENT:
            content = event.data.get("content", "")
            print(content, end="", flush=True)
        elif event.type == StreamEventType.ROLE and self.include_role:
            role = event.data.get("role", "")
            if self._first_content:
                print(f"[{role}] ", end="", flush=True)
                self._first_content = False
    
    def get_subscribed_events(self) -> List[StreamEventType]:
        """Return subscribed event types.
        
        Returns:
            List[StreamEventType]: Event types to subscribe to.
        """
        events = [StreamEventType.CONTENT]
        if self.include_role:
            events.append(StreamEventType.ROLE)
        return events


class UsageStatsSubscriber(StreamSubscriber):
    """Subscriber that tracks and reports usage statistics."""
    
    def __init__(self):
        """Initialize usage stats subscriber."""
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.start_time = None
        self.end_time = None
    
    def on_event(self, event: StreamEvent) -> None:
        """Handle usage and timing events.
        
        Args:
            event (StreamEvent): The event to handle.
        """
        if event.type == StreamEventType.CONTENT and self.start_time is None:
            # Record start time on first content
            self.start_time = event.timestamp
        elif event.type == StreamEventType.USAGE:
            # Record final usage stats
            usage_data = event.data.get("usage", {})
            self.total_tokens = usage_data.get("total_tokens", 0)
            self.prompt_tokens = usage_data.get("prompt_tokens", 0)
            self.completion_tokens = usage_data.get("completion_tokens", 0)
            self.end_time = event.timestamp
            self._print_stats()
        elif event.type == StreamEventType.FINISH and self.start_time and not self.end_time:
            # If no usage event, record end time on finish
            self.end_time = event.timestamp
            self._print_stats()
    
    def _print_stats(self) -> None:
        """Print usage statistics and generation rate."""
        print(f"\n\n=== Usage Statistics ===")
        print(f"Total tokens: {self.total_tokens}")
        print(f"Prompt tokens: {self.prompt_tokens}")
        print(f"Completion tokens: {self.completion_tokens}")
        
        if self.start_time and self.end_time and self.completion_tokens > 0:
            duration = self.end_time - self.start_time
            tokens_per_second = self.completion_tokens / duration if duration > 0 else 0
            print(f"Generation time: {duration:.2f} seconds")
            print(f"Generation rate: {tokens_per_second:.2f} tokens/second")
        print("========================")
    
    def get_subscribed_events(self) -> List[StreamEventType]:
        """Return subscribed event types.
        
        Returns:
            List[StreamEventType]: Event types to subscribe to.
        """
        return [StreamEventType.CONTENT, StreamEventType.USAGE, StreamEventType.FINISH]


class ErrorHandlerSubscriber(StreamSubscriber):
    """Subscriber that handles and reports errors."""
    
    def on_event(self, event: StreamEvent) -> None:
        """Handle error events.
        
        Args:
            event (StreamEvent): The event to handle.
        """
        if event.type == StreamEventType.ERROR:
            error_data = event.data.get("error", {})
            message = error_data.get("message", "Unknown error")
            error_type = error_data.get("type", "Unknown")
            print(f"\n\nStreaming Error ({error_type}): {message}")
        elif event.type == StreamEventType.REFUSAL:
            refusal = event.data.get("refusal", "")
            print(f"\n\nModel refused: {refusal}")
    
    def get_subscribed_events(self) -> List[StreamEventType]:
        """Return subscribed event types.
        
        Returns:
            List[StreamEventType]: Event types to subscribe to.
        """
        return [StreamEventType.ERROR, StreamEventType.REFUSAL]
