"""Event subscriber implementations for LLM system.

This module provides example implementation of subscribers.
They are mainly used in the tests, and are not flexible enough
for production code.
"""

import logging
from typing import Callable, List

from .event_data import Event, EventType
from .event_subscriber import EventSubscriber

logger = logging.getLogger(__name__)

class CallableSubscriber(EventSubscriber):
    """A subscriber that wraps a callable function."""
    
    def __init__(self, callback: Callable[[Event], None], event_types: List[EventType]):
        """Initialize callable subscriber.
        
        Args:
            callback (Callable[[Event], None]): Function to call on events.
            event_types (List[EventType]): Event types to subscribe to.
        """
        self.callback = callback
        self.event_types = event_types
    
    def on_event(self, event: Event) -> None:
        """Handle event by calling the callback function.
        
        Args:
            event (Event): The event to handle.
        """
        try:
            self.callback(event)
        except Exception as e:
            logger.error(f"Error in callback subscriber: {e}")
    
    def get_subscribed_events(self) -> List[EventType]:
        """Return subscribed event types.
        
        Returns:
            List[EventType]: Event types to subscribe to.
        """
        return self.event_types

class ContentPrinterSubscriber(EventSubscriber):
    """Subscriber that prints content to console as it arrives."""
    
    def __init__(self):
        """Initialize content printer."""
        self._first_content = True
    
    def on_event(self, event: Event) -> None:
        """Handle content and role events.
        
        Args:
            event (Event): The event to handle.
        """
        if event.type == EventType.CONTENT:
            content = event.data.get("content", "")
            print(content, end="", flush=True)
        elif event.type == EventType.ROLE and self.include_role:
            role = event.data.get("role", "")
            if self._first_content:
                print(f"[{role}] ", end="", flush=True)
                self._first_content = False
    
    def get_subscribed_events(self) -> List[EventType]:
        """Return subscribed event types.
        
        Returns:
            List[EventType]: Event types to subscribe to.
        """
        return [EventType.CONTENT]
    
class ContentAccumulatorSubscriber(EventSubscriber):
    """Subscriber that collects content for returning complete responses."""
    
    def __init__(self):
        """Initialize content collector."""
        self.full_response = ""
        
    def on_event(self, event: Event) -> None:
        """Handle content and finish events.
        
        Args:
            event (Event): The event to handle.
        """
        if event.type == EventType.CONTENT:
            self.full_response += event.data.get("content", "")
    
    def get_subscribed_events(self) -> List[EventType]:
        """Return subscribed event types.
        
        Returns:
            List[EventType]: Event types to subscribe to.
        """
        return [EventType.CONTENT]
    
    def reset(self) -> None:
        """Reset the collector for a new response."""
        self.full_response = ""


class UsageStatsSubscriber(EventSubscriber):
    """Subscriber that tracks and reports usage statistics."""
    
    def __init__(self):
        """Initialize usage stats subscriber."""
        self.total_tokens = 0
        self.total_current = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.start_time = None
        self.end_time = None
    
    def on_event(self, event: Event) -> None:
        """Handle usage and timing events.
        
        Args:
            event (Event): The event to handle.
        """
        if event.type == EventType.CONTENT and self.start_time is None:
            # Record start time on first content
            self.start_time = event.timestamp
        elif event.type == EventType.USAGE:
            # Record final usage stats
            usage_data = event.data.get("usage", {})
            self.total_current = usage_data.get("total_tokens", 0)
            self.total_tokens += self.total_current
            self.prompt_tokens = usage_data.get("prompt_tokens", 0)
            self.completion_tokens = usage_data.get("completion_tokens", 0)
            self._print_stats()
            self.start_time = None  # Reset for next session
            self.end_time = None  # Reset for next session
        elif event.type == EventType.FINISH and self.start_time and not self.end_time:
            # If no usage event, record end time on finish
            self.end_time = event.timestamp
    
    def _print_stats(self) -> None:
        """Print usage statistics and generation rate."""
        print(f"\n\n=== Usage Statistics ===")
        print(f"Query tokens: {self.total_current} (in: {self.prompt_tokens} | out: {self.completion_tokens})")
        print(f"Total tokens: {self.total_tokens}")
        if self.start_time and self.end_time and self.completion_tokens > 0:
            duration = self.end_time - self.start_time
            tokens_per_second = self.completion_tokens / duration if duration > 0 else 0
            print(f"Query time: {duration:.2f} seconds ({tokens_per_second:.2f} TPS)")
        print("========================")
    
    def get_subscribed_events(self) -> List[EventType]:
        """Return subscribed event types.
        
        Returns:
            List[EventType]: Event types to subscribe to.
        """
        return [EventType.CONTENT, EventType.USAGE, EventType.FINISH]


class ErrorHandlerSubscriber(EventSubscriber):
    """Subscriber that handles and reports errors."""
    
    def on_event(self, event: Event) -> None:
        """Handle error events.
        
        Args:
            event (Event): The event to handle.
        """
        if event.type == EventType.ERROR:
            error_data = event.data.get("error", {})
            message = error_data.get("message", "Unknown error")
            error_type = error_data.get("type", "Unknown")
            print(f"\n\nEvent Error ({error_type}): {message}")
    
    def get_subscribed_events(self) -> List[EventType]:
        """Return subscribed event types.
        
        Returns:
            List[EventType]: Event types to subscribe to.
        """
        return [EventType.ERROR]
