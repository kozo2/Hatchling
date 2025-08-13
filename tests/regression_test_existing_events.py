"""Regression test for existing event handling functionality.

This test ensures that existing event types and subscribers continue to work
correctly after adding new MCP-related events.
"""

import sys
import unittest
import logging
import time
from pathlib import Path
from typing import Dict, Any

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_decorators import regression_test

from hatchling.core.llm.event_system import (
    StreamEventType,
    StreamEvent,
    EventPublisher,
    ContentPrinterSubscriber,
    UsageStatsSubscriber,
    ErrorHandlerSubscriber
)

class TestExistingEventHandling(unittest.TestCase):
    """Test suite for existing event handling functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.publisher = EventPublisher()
    
    def tearDown(self):
        """Clean up after each test method."""
        self.publisher.clear_subscribers()
    
    @regression_test
    def test_existing_event_types_still_available(self):
        """Test that all core event types are still available."""
        # Core event types that should exist in the current system
        core_events = [
            "CONTENT", "ROLE", "FINISH", "USAGE", 
            "ERROR", "METADATA", "LLM_TOOL_CALL_REQUEST"
        ]
        
        for event_name in core_events:
            self.assertTrue(hasattr(StreamEventType, event_name),
                          f"Core event type {event_name} is missing")
            
            # Test that the enum value is correct
            event = getattr(StreamEventType, event_name)
            self.assertIsInstance(event, StreamEventType)
    
    @regression_test
    def test_stream_event_creation_still_works(self):
        """Test that StreamEvent creation still works with original events."""
        # Test creating various types of events
        content_event = StreamEvent(
            type=StreamEventType.CONTENT,
            data={"content": "Hello world"},
            provider="test_provider"
        )
        
        self.assertEqual(content_event.type, StreamEventType.CONTENT)
        self.assertEqual(content_event.data["content"], "Hello world")
        self.assertEqual(content_event.provider, "test_provider")
        self.assertIsNotNone(content_event.timestamp)
        
        # Test role event
        role_event = StreamEvent(
            type=StreamEventType.ROLE,
            data={"role": "assistant"},
            provider="test_provider"
        )
        
        self.assertEqual(role_event.type, StreamEventType.ROLE)
        self.assertEqual(role_event.data["role"], "assistant")
    
    @regression_test
    def test_content_printer_subscriber_still_works(self):
        """Test that ContentPrinterSubscriber still works correctly."""
        subscriber = ContentPrinterSubscriber()
        self.publisher.subscribe(subscriber)
        
        # Test subscribed events
        subscribed_events = subscriber.get_subscribed_events()
        self.assertIn(StreamEventType.CONTENT, subscribed_events)
        
        # Test event handling (should not raise exceptions)
        try:
            content_event = StreamEvent(
                type=StreamEventType.CONTENT,
                data={"content": "Test content"},
                provider="test_provider"
            )
            subscriber.on_event(content_event)
            
            # ContentPrinterSubscriber in current implementation only handles CONTENT events
            # and doesn't have include_role attribute - ROLE events are handled differently
            
        except Exception as e:
            self.fail(f"ContentPrinterSubscriber failed to handle events: {e}")
    
    @regression_test
    def test_usage_stats_subscriber_still_works(self):
        """Test that UsageStatsSubscriber still works correctly."""
        subscriber = UsageStatsSubscriber()
        self.publisher.subscribe(subscriber)
        
        # Test subscribed events
        subscribed_events = subscriber.get_subscribed_events()
        self.assertIn(StreamEventType.CONTENT, subscribed_events)
        self.assertIn(StreamEventType.USAGE, subscribed_events)
        self.assertIn(StreamEventType.FINISH, subscribed_events)
        
        # Test event handling (should not raise exceptions)
        try:
            content_event = StreamEvent(
                type=StreamEventType.CONTENT,
                data={"content": "Test content"},
                provider="test_provider"
            )
            subscriber.on_event(content_event)
            
            usage_event = StreamEvent(
                type=StreamEventType.USAGE,
                data={
                    "usage": {
                        "total_tokens": 50,
                        "prompt_tokens": 20,
                        "completion_tokens": 30
                    }
                },
                provider="test_provider"
            )
            subscriber.on_event(usage_event)
            
        except Exception as e:
            self.fail(f"UsageStatsSubscriber failed to handle events: {e}")
    
    @regression_test
    def test_error_handler_subscriber_still_works(self):
        """Test that ErrorHandlerSubscriber still works correctly."""
        subscriber = ErrorHandlerSubscriber()
        self.publisher.subscribe(subscriber)
        
        # Test subscribed events
        subscribed_events = subscriber.get_subscribed_events()
        self.assertIn(StreamEventType.ERROR, subscribed_events)
        
        # Test event handling (should not raise exceptions)
        try:
            error_event = StreamEvent(
                type=StreamEventType.ERROR,
                data={
                    "error": {
                        "type": "TestError",
                        "message": "Test error message"
                    }
                },
                provider="test_provider"
            )
            subscriber.on_event(error_event)
            
        except Exception as e:
            self.fail(f"ErrorHandlerSubscriber failed to handle events: {e}")
    
    @regression_test
    def test_publisher_subscription_system_still_works(self):
        """Test that the publisher subscription system still works."""
        content_subscriber = ContentPrinterSubscriber()
        error_subscriber = ErrorHandlerSubscriber()
        
        # Test subscription
        self.publisher.subscribe(content_subscriber)
        self.publisher.subscribe(error_subscriber)
        
        # Test that subscribers are registered
        self.assertEqual(len(self.publisher._subscribers), 2)
        
        # Test publishing to interested subscribers only
        try:
            # This should reach ContentPrinterSubscriber only
            self.publisher.publish(StreamEventType.CONTENT, {"content": "Test"})
            
            # This should reach ErrorHandlerSubscriber only  
            self.publisher.publish(StreamEventType.ERROR, {
                "error": {"type": "Test", "message": "Test error"}
            })
            
            # This should reach neither (using USAGE instead of non-existent THINKING)
            self.publisher.publish(StreamEventType.USAGE, {"usage": {"total_tokens": 10}})
            
        except Exception as e:
            self.fail(f"Publisher failed to handle event publishing: {e}")
        
        # Test unsubscription
        self.publisher.unsubscribe(content_subscriber)
        self.assertEqual(len(self.publisher._subscribers), 1)
        
        # Test clear subscribers
        self.publisher.clear_subscribers()
        self.assertEqual(len(self.publisher._subscribers), 0)


def run_regression_tests():
    """Run all regression tests for existing event handling.
    
    Returns:
        bool: True if all tests pass, False if any fail.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestExistingEventHandling))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_regression_tests()
    sys.exit(0 if success else 1)
