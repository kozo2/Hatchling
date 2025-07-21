
import logging
from typing import List, Dict, Any, Optional

from .stream_data import StreamEvent, StreamEventType
from .stream_subscriber import StreamSubscriber

from hatchling.config.llm_settings import ELLMProvider

logger = logging.getLogger(__name__)

class StreamPublisher:
    """Publisher for streaming events using the observer pattern."""

    def __init__(self, provider: ELLMProvider):
        """Initialize the publisher.
        
        Args:
            provider (ELLMProvider): The LLM provider publishing events.
        """
        self.provider = provider
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
            provider=self.provider,
            request_id=self._active_request_id
        )
        
        for subscriber in self._subscribers:
            if event_type in subscriber.get_subscribed_events():
                try:
                    subscriber.on_event(event)
                except Exception as e:
                    logger.error(f"Error notifying subscriber: {e}")

