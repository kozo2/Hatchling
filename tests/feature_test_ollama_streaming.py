"""Test suite for Ollama provider publish-subscribe chunk parsing.

This module tests the Ollama provider's ability to parse streaming chunks
and publish events to subscribers using the publish-subscribe pattern.
"""
import sys
import logging
import unittest

from tests.test_decorators import feature_test

from hatchling.config.llm_settings import ELLMProvider
from hatchling.config.settings import AppSettings
from hatchling.config.ollama_settings import OllamaSettings
from hatchling.core.llm.providers import ProviderRegistry
from hatchling.core.llm.event_system import (
    EventPublisher,
    ContentPrinterSubscriber,
    UsageStatsSubscriber,
    ErrorHandlerSubscriber
)


class TestOllamaChunkParsing(unittest.TestCase):
    """Test suite for Ollama provider publish-subscribe chunk parsing."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create proper AppSettings for testing
        ollama_settings = OllamaSettings(
            ip="localhost",
            port=11434
        )
        self.test_settings = AppSettings(ollama=ollama_settings)
        
        # Create provider with proper settings
        self.provider = ProviderRegistry.create_provider(ELLMProvider.OLLAMA, self.test_settings)
        
        # Mock Ollama response chunks based on actual Ollama streaming format
        self.mock_chunks = [
            # Initial role chunk
            {
                "model": "llama3.2:latest",
                "created_at": "2024-01-01T12:00:00Z",
                "message": {
                    "role": "assistant",
                    "content": ""
                },
                "done": False
            },
            # Content chunks
            {
                "model": "llama3.2:latest", 
                "created_at": "2024-01-01T12:00:01Z",
                "message": {
                    "role": "assistant",
                    "content": "Hello"
                },
                "done": False
            },
            {
                "model": "llama3.2:latest",
                "created_at": "2024-01-01T12:00:02Z", 
                "message": {
                    "role": "assistant",
                    "content": " world"
                },
                "done": False
            },
            {
                "model": "llama3.2:latest",
                "created_at": "2024-01-01T12:00:03Z",
                "message": {
                    "role": "assistant", 
                    "content": "!"
                },
                "done": False
            },
            # Final chunk with usage stats
            {
                "model": "llama3.2:latest",
                "created_at": "2024-01-01T12:00:04Z",
                "message": {
                    "role": "assistant",
                    "content": ""
                },
                "done": True,
                "total_duration": 4750000000,
                "load_duration": 125000000,
                "prompt_eval_count": 10,
                "prompt_eval_duration": 250000000,
                "eval_count": 3,
                "eval_duration": 375000000
            }
        ]
    
    def tearDown(self):
        """Clean up after each test method."""
        if hasattr(self.provider, 'publisher'):
            self.provider.publisher.clear_subscribers()
        self.provider = None
    
    @feature_test
    def test_ollama_chunk_parsing_with_subscribers(self):
        """Test Ollama chunk parsing with publish-subscribe pattern."""
        # Create test subscribers
        content_printer = ContentPrinterSubscriber()
        usage_stats = UsageStatsSubscriber()
        error_handler = ErrorHandlerSubscriber()

        # Subscribe to publisher
        self.provider.publisher.subscribe(content_printer)
        self.provider.publisher.subscribe(usage_stats)
        self.provider.publisher.subscribe(error_handler)
        
        print("Testing Ollama chunk parsing with subscribers...")
        print("=" * 50)
        
        # Test chunk parsing
        parsed_chunks = []
        for i, chunk in enumerate(self.mock_chunks):
            print(f"\nProcessing chunk {i+1}:")
            self.provider._parse_and_publish_chunk(chunk)
        
        print("\n" + "=" * 50)
        print("Test completed successfully!")

    @feature_test 
    def test_ollama_chunk_parsing_error_handling(self):
        """Test error handling in Ollama chunk parsing."""
        error_handler = ErrorHandlerSubscriber()
        self.provider.publisher.subscribe(error_handler)

        # Test with None chunk
        try:
            self.provider._parse_and_publish_chunk(None)
        except Exception as e:
            self.fail(f"Should not raise exception for None chunk: {e}")
        
        print("Error handling test completed successfully")

def run_ollama_chunk_parsing_tests():
    """Run all Ollama chunk parsing tests.
    
    Returns:
        bool: True if all tests pass or are skipped, False if any fail.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestOllamaChunkParsing))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Consider skipped tests as success for integration tests
    return result.wasSuccessful()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_ollama_chunk_parsing_tests()
    sys.exit(0 if success else 1)