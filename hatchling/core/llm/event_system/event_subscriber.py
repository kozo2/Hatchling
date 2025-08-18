"""Abstract base class for event subscribers.

This module defines the interface that all event subscribers must implement
to participate in the publish-subscribe event system.
"""

import logging
from typing import List
from abc import ABC, abstractmethod

from .event_data import Event, EventType

logger = logging.getLogger(__name__)

class EventSubscriber(ABC):
    """Abstract base class for event subscribers."""
    
    @abstractmethod
    def on_event(self, event: Event) -> None:
        """Handle an event.
        
        Args:
            event (Event): The event to handle.
        """
        pass
    
    @abstractmethod
    def get_subscribed_events(self) -> List[EventType]:
        """Return list of event types this subscriber is interested in.
        
        Returns:
            List[EventType]: Event types to subscribe to.
        """
        pass
