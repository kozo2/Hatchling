"""
Test data utilities for loading reusable test fixtures.

This module provides utilities for loading test configurations, mock responses,
event payloads, and other test data from the test_data directory.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List


class TestDataLoader:
    """Utility class for loading test data from standardized locations."""
    
    def __init__(self):
        """Initialize the test data loader."""
        self.test_data_dir = Path(__file__).parent / "test_data"
        self.configs_dir = self.test_data_dir / "configs"
        self.responses_dir = self.test_data_dir / "responses" 
        self.events_dir = self.test_data_dir / "events"
        self.servers_dir = self.test_data_dir / "servers"
    
    def load_config(self, config_name: str) -> Dict[str, Any]:
        """Load a test configuration file.
        
        Args:
            config_name: Name of the config file (without .json extension)
            
        Returns:
            Loaded configuration as a dictionary
        """
        config_path = self.configs_dir / f"{config_name}.json"
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def load_response(self, response_name: str) -> Dict[str, Any]:
        """Load a mock response file.
        
        Args:
            response_name: Name of the response file (without .json extension)
            
        Returns:
            Loaded response data as a dictionary
        """
        response_path = self.responses_dir / f"{response_name}.json"
        with open(response_path, 'r') as f:
            return json.load(f)
    
    def load_events(self, event_name: str) -> Dict[str, Any]:
        """Load event payload data.
        
        Args:
            event_name: Name of the event file (without .json extension)
            
        Returns:
            Loaded event data as a dictionary
        """
        event_path = self.events_dir / f"{event_name}.json"
        with open(event_path, 'r') as f:
            return json.load(f)
    
    def get_server_path(self, server_name: str) -> str:
        """Get the path to a test MCP server.
        
        Args:
            server_name: Name of the server file (without .py extension)
            
        Returns:
            Absolute path to the server file
        """
        server_path = self.servers_dir / f"{server_name}.py"
        return str(server_path.absolute())
    
    def get_ollama_streaming_events(self) -> List[Dict[str, Any]]:
        """Get sample Ollama streaming events."""
        events = self.load_events("ollama_streaming")
        return events["ollama_streaming_events"]
    
    def get_tool_call_events(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get sample tool call events for different providers."""
        return self.load_events("tool_calls")
    
    def get_api_responses(self) -> Dict[str, Any]:
        """Get sample API responses."""
        return self.load_response("api_responses")
    
    def get_test_settings(self) -> Dict[str, Any]:
        """Get default test settings configuration."""
        return self.load_config("test_settings")
    
    def get_openai_test_settings(self) -> Dict[str, Any]:
        """Get OpenAI-specific test settings."""
        return self.load_config("openai_test_settings")


# Global instance for easy access
test_data = TestDataLoader()
