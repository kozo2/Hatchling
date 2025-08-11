"""Test script for OpenAI chunk parsing functionality with Publish-Subscribe pattern.

This script demonstrates how the enhanced publish-subscribe chunk parsing works with
real ChatCompletionChunk data.
"""

import sys
import os
import unittest
import logging

from openai.types.chat import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice, ChoiceDelta
from openai.types import CompletionUsage
from openai.types.completion_usage import CompletionTokensDetails, PromptTokensDetails

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from hatchling.core.llm.providers.openai_provider import OpenAIProvider
from hatchling.core.llm.streaming_management import (
    StreamPublisher,
    ContentPrinterSubscriber, 
    UsageStatsSubscriber, 
    ErrorHandlerSubscriber
)

logging.basicConfig(level=logging.DEBUG)


def create_test_chunks():
    """Create test chunks based on the debug data."""
    
    # First chunk - role assignment
    chunk1 = ChatCompletionChunk(
        id='chatcmpl-Bv52g8HyZYqQkVQ54gOmopBRE0hLp',
        choices=[Choice(
            delta=ChoiceDelta(
                content='',
                function_call=None,
                refusal=None,
                role='assistant',
                tool_calls=None
            ),
            finish_reason=None,
            index=0,
            logprobs=None
        )],
        created=1752943778,
        model='gpt-4.1-nano-2025-04-14',
        object='chat.completion.chunk',
        service_tier='default',
        system_fingerprint=None,
        usage=None
    )
    
    # Content chunks
    content_chunks = [
        ('Hello', None),
        (',', None),
        (' how', None),
        (' are', None),
        ('?', None)
    ]
    
    chunks = [chunk1]
    
    for content, finish_reason in content_chunks:
        chunk = ChatCompletionChunk(
            id='chatcmpl-Bv52g8HyZYqQkVQ54gOmopBRE0hLp',
            choices=[Choice(
                delta=ChoiceDelta(
                    content=content,
                    function_call=None,
                    refusal=None,
                    role=None,
                    tool_calls=None
                ),
                finish_reason=finish_reason,
                index=0,
                logprobs=None
            )],
            created=1752943778,
            model='gpt-4.1-nano-2025-04-14',
            object='chat.completion.chunk',
            service_tier='default',
            system_fingerprint=None,
            usage=None
        )
        chunks.append(chunk)
    
    # Final chunk with finish_reason
    final_chunk = ChatCompletionChunk(
        id='chatcmpl-Bv52g8HyZYqQkVQ54gOmopBRE0hLp',
        choices=[Choice(
            delta=ChoiceDelta(
                content=None,
                function_call=None,
                refusal=None,
                role=None,
                tool_calls=None
            ),
            finish_reason='stop',
            index=0,
            logprobs=None
        )],
        created=1752943778,
        model='gpt-4.1-nano-2025-04-14',
        object='chat.completion.chunk',
        service_tier='default',
        system_fingerprint=None,
        usage=None
    )
    chunks.append(final_chunk)
    
    # Usage chunk (final)
    usage_chunk = ChatCompletionChunk(
        id='chatcmpl-Bv52g8HyZYqQkVQ54gOmopBRE0hLp',
        choices=[],
        created=1752943778,
        model='gpt-4.1-nano-2025-04-14',
        object='chat.completion.chunk',
        service_tier='default',
        system_fingerprint=None,
        usage=CompletionUsage(
            completion_tokens=5,
            prompt_tokens=15,
            total_tokens=20,
            completion_tokens_details=CompletionTokensDetails(
                accepted_prediction_tokens=0,
                audio_tokens=0,
                reasoning_tokens=0,
                rejected_prediction_tokens=0
            ),
            prompt_tokens_details=PromptTokensDetails(
                audio_tokens=0,
                cached_tokens=0
            )
        )
    )
    chunks.append(usage_chunk)
    
    return chunks


class TestOpenAIChunkParsing(unittest.TestCase):
    """Test suite for OpenAI provider publish-subscribe chunk parsing."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.config = {
            "api_key": "dummy-key",  # Won't be used for parsing test
            "model": "gpt-4-1-nano"
        }
        self.provider = OpenAIProvider(self.config)

        # Mocking the provider's initialize. Only focus on the stream publisher
        self.provider._stream_publisher = StreamPublisher()

        self.chunks = create_test_chunks()
    
    def tearDown(self):
        """Clean up after each test method."""
        self.provider.publisher.clear_subscribers()
        self.provider = None
    
    def test_chunk_parsing_with_subscribers(self):
        """Test the publish-subscribe chunk parsing functionality."""
        # Set up subscribers
        content_printer = ContentPrinterSubscriber(include_role=True)
        usage_stats = UsageStatsSubscriber()
        error_handler = ErrorHandlerSubscriber()
        
        # Subscribe to events
        self.provider.publisher.subscribe(content_printer)
        self.provider.publisher.subscribe(usage_stats)
        self.provider.publisher.subscribe(error_handler)
        
        print("Testing publish-subscribe chunk parsing...")
        print("=" * 50)
        
        # Process all chunks
        for i, chunk in enumerate(self.chunks):
            print(f"\nProcessing chunk {i + 1}...")
            self.provider._parse_and_publish_chunk(chunk)
        
        print("\n" + "=" * 50)
        print("Test completed successfully!")
    
    def test_chunk_parsing_error_handling(self):
        """Test error handling in chunk parsing."""
        error_handler = ErrorHandlerSubscriber()
        self.provider.publisher.subscribe(error_handler)
        
        # Test with None chunk
        try:
            self.provider._parse_and_publish_chunk(None)
        except Exception as e:
            self.fail(f"Should not raise exception for None chunk: {e}")


def run_openai_chunk_parsing_tests():
    """Run all OpenAI integration tests.
    
    Returns:
        bool: True if all tests pass or are skipped, False if any fail.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestOpenAIChunkParsing))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Consider skipped tests as success for integration tests
    return result.wasSuccessful()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_openai_chunk_parsing_tests()
    sys.exit(0 if success else 1)