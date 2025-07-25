import aiohttp
import logging
import asyncio
from pathlib import Path
from typing import Optional

from prompt_toolkit import PromptSession, print_formatted_text as print_pt
from prompt_toolkit.history import FileHistory, InMemoryHistory
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style

from hatchling.core.logging.logging_manager import logging_manager
from hatchling.core.llm.providers.registry import ProviderRegistry
from hatchling.core.llm.chat_session import ChatSession
from hatchling.core.chat.chat_command_handler import ChatCommandHandler
from hatchling.config.settings_registry import SettingsRegistry
from hatchling.mcp_utils.manager import mcp_manager
from hatchling.mcp_utils.mcp_health_subscriber import MCPHealthSubscriber

from hatch import HatchEnvironmentManager

class CLIChat:
    """Command-line interface for chat functionality."""

    def __init__(self, settings_registry: SettingsRegistry):
        """Initialize the CLI chat interface.
        
        Args:
            settings (SettingsRegistry): The settings management instance containing configuration.
        """
        # Store settings first
        self.settings_registry = settings_registry
        mcp_manager.set_settings_registry(settings_registry)
        
        # Get a logger - styling is already configured at the application level
        self.logger = logging_manager.get_session("CLIChat")
        
        # Initialize prompt toolkit session with history
        history_dir = self.settings_registry.settings.paths.hatchling_cache_dir / 'histories'
        history_dir.mkdir(exist_ok=True, parents=True)
        
        # Setup persistent history with 500 entries limit
        try:
            self.prompt_session = PromptSession(
                history=FileHistory(str(history_dir / '.user_inputs')))
        except (IOError, OSError) as e:
            self.logger.warning(f"Could not create history file: {e}")
            self.logger.warning("Falling back to in-memory history")
            self.prompt_session = PromptSession(history=InMemoryHistory())
        
        # Define command styling for both help display and real-time input highlighting
        self.command_style = Style.from_dict({
            # Help display styles
            'command.name': 'bold #44ff00',          # Green bold for command names
            'command.description': "#ffffff",        # White for descriptions
            'command.args': 'italic #87afff',        # Light blue italic for arguments
            'header': 'bold #ff9d00 underline',      # Orange underline for headers

            # Group specific styles for help
            'command.name.hatch': 'bold #00b7c3',    # Teal for Hatch commands
            'command.name.base': 'bold #44ff00',     # Green for base commands
            'group.default': '',                     # Default group style
            
            # Real-time input highlighting styles
            'command.name': 'bold #44ff00',          # Command names - bright green
            'command.args.base': 'bold #87afff',     # Base command arguments - blue
            'command.args.hatch': 'bold #00b7c3',    # Hatch command arguments - teal
            'command.args.invalid': '#ff6b6b',       # Invalid arguments - red
            'command.value.path': '#ffb347',         # Path values - orange
            'command.value.number': '#98fb98',       # Number values - light green
            'command.value.string': '#dda0dd',       # String values - plum
            'command.value.generic': '#f0f0f0',      # Generic values - light gray
            'text.default': '#ffffff',               # Default text - white
        })
        
        self.env_manager = HatchEnvironmentManager(
            environments_dir = self.settings_registry.settings.paths.envs_dir,
            cache_ttl = 86400,  # 1 day default
        )
            
        # Provider will be initialized during startup
        # Initialize the provider
        try:
            ProviderRegistry.get_provider(self.settings_registry.settings.llm.provider_enum)
        
        except Exception as e:
            msg = f"Failed to initialize {self.settings_registry.settings.llm.provider_enum} LLM provider: {e}"
            msg += "\nEnsure the LLM provider name is correct in your settings."
            msg += "\nYou can list providers compatible with Hatchling using `model:provider:list` command."
            msg += "\nEnsure you have switched to a supported provider before trying to use the chat interface."
            self.logger.warning(msg)
        
        finally:
            # MCP health subscriber for event-driven server monitoring
            self.mcp_health_subscriber = MCPHealthSubscriber()
            
            # Initialize chat session
            self.chat_session = ChatSession()

            # Initialize command handler
            self.cmd_handler = ChatCommandHandler(self.chat_session, self.settings_registry, self.env_manager, self.command_style)
    
    async def start_interactive_session(self) -> None:
        """Run an interactive chat session with message history."""
        
        async with aiohttp.ClientSession() as session:
            while True: 
                try:
                    # Create formatted prompt
                    prompt_message = [
                        # status_style,
                        ('', 'You: ')
                    ]
                    # Use patch_stdout to prevent output interference
                    with patch_stdout():
                        user_message = await self.prompt_session.prompt_async(
                            FormattedText(prompt_message),
                            completer=self.cmd_handler.command_completer,
                            lexer=self.cmd_handler.command_lexer,
                            style=self.command_style
                        )
                    
                    # Process as command if applicable
                    is_command, should_continue = await self.cmd_handler.process_command(user_message)
                    if is_command:
                        if not should_continue:
                            break
                        continue
                    
                    # Handle normal message
                    if not user_message.strip():
                        # Skip empty input
                        continue

                    # Send the query
                    print_pt(FormattedText([('green', f"\n{self.settings_registry.settings.llm.provider_name} "+
                                             f"({self.settings_registry.settings.api_base}) - "+
                                             f"{self.settings_registry.settings.llm.model}: ")]
                                        ),
                                end='', flush=True)

                    await self.chat_session.send_message(user_message)
                    
                    print_pt('')  # Add an extra newline for readability

                except KeyboardInterrupt:
                    print_pt(FormattedText([('red', '\nInterrupted. Ending chat session...')]))
                    break
                except Exception as e:
                    self.logger.error(f"Error: {e}")
                    print_pt(FormattedText([('red', f'\nError: {e}')]))
    
    async def initialize_and_run(self) -> None:
        """Initialize the environment and run the interactive chat session."""
        try:
            # Start the interactive session
            await self.start_interactive_session()
            
        except Exception as e:
            error_msg = f"An error occurred: {e}"
            self.logger.error(error_msg)
            return
        
        finally:
            # Clean up any remaining MCP server processes only if tools were enabled
            if self.chat_session and len(mcp_manager.get_enabled_tools()) > 0:
                await mcp_manager.disconnect_all()