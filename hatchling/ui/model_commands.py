"""LLM Model Management Commands.

This module provides CLI commands for managing LLM models and providers.
Commands follow the format 'llm:target:action' for clarity and consistency.
"""

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText

from hatchling.ui.abstract_commands import AbstractCommands
from hatchling.core.llm.model_manager_api import ModelManagerAPI
from hatchling.config.llm_settings import LLMSettings

class ModelCommands(AbstractCommands):
    """CLI commands for LLM model and provider management."""
    
    def _register_commands(self) -> None:
        """Register all model-related commands."""
        
        from hatchling.config.i18n import translate
        self.commands = {
            # Provider management commands
            'llm:provider:supported': {
                'handler': self._cmd_provider_supported,
                'description': translate('commands.llm.provider_supported_description'),
                'is_async': False,
                'args': {}
            },
            'llm:provider:status': {
                'handler': self._cmd_provider_status,
                'description': translate('commands.llm.provider_status_description'),
                'is_async': True,
                'args': {
                    'provider-name': {
                        'positional': False,
                        'completer_type': 'suggestions',
                        'values': self.settings.llm.provider_names,
                        'description': translate('commands.llm.provider_name_arg_description'),
                        'required': False
                    }
                }
            },
            # Model management commands
            'llm:model:list': {
                'handler': self._cmd_model_list,
                'description': translate('commands.llm.model_list_description'),
                'is_async': True,
                'args': {}
            },
            'llm:model:add': {
                'handler': self._cmd_model_add,
                'description': translate('commands.llm.model_add_description'),
                'is_async': True,
                'args': {
                    'provider-name': {
                        'positional': False,
                        'completer_type': 'suggestions',
                        'values': self.settings.llm.provider_names,
                        'description': translate('commands.llm.provider_name_arg_description'),
                        'required': False
                    },
                    'model-name': {
                        'positional': True,
                        'description': translate('commands.llm.model_name_arg_description'),
                        'required': True
                    }
                }
            },
            'llm:model:use': {
                'handler': self._cmd_model_use,
                'description': translate('commands.llm.model_use_description'),
                'is_async': False,
                'args': {
                    'model-name': {
                        'positional': True,
                        'completer_type': 'suggestions',
                        'values': [model.name for model in self.settings.llm.models],
                        'description': translate('commands.llm.model_name_arg_description'),
                        'required': True
                    },
                    'force-confirmed':{
                        'positional': False,
                        'completer_type': 'boolean',
                        'description': translate('commands.llm.force_confirmed_arg_description'),
                        'required': False,
                        'default': False,
                        'is_flag': True
                    }
                }
            },
            'llm:model:remove': {
                'handler': self._cmd_model_remove,
                'description': translate('commands.llm.model_remove_description'),
                'is_async': False,
                'args': {
                    'model-name': {
                        'positional': True,
                        'completer_type': 'suggestions',
                        'values': [model.name for model in self.settings.llm.models],
                        'description': translate('commands.llm.model_name_arg_description'),
                        'required': True
                    }
                }
            }
        }

    def print_commands_help(self) -> None:
        """Print help for all available chat commands."""
        print_formatted_text(FormattedText([
            ('class:header', "\n=== Model Commands ===\n")
        ]), style=self.style)

        # Call parent class method to print formatted commands
        super().print_commands_help()
    
    # =============================================================================
    # Provider Management Commands
    # =============================================================================

    def _cmd_provider_supported(self, args: str) -> bool:
        """List all supported LLM providers.
        This command retrieves and displays all LLM providers supported by the system.

        Args:
            args (str): Unused arguments.
            
        Returns:
            bool: True to continue the chat session.
        """
        try:
            providers = ModelManagerAPI.list_providers()
            
            if not providers:
                print("No LLM providers found")
                return True
            
            print("Available LLM Providers:")
            for provider in providers:
                print(f"  {provider}")
                
        except Exception as e:
            print(f"Error listing providers: {e}")
            self.logger.error(f"Error in provider list command: {e}")
            
        return True
    
    async def _cmd_provider_status(self, args: str) -> bool:
        """Check status of a specific provider.

        Args:
            args (str): Provider name argument.
            
        Returns:
            bool: True to continue the chat session.
        """
        try:
            args_def = self.commands['llm:provider:status']['args']
            parsed_args = self._parse_args(args, args_def)
            provider_name = parsed_args.get('provider-name', '')
            providers = self.settings.llm.provider_enums

            if provider_name:
                # Get provider health
                providers = [self.settings.llm.to_provider_enum(provider_name)] 
            
            for provider in providers:
                is_healthy = await ModelManagerAPI.check_provider_health(provider)
                if is_healthy:
                    print(f"Provider: {provider} - Status: AVAILABLE")
                    models = await ModelManagerAPI.list_available_models(provider)
                    print(f"  - Models: {[model.name for model in models]}")
                else:
                    print(f"Provider: {provider.value} - Status: UNAVAILABLE")

        except Exception as e:
            self.logger.error(f"Error in provider status command: {e}")
        
        finally:
            return True
    
    # =============================================================================
    # Model Management Commands
    # =============================================================================
    
    async def _cmd_model_list(self, args: str) -> bool:
        """List all available models, optionally filtered by provider or search query.
        
        Args:
            args (str): Optional provider name or search query to filter models.
            
        Returns:
            bool: True to continue the chat session.
        """
        
        #TODO: Implement filtering by provider name or search query

        print("Available LLM Models:")
        for model_info in self.settings.llm.models:
            print(f"  - {model_info.provider.value} {model_info.name}")

        return True
    
    async def _cmd_model_add(self, args: str) -> bool:
        """Pull/download a model (Ollama only).
        
        Args:
            args (str): Model name argument.
            
        Returns:
            bool: True to continue the chat session.
        """
        try:
            args_def = self.commands['llm:model:add']['args']
            parsed_args = self._parse_args(args, args_def)

            model_name = parsed_args.get('model-name', '')
            provider_name = parsed_args.get('provider-name', self.settings.llm.provider_enum.value)
            
            if not model_name:
                self.logger.error("Positional argument 'model-name' is required for pulling a model.")
                return True

            success = await ModelManagerAPI.pull_model(model_name, LLMSettings.to_provider_enum(provider_name))

            if success:
                # We update the commands args value suggestion for the autocompletion
                self.commands['llm:model:use']['args']['model-name']['values'] = [model.name for model in self.settings.llm.models]
                self.commands['llm:model:remove']['args']['model-name']['values'] = [model.name for model in self.settings.llm.models]

        except Exception as e:
            self.logger.error(f"Error in model pull command: {e}")
            
        return True

    def _cmd_model_use(self, args: str) -> bool:
        """Set the default model to use for the current session.
        
        Args:
            args (str): Model name argument.
            
        Returns:
            bool: True to continue the chat session.
        """
        try:
            args_def = self.commands['llm:model:use']['args']
            parsed_args = self._parse_args(args, args_def)
            model_name = parsed_args.get('model-name', '')
            force_confirmed = parsed_args.get('force-confirmed', False)

            if not model_name:
                self.logger.error("Positional argument 'model-name' is required to set the default model.")
                return True
            
            # Check if the model exists in the available models
            model_info = None
            for model in self.settings.llm.models:
                if model.name == model_name:
                    model_info = model
                    break

            if not model_info:
                self.logger.warning(f"Model '{model_name}' not found in available models. No action taken.")
                return True
            
            # Set the default model in the settings
            self.settings_registry.set_setting(
                "llm", "model", model_info.name, force=force_confirmed
            )
            self.settings_registry.set_setting(
                "llm", "provider_enum", model_info.provider, force=force_confirmed
            )

        except Exception as e:
            self.logger.error(f"Error in model use command: {e}")
            
        return True
    
    def _cmd_model_remove(self, args: str) -> bool:
        """Remove a model from the list of available models.
        
        Args:
            args (str): Model name argument.
            
        Returns:
            bool: True to continue the chat session.
        """
        try:
            args_def = self.commands['llm:model:remove']['args']
            parsed_args = self._parse_args(args, args_def)

            model_name = parsed_args.get('model-name', '')
            if not model_name:
                self.logger.error("Positional argument 'model-name' is required to remove a model.")
                return True
            
            # Find and remove the model
            for model_info in self.settings.llm.models:
                if model_info.name == model_name:
                    self.settings.llm.models.remove(model_info)
                    self.logger.info(f"Model '{model_name}' removed successfully.")
                    
                    # Update the command args values for autocompletion
                    self.commands['llm:model:use']['args']['model-name']['values'] = [model.name for model in self.settings.llm.models]
                    self.commands['llm:model:remove']['args']['model-name']['values'] = [model.name for model in self.settings.llm.models]
                    return True

            self.logger.warning(f"Model '{model_name}' not found in available models. No action taken.")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in model remove command: {e}")
            
        return True
    