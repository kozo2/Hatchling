"""Content collector subscriber for gathering streaming response content.

This module provides a subscriber that collects streaming content to allow
legacy APIs to return a complete response string.
"""

import asyncio
from typing import List, Optional

from hatchling.core.llm.streaming_management.stream_data import StreamEvent, StreamEventType
from hatchling.core.llm.streaming_management.stream_subscriber import StreamSubscriber


class ContentAccumulatorSubscriber(StreamSubscriber):
    """Subscriber that collects content for returning complete responses."""
    
    def __init__(self):
        """Initialize content collector."""
        self.full_response = ""
        
    def on_event(self, event: StreamEvent) -> None:
        """Handle content and finish events.
        
        Args:
            event (StreamEvent): The event to handle.
        """
        if event.type == StreamEventType.CONTENT:
            self.full_response += event.data.get("content", "")
    
    def get_subscribed_events(self) -> List[StreamEventType]:
        """Return subscribed event types.
        
        Returns:
            List[StreamEventType]: Event types to subscribe to.
        """
        return [StreamEventType.CONTENT]
    
    def reset(self) -> None:
        """Reset the collector for a new response."""
        self.full_response = ""
