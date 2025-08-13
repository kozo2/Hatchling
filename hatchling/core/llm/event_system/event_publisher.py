"""Event publisher implementing the publish-subscribe pattern.

This module provides the core publisher that manages event subscribers
and handles event distribution in the LLM event system.
"""

import logging
from typing import List, Dict, Any, Optional

from .event_data import Event, EventType
from .event_subscriber import EventSubscriber

logger = logging.getLogger(__name__)

class EventPublisher:
    """Publisher for events using the observer pattern."""

    def __init__(self):
        """Initialize the publisher."""
        self._subscribers: List[EventSubscriber] = []
        self._active_request_id: Optional[str] = None
    
    def subscribe(self, subscriber: EventSubscriber) -> None:
        """Subscribe to events.
        
        Args:
            subscriber (EventSubscriber): Subscriber to add.
        """
        if subscriber not in self._subscribers:
            self._subscribers.append(subscriber)
            logger.debug(f"Added subscriber for events: {subscriber.get_subscribed_events()}")
    
    def unsubscribe(self, subscriber: EventSubscriber) -> None:
        """Unsubscribe from events.
        
        Args:
            subscriber (EventSubscriber): Subscriber to remove.
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
    
    def publish(self, event_type: EventType, data: Dict[str, Any]) -> None:
        """Publish an event to all interested subscribers.
        
        Args:
            event_type (EventType): Type of event to publish.
            data (Dict[str, Any]): Event data.
        """
        from hatchling.core.llm.providers import ProviderRegistry
        
        event = Event(
            type=event_type,
            data=data,
            provider=ProviderRegistry.get_current_provider().provider_enum,
            request_id=self._active_request_id
        )
        
        for subscriber in self._subscribers:
            if event_type in subscriber.get_subscribed_events():
                try:
                    subscriber.on_event(event)
                except Exception as e:
                    logger.error(f"Error notifying subscriber: {e}")
