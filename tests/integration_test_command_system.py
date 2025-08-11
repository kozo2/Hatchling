"""Integration tests for the new command system.

These tests validate the complete command system integration including:
1. Command registration and discovery
2. Dynamic argument parsing
3. MCP and Model command execution
4. Command completion and validation
"""

import sys
import unittest
import logging
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from io import StringIO
from contextlib import redirect_stdout

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hatchling.core.chat.mcp_commands import MCPCommands
from hatchling.core.chat.model_commands import ModelCommands
from hatchling.core.chat.chat_command_handler import ChatCommandHandler
from hatchling.core.llm.chat_session import ChatSession
from hatchling.config.settings_registry import SettingsRegistry
from hatchling.mcp_utils.mcp_tool_data import MCPToolInfo, MCPToolStatus, MCPToolStatusReason
from prompt_toolkit.styles import Style


class MockEnvironmentManager:
    """Mock environment manager for testing."""
    
    def get_current_environment(self):
        return "test_env"
    
    def get_servers_entry_points(self, env_name):
        return ["/path/to/test/server.py"]


class MockSettings:
    """Mock settings for testing."""
    
    def __init__(self):
        self.llm = MagicMock()
        self.llm.provider_name = "openai"
        self.llm.model = "gpt-4"


class AsyncTestCase(unittest.TestCase):
    """Base test case with async support."""
    
    def run_async(self, async_test):
        """Helper to run async tests."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(async_test)
        finally:
            loop.close()


class TestCommandSystemIntegration(AsyncTestCase):
    """Integration tests for the command system."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock settings registry
        self.mock_settings_registry = MagicMock()
        self.mock_settings_registry.settings = MockSettings()
        
        # Mock environment manager
        self.mock_env_manager = MockEnvironmentManager()
        
        # Mock chat session
        self.mock_chat_session = MagicMock(spec=ChatSession)
        
        # Create command style
        self.command_style = Style.from_dict({
            'command.name': 'bold #44ff00',
            'command.description': "#ffffff",
        })
        
        # Initialize command handler
        self.cmd_handler = ChatCommandHandler(
            self.mock_chat_session, 
            self.mock_settings_registry, 
            self.command_style
        )
        
        # Setup logging
        self.logger = logging.getLogger("test_command_system")
        self.logger.setLevel(logging.DEBUG)
    
    def test_command_handler_initialization(self):
        """Test that command handler initializes correctly."""
        # Verify command handler has both command types
        self.assertIsInstance(self.cmd_handler.mcp_commands, MCPCommands)
        self.assertIsInstance(self.cmd_handler.model_commands, ModelCommands)
        
        # Verify command collections are populated
        mcp_commands = self.cmd_handler.mcp_commands.commands
        model_commands = self.cmd_handler.model_commands.commands
        
        self.assertGreater(len(mcp_commands), 0, "MCP commands should be registered")
        self.assertGreater(len(model_commands), 0, "Model commands should be registered")
        
        # Log available commands for debugging
        self.logger.info(f"Available MCP commands: {list(mcp_commands.keys())}")
        self.logger.info(f"Available Model commands: {list(model_commands.keys())}")
        
        # Verify all MCP commands follow colon naming convention
        for cmd_name in mcp_commands.keys():
            self.assertTrue(cmd_name.startswith('mcp:'), f"MCP command {cmd_name} should start with 'mcp:'")
            self.assertIn(':', cmd_name, f"Command {cmd_name} should use colon separator")
        
        # Verify model commands exist (naming convention may vary)
        for cmd_name in model_commands.keys():
            self.assertIn(':', cmd_name, f"Command {cmd_name} should use colon separator")
    
    def test_mcp_command_structure(self):
        """Test MCP command structure and validation."""
        mcp_commands = self.cmd_handler.mcp_commands.commands
        
        # Expected MCP commands
        expected_commands = [
            'mcp:server:list',
            'mcp:server:status', 
            'mcp:server:connect',
            'mcp:server:disconnect',
            'mcp:tool:list',
            'mcp:tool:info',
            'mcp:tool:enable',
            'mcp:tool:disable',
            'mcp:tool:execute',
            'mcp:tool:schema',
            'mcp:health',
            'mcp:citations',
            'mcp:reset'
        ]
        
        for cmd_name in expected_commands:
            self.assertIn(cmd_name, mcp_commands, f"MCP command {cmd_name} should be registered")
            
            cmd_info = mcp_commands[cmd_name]
            self.assertIn('handler', cmd_info, f"Command {cmd_name} should have handler")
            self.assertIn('description', cmd_info, f"Command {cmd_name} should have description")
            self.assertIn('is_async', cmd_info, f"Command {cmd_name} should specify async flag")
            self.assertIn('args', cmd_info, f"Command {cmd_name} should have args definition")
    
    def test_model_command_structure(self):
        """Test Model command structure and validation."""
        model_commands = self.cmd_handler.model_commands.commands
        
        # Print available commands for debugging
        self.logger.info(f"Available model commands: {list(model_commands.keys())}")
        
        # Verify we have some model commands registered
        self.assertGreater(len(model_commands), 0, "Should have model commands registered")
        
        # Check that actual commands exist (based on the help output we saw earlier)
        actual_commands = list(model_commands.keys())
        
        # Verify structure of existing commands
        for cmd_name, cmd_info in model_commands.items():
            self.assertIn('handler', cmd_info, f"Command {cmd_name} should have handler")
            self.assertIn('description', cmd_info, f"Command {cmd_name} should have description")
            self.assertIn('is_async', cmd_info, f"Command {cmd_name} should specify async flag")
            self.assertIn('args', cmd_info, f"Command {cmd_name} should have args definition")
    
    def test_command_recognition(self):
        """Test command recognition and parsing."""
        # Test valid command recognition through process_command
        async def async_test():
            # Test MCP command recognition
            is_command, should_continue = await self.cmd_handler.process_command("mcp:server:list")
            self.assertTrue(is_command, "Should recognize mcp:server:list as a command")
            self.assertTrue(should_continue, "Should continue chat after command")
            
            # Test Model command recognition - use actual command from the system
            model_commands = list(self.cmd_handler.model_commands.commands.keys())
            if model_commands:
                test_command = model_commands[0]  # Use first available command
                is_command, should_continue = await self.cmd_handler.process_command(test_command)
                self.assertTrue(is_command, f"Should recognize {test_command} as a command")
                self.assertTrue(should_continue, "Should continue chat after command")
            
            # Test non-command text
            is_command, should_continue = await self.cmd_handler.process_command("This is just regular text")
            self.assertFalse(is_command, "Should not recognize regular text as a command")
            self.assertTrue(should_continue, "Should continue chat after non-command")
        
        self.run_async(async_test())
    
    def test_command_argument_parsing(self):
        """Test command argument parsing and validation."""
        # Test simple command without arguments
        arg_defs = self.cmd_handler.mcp_commands.commands['mcp:server:list']['args']
        args = self.cmd_handler.mcp_commands._parse_args("", arg_defs)
        self.assertEqual(args, {})
        
        # Test command with positional arguments
        arg_defs = self.cmd_handler.mcp_commands.commands['mcp:tool:enable']['args']
        args = self.cmd_handler.mcp_commands._parse_args("test_tool", arg_defs)
        self.assertEqual(args, {"tool_name": "test_tool"})
        
        # Test command with multiple arguments - using llm:provider:status
        arg_defs = self.cmd_handler.model_commands.commands['llm:provider:status']['args']
        args = self.cmd_handler.model_commands._parse_args("--provider-name openai", arg_defs)
        self.assertEqual(args, {"provider-name": "openai"})
    
    def test_mcp_server_list_command(self):
        """Test MCP server list command execution."""
        async def async_test():
            with patch('hatchling.mcp_utils.mcp_server_api.MCPServerAPI.get_server_list') as mock_api:
                # Mock the API response
                mock_api.return_value = {
                    '/path/to/server1.py': True,
                    '/path/to/server2.py': False
                }
                
                # Capture output
                output = StringIO()
                with redirect_stdout(output):
                    result = await self.cmd_handler.process_command("mcp:server:list")
                
                # Verify command was recognized and executed
                is_command, should_continue = result
                self.assertTrue(is_command)
                self.assertTrue(should_continue)
                
                # Verify API was called
                mock_api.assert_called_once()
        
        self.run_async(async_test())
    
    def test_model_provider_list_command(self):
        """Test Model provider list command execution."""
        async def async_test():
            with patch('hatchling.core.llm.model_manager_api.ModelManagerAPI.list_providers') as mock_list_providers:
                # Mock the API response
                mock_list_providers.return_value = ['openai', 'ollama', 'anthropic']
                
                # Capture output
                output = StringIO()
                with redirect_stdout(output):
                    result = await self.cmd_handler.process_command("llm:provider:supported")
                
                # Verify command was recognized and executed
                is_command, should_continue = result
                self.assertTrue(is_command)
                self.assertTrue(should_continue)
                
                # Verify API was called
                mock_list_providers.assert_called_once()
                
                # Check output contains expected providers
                output_text = output.getvalue()
                self.assertIn('openai', output_text)
                self.assertIn('ollama', output_text)
                self.assertIn('anthropic', output_text)
        
        self.run_async(async_test())
    
    def test_command_error_handling(self):
        """Test command error handling."""
        async def async_test():
            with patch('hatchling.mcp_utils.mcp_server_api.MCPServerAPI.get_server_list') as mock_mcp_server_list:
                # Mock API to raise an exception
                mock_mcp_server_list.side_effect = Exception("Test error")
                
                result = await self.cmd_handler.process_command("mcp:server:list")
                
                # Verify command was recognized but handled error gracefully
                is_command, should_continue = result
                self.assertTrue(is_command)
                self.assertTrue(should_continue)  # Should continue despite error
        
        self.run_async(async_test())
    
    def test_command_help_system(self):
        """Test command help and discovery system."""
        # Test general help
        output = StringIO()
        with redirect_stdout(output):
            self.cmd_handler.print_commands_help()
        
        help_text = output.getvalue()
        
        # Verify help contains command categories
        self.assertIn('Model Commands', help_text)
        self.assertIn('Base Chat Commands', help_text)
        
        # Verify some specific commands are listed
        self.assertIn('mcp:server:list', help_text)
        self.assertIn('llm:provider:supported', help_text)
        self.assertIn('help', help_text)
        self.assertIn('quit', help_text)
    
    def test_invalid_command_handling(self):
        """Test handling of invalid commands."""
        async def async_test():
            # Test nonexistent command
            result = await self.cmd_handler.process_command("nonexistent:command")
            is_command, should_continue = result
            self.assertFalse(is_command)
            self.assertTrue(should_continue)
            
            # Test malformed command
            result = await self.cmd_handler.process_command("mcp:")
            is_command, should_continue = result
            self.assertFalse(is_command)
            self.assertTrue(should_continue)
        
        self.run_async(async_test())


