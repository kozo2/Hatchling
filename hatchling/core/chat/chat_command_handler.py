"""Chat command handler module for processing user commands in the chat interface.

This module provides a central handler for all chat commands by combining
base commands, Hatch-specific commands, and settings commands into a unified interface.
"""

import logging
from typing import Tuple, Optional

from prompt_toolkit.styles import Style

from hatchling.core.logging.session_debug_log import SessionDebugLog
from hatchling.config.settings import AppSettings
from hatchling.core.chat.base_commands import BaseChatCommands
from hatchling.core.chat.hatch_commands import HatchCommands
from hatchling.core.chat.settings_commands import SettingsCommands
from hatchling.config.settings_registry import SettingsRegistry

from hatch import HatchEnvironmentManager


class ChatCommandHandler:
    """Handles processing of command inputs in the chat interface."""    
    def __init__(self, chat_session, settings: AppSettings, env_manager: HatchEnvironmentManager, debug_log: SessionDebugLog, style: Optional[Style] = None, settings_registry: Optional[SettingsRegistry] = None):
        """Initialize the command handler.
        
        Args:
            chat_session: The chat session this handler is associated with.
            settings (AppSettings): The chat settings to use.
            env_manager (HatchEnvironmentManager): The Hatch environment manager.
            debug_log (SessionDebugLog): Logger for command operations.
            style (Optional[Style]): Style for formatting command output.
            settings_registry (Optional[SettingsRegistry]): Settings registry for settings commands.
        """

        self.base_commands = BaseChatCommands(chat_session, settings, env_manager, debug_log, style, settings_registry)
        self.hatch_commands = HatchCommands(chat_session, settings, env_manager, debug_log, style, settings_registry)
        self.settings_commands = SettingsCommands(chat_session, settings, env_manager, debug_log, style, settings_registry)

        self._register_commands()
    
    def _register_commands(self) -> None:
        """Register all available chat commands with their handlers."""
        # Combine all commands from all handlers
        self.commands = {}
        self.commands.update(self.base_commands.get_command_metadata())
        self.commands.update(self.hatch_commands.get_command_metadata())
        self.commands.update(self.settings_commands.get_command_metadata())
        
        # Keep old format for backward compatibility
        self.sync_commands = {}
        self.async_commands = {}
        
        for cmd_name, cmd_info in self.commands.items():
            if cmd_info['is_async']:
                self.async_commands[cmd_name] = (cmd_info['handler'], cmd_info['description'])
            else:
                self.sync_commands[cmd_name] = (cmd_info['handler'], cmd_info['description'])
        
    def print_commands_help(self) -> None:
        """Print help for all available chat commands."""
        print("\n=== Chat Commands ===")
        print("Type 'help' for this help message")
        print()
        
        self.base_commands.print_commands_help()
        self.hatch_commands.print_commands_help()
        self.settings_commands.print_commands_help()
            
        print("======================\n")

    def set_commands_language(self, language_code: str) -> None:
        """Set the language for all commands.
        
        Args:
            language_code (str): The language code to set.
        """
        self.base_commands.set_commands_language(language_code)
        self.hatch_commands.set_commands_language(language_code)
        self.settings_commands.set_commands_language(language_code)
    
    async def process_command(self, user_input: str) -> Tuple[bool, bool]:
        """Process a potential command from user input.
        
        Args:
            user_input (str): The user's input text.
            
        Returns:
            Tuple[bool, bool]: (is_command, should_continue)
              - is_command: True if input was a command
              - should_continue: False if chat session should end
        """
        user_input = user_input.strip()
        
        # Handle empty input
        if not user_input:
            return True, True
            
        # Extract command and arguments
        parts = user_input.split(' ', 1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command == "help":
            self.print_commands_help()
            return True, True
        
        if command == "settings:language:set":
            self.set_commands_language(args.strip())
            return True, True
        
        # Check if the input is a registered command
        if command in self.sync_commands:
            handler_func, _ = self.sync_commands[command]
            return True, handler_func(args)
        elif command in self.async_commands:
            async_handler_func, _ = self.async_commands[command]
            return True, await async_handler_func(args)
            
        # Not a command
        return False, True

    def get_all_command_metadata(self) -> dict:
        """Get all command metadata from both command handlers.
        
        Returns:
            dict: Combined command metadata from base and hatch commands.
        """
        return self.commands