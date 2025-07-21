
import logging
from typing import List
from abc import ABC, abstractmethod

from .stream_data import StreamEvent, StreamEventType

logger = logging.getLogger(__name__)

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