class TestCommandArgumentValidation(AsyncTestCase):
    """Test command argument validation and dynamic parsing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_settings_registry = MagicMock()
        self.mock_settings_registry.settings = MockSettings()
        self.mock_env_manager = MockEnvironmentManager()
        self.mock_chat_session = MagicMock(spec=ChatSession)
        self.command_style = Style.from_dict({})
        
        self.cmd_handler = ChatCommandHandler(
            self.mock_chat_session, 
            self.mock_settings_registry, 
            self.command_style
        )
    
    def test_required_argument_validation(self):
        """Test validation of required arguments."""
        # Test missing required argument
        with patch('hatchling.mcp_utils.mcp_server_api.MCPServerAPI'):
            async def async_test():
                output = StringIO()
                with redirect_stdout(output):
                    result = await self.cmd_handler.process_command("mcp:tool:enable")
                
                # Should execute but show error for missing argument
                is_command, should_continue = result
                self.assertTrue(is_command)
                self.assertTrue(should_continue)
                
                output_text = output.getvalue()
                self.assertIn('Error', output_text)  # Should show error for missing argument
            
            self.run_async(async_test())
    
    def test_optional_argument_handling(self):
        """Test handling of optional arguments."""
        with patch('hatchling.core.llm.model_manager_api.ModelManagerAPI.list_available_models') as mock_api:
            mock_api.return_value = [
                MagicMock(provider='openai', name='gpt-4'),
                MagicMock(provider='openai', name='gpt-3.5'),
            ]

            async def async_test():
                # Test with optional argument
                result = await self.cmd_handler.process_command("llm:model:list openai")
                is_command, should_continue = result
                self.assertTrue(is_command)
                self.assertTrue(should_continue)
                
                # Test without optional argument
                result = await self.cmd_handler.process_command("llm:model:list")
                is_command, should_continue = result
                self.assertTrue(is_command)
                self.assertTrue(should_continue)
            
            self.run_async(async_test())


def run_command_system_integration_tests():
    """Run all command system integration tests.
    
    Returns:
        bool: True if all tests pass, False if any fail.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestCommandSystemIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestCommandArgumentValidation))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_command_system_integration_tests()
    sys.exit(0 if success else 1)
