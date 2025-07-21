"""Publisher-Subscriber pattern for LLM streaming responses.

This module provides a flexible publish-subscribe system that allows different
components to subscribe to specific events from LLM streaming responses.
"""

import logging
from typing import Callable, List

from .stream_data import StreamEvent, StreamEventType
from .stream_subscriber import StreamSubscriber

logger = logging.getLogger(__name__)

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