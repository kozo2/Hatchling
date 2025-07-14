"""Settings commands module for handling settings-related CLI operations.

This module provides SettingsCommands class which handles all settings-related
command operations including list, get, set, reset, import, export, and language
management through the chat interface.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

import tomli_w as toml_write
import tomli as toml_read
import yaml

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.formatted_text import FormattedText

from hatchling.core.chat.abstract_commands import AbstractCommands
from hatchling.config.i18n import translate


class SettingsCommands(AbstractCommands):
    """Handles settings-related command operations in the chat interface."""

    def _register_commands(self) -> None:
        """Register all settings-related commands."""
        self.commands = {
            'settings:list': {
                'handler': self._cmd_settings_list,
                'description': translate("commands.settings.list_description"),
                'is_async': False,
                'args': {
                    'filter': {
                        'positional': True,
                        'description': translate("commands.args.filter_description"),
                        'default': None,
                        'required': False
                    },
                    'format': {
                        'positional': False,
                        'description': translate("commands.args.format_description"),
                        'default': "table",
                        'completer_type': 'suggestions',
                        'values': ["table", "json", "yaml"],
                        'required': False
                    }
                }
            },
            'settings:get': {
                'handler': self._cmd_settings_get,
                'description': translate("commands.settings.get_description"),
                'is_async': False,
                'args': {
                    'setting': {
                        'positional': True,
                        'completer_type': 'suggestions',
                        'values': self._get_available_settings(),
                        'description': translate("commands.args.setting_description"),
                        'required': True
                    }
                }
            },
            'settings:set': {
                'handler': self._cmd_settings_set,
                'description': translate("commands.settings.set_description"),
                'is_async': True,
                'args': {
                    'setting': {
                        'positional': True,
                        'completer_type': 'suggestions',
                        'values': self._get_available_settings(),
                        'description': translate("commands.args.setting_description"),
                        'required': True
                    },
                    'value': {
                        'positional': True,
                        'description': translate("commands.args.value_description"),
                        'required': True
                    },
                    'force-confirm': {
                        'positional': False,
                        'description': translate("commands.args.force_description"),
                        'default': False,
                        'is_flag': True,
                        'required': False
                    },
                    'force-protected': {
                        'positional': False,
                        'description': translate("commands.args.force_protected_description"),
                        'default': False,
                        'is_flag': True,
                        'required': False
                    }
                }
            },
            'settings:reset': {
                'handler': self._cmd_settings_reset,
                'description': translate("commands.settings.reset_description"),
                'is_async': True,
                'args': {
                    'setting': {
                        'positional': True,
                        'completer_type': 'suggestions',
                        'values': self._get_available_settings(),
                        'description': translate("commands.args.setting_description"),
                        'required': True
                    },
                    'force-confirmed': {
                        'positional': False,
                        'description': translate("commands.args.force_description"),
                        'default': False,
                        'is_flag': True,
                        'required': False
                    },
                    'force-protected': {
                        'positional': False,
                        'description': translate("commands.args.force_protected_description"),
                        'default': False,
                        'is_flag': True,
                        'required': False
                    }
                }
            },
            'settings:export': {
                'handler': self._cmd_settings_export,
                'description': translate("commands.settings.export_description"),
                'is_async': False,
                'args': {
                    'file': {
                        'positional': True,
                        'completer_type': 'path',
                        'description': translate("commands.args.file_description"),
                        'required': True
                    },
                    'format': {
                        'positional': False,
                        'completer_type': 'suggestions',
                        'values': ["json", "yaml", "toml"],
                        'description': translate("commands.args.format_description"),
                        'default': "toml",
                        'required': False
                    },
                    'all': {
                        'positional': False,
                        'description': translate("commands.args.all_settings_description"),
                        'default': False,
                        'is_flag': True,
                        'required': False
                    }
                }
            },
            'settings:import': {
                'handler': self._cmd_settings_import,
                'description': translate("commands.settings.import_description"),
                'is_async': True,
                'args': {
                    'file': {
                        'positional': True,
                        'completer_type': 'path',
                        'description': translate("commands.args.file_description"),
                        'required': True
                    },
                    'force-confirm': {
                        'positional': False,
                        'description': translate("commands.args.force_description"),
                        'default': False,
                        'is_flag': True,
                        'required': False
                    },
                    'force-protected': {
                        'positional': False,
                        'description': translate("commands.args.force_protected_description"),
                        'default': False,
                        'is_flag': True,
                        'required': False
                    }
                }
            },
            'settings:language:list': {
                'handler': self._cmd_language_list,
                'description': translate("commands.settings.language_list_description"),
                'is_async': False,
                'args': {}
            },
            'settings:language:set': {
                'handler': self._cmd_language_set,
                'description': translate("commands.settings.language_set_description"),
                'is_async': False,
                'args': {
                    'language': {
                        'positional': True,
                        'completer_type': 'languages',
                        'description': translate("commands.args.language_description"),
                        'required': True
                    }
                }
            }
        }
    
    def print_commands_help(self) -> None:
        """Print help for all available chat commands."""
        print_formatted_text(FormattedText([
            ('class:header', "\n=== Settings Commands ===\n")
        ]), style=self.style)

        # Call parent class method to print formatted commands
        super().print_commands_help()
    
    def _cmd_settings_list(self, args: str) -> bool:
        """List all available settings with optional filtering.

        Args:
            args (str): Command arguments as a string.

        Returns:
            bool: True to continue the chat session, False to exit.
        """
        arg_defs = self.commands['settings:list']['args']

        parsed_args = self._parse_args(args, arg_defs)
        filter_pattern = parsed_args.get('filter')
        output_format = parsed_args.get('format', "table")

        if not self.settings_registry:
            self._print_error(translate("errors.settings_registry_not_available"))
            return True

        try:
            settings = self.settings_registry.list_settings(filter_pattern)
            self._output_settings_list(settings, output_format)
        except Exception as e:
            self._print_error(translate("errors.list_settings_failed", error=str(e)))
        return True

    def _cmd_settings_get(self, args: str) -> bool:
        """Get the value and metadata for a specific setting.

        Args:
            args (str): Command arguments as a string.

        Returns:
            bool: True to continue the chat session, False to exit.
        """
        arg_defs = self.commands['settings:get']['args']

        parsed_args = self._parse_args(args, arg_defs)
        setting_path = parsed_args.get('setting')

        if not setting_path:
            self._print_error(translate("errors.setting_name_required"))
            return True

        if not self.settings_registry:
            self._print_error(translate("errors.settings_registry_not_available"))
            return True

        try:
            category, name = self._parse_setting_path(setting_path)
            setting_info = self.settings_registry.get_setting(category, name)
            self._output_setting_info(setting_info)
        except ValueError as e:
            self._print_error(str(e))
        except Exception as e:
            self._print_error(translate("errors.get_setting_failed", error=str(e)))
        return True

    async def _cmd_settings_set(self, args: str) -> bool:
        """Set the value of a specific setting.

        Args:
            args (str): Command arguments as a string.

        Returns:
            bool: True to continue the chat session, False to exit.
        """
        arg_defs = self.commands['settings:set']['args']

        parsed_args = self._parse_args(args, arg_defs)
        setting_path = parsed_args.get('setting')
        value = parsed_args.get('value')
        force_confirm = parsed_args.get('force-confirm', False)
        force_protected = parsed_args.get('force-protected', False)

        if not setting_path or value is None:
            self._print_error(translate("errors.setting_and_value_required"))
            return True

        if not self.settings_registry:
            self._print_error(translate("errors.settings_registry_not_available"))
            return True

        try:
            category, name = self._parse_setting_path(setting_path)

            if not force_confirm:
                if not await self._request_user_consent(translate("prompts.confirm_set", setting=f"{category}:{name}", value=value)):
                    self._print_info(translate("info.operation_cancelled"))
                    return True

            current_setting = self.settings_registry.get_setting(category, name)
            typed_value = self._convert_value(value, current_setting["current_value"])
            success = self.settings_registry.set_setting(category, name, typed_value, force=force_protected)
            if success:
                self._print_success(translate("info.setting_updated",
                                              setting=f"{category}:{name}",
                                              value=str(typed_value)))
            else:
                self._print_error(translate("errors.set_setting_failed", setting=f"{category}:{name}"))
        except ValueError as e:
            self._print_error(str(e))
        except Exception as e:
            self._print_error(translate("errors.set_setting_failed", error=str(e)))
        return True

    async def _cmd_settings_reset(self, args: str) -> bool:
        """Reset a setting to its default value.

        Args:
            args (str): Command arguments as a string.

        Returns:
            bool: True to continue the chat session, False to exit.
        """
        arg_defs = self.commands['settings:reset']['args']

        parsed_args = self._parse_args(args, arg_defs)
        setting_path = parsed_args.get('setting')
        force_confirm = parsed_args.get('force-confirm', False)
        force_protected = parsed_args.get('force-protected', False)

        if not setting_path:
            self._print_error(translate("errors.setting_name_required"))
            return True

        if not self.settings_registry:
            self._print_error(translate("errors.settings_registry_not_available"))
            return True

        try:
            category, name = self._parse_setting_path(setting_path)
            if not force_confirm:
                if not await self._request_user_consent(translate("prompts.confirm_reset", setting=f"{category}:{name}")):
                    self._print_info(translate("info.operation_cancelled"))
                    return True

            success = self.settings_registry.reset_setting(category, name, force=force_protected)
            if success:
                self._print_success(translate("info.setting_reset", setting=f"{category}:{name}"))
            else:
                self._print_error(translate("errors.reset_setting_failed", setting=f"{category}:{name}"))
        except ValueError as e:
            self._print_error(str(e))
        except Exception as e:
            self._print_error(translate("errors.reset_setting_failed", error=str(e)))
        return True

    def _cmd_settings_export(self, args: str) -> bool:
        """Export settings to a file.

        Args:
            args (str): Command arguments as a string.

        Returns:
            bool: True to continue the chat session, False to exit.
        """
        arg_defs = self.commands['settings:export']['args']

        parsed_args = self._parse_args(args, arg_defs)
        file_path = parsed_args.get('file')
        file_format = parsed_args.get('format')
        all_settings = parsed_args.get('all', False)

        if not file_path:
            self._print_error(translate("errors.file_path_required"))
            return True

        if not self.settings_registry:
            self._print_error(translate("errors.settings_registry_not_available"))
            return True
        
        file_path_obj = Path(file_path)
        if not file_format:
            file_format = self._detect_format(file_path_obj)

        try:
            success = self.settings_registry.export_settings_to_file(str(file_path_obj), file_format, include_read_only=all_settings)
            if success:
                self._print_success(translate("info.settings_exported", file=str(file_path_obj)))
            else:
                self._print_error(translate("errors.export_settings_failed", file=str(file_path_obj)))
        except Exception as e:
            self._print_error(translate("errors.export_settings_failed", error=str(e)))
        return True

    async def _cmd_settings_import(self, args: str) -> bool:
        """Import settings from a file.

        Args:
            args (str): Command arguments as a string.

        Returns:
            bool: True to continue the chat session, False to exit.
        """
        arg_defs = self.commands['settings:import']['args']

        parsed_args = self._parse_args(args, arg_defs)
        file_path = parsed_args.get('file')
        force_confirm = parsed_args.get('force-confirm', False)
        force_protected = parsed_args.get('force-protected', False)

        if not file_path:
            self._print_error(translate("errors.file_path_required"))
            return True

        if not self.settings_registry:
            self._print_error(translate("errors.settings_registry_not_available"))
            return True

        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            self._print_error(translate("errors.file_not_found", file=str(file_path_obj)))
            return True

        try:
            if not force_confirm:
                if not await self._request_user_consent(translate("prompts.confirm_import", file=str(file_path_obj))):
                    self._print_info(translate("info.operation_cancelled"))
                    return True

            success = self.settings_registry.import_settings_from_file(str(file_path_obj), force=force_protected)
            if success:
                self._print_success(translate("info.settings_imported", file=str(file_path_obj)))
            else:
                self._print_error(translate("errors.import_settings_failed", file=str(file_path_obj)))
        except Exception as e:
            self._print_error(translate("errors.import_settings_failed", error=str(e)))
        return True

    def _cmd_language_list(self, args: str) -> bool:
        """List available languages.

        Args:
            args (str): Command arguments as a string.

        Returns:
            bool: True to continue the chat session, False to exit.
        """
        if not self.settings_registry:
            self._print_error(translate("errors.settings_registry_not_available"))
            return True

        try:
            languages = self.settings_registry.get_available_languages()
            current_language = self.settings_registry.get_current_language()

            self._print_header(translate("headers.available_languages"))
            for lang in languages:
                marker = "* " if lang["code"] == current_language else "  "
                self._print_info(f"{marker}{lang['code']}: {lang['name']}")
        except Exception as e:
            self._print_error(translate("errors.list_languages_failed", error=str(e)))
        return True

    def _cmd_language_set(self, args: str) -> bool:
        """
        List all available languages for settings commands.
        This command is picked up by the ChatCommandHandler and not here.
        That's because it concerns all commands, not just settings commands.
        """
        pass

    # Helper methods

    async def _request_user_consent(self, message: str) -> bool:
        """Request user consent for the installation plan.
        
        Args:
            message (str): Message to display for confirmation.

        Returns:
            bool: True if user approves, False otherwise.
        """        
        # Request confirmation
        session = PromptSession()
        while True:
            response = (await session.prompt_async(f"\n{message} [y/N]: ")).strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no', '']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
    
    def _parse_setting_path(self, setting_path: str) -> tuple[str, str]:
        """Parse a setting path in format 'category:name'.
        
        Args:
            setting_path (str): Setting path to parse.
            
        Returns:
            tuple[str, str]: Tuple of (category, name).
            
        Raises:
            ValueError: If path format is invalid.
        """
        if ":" not in setting_path:
            raise ValueError(translate("errors.invalid_setting_path", path=setting_path))
        
        parts = setting_path.split(":", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(translate("errors.invalid_setting_path", path=setting_path))
        
        return parts[0], parts[1]
    
    def _convert_value(self, value: str, current_value: Any) -> Any:
        """Convert string value to appropriate type based on current value.
        
        Args:
            value (str): String value to convert.
            current_value (Any): Current value to infer type from.
            
        Returns:
            Any: Converted value.
        """
        if isinstance(current_value, bool):
            return value.lower() in ("true", "1", "yes", "on", "enabled")
        elif isinstance(current_value, int):
            return int(value)
        elif isinstance(current_value, float):
            return float(value)
        else:
            return value
    
    def _detect_format(self, file_path: Path) -> str:
        """Detect file format from extension.
        
        Args:
            file_path (Path): File path to check.
            
        Returns:
            str: Detected format ("toml", "json", or "yaml").
        """
        suffix = file_path.suffix.lower()
        if suffix == ".toml":
            return "toml"
        elif suffix == ".json":
            return "json"
        elif suffix in (".yaml", ".yml"):
            return "yaml"
        else:
            return "toml"  # Default to TOML
    
    def _output_settings_list(self, settings: List[Dict[str, Any]], format_type: str) -> None:
        """Output settings list in specified format.
        
        Args:
            settings (List[Dict[str, Any]]): List of settings to output.
            format_type (str): Output format ("table", "json", or "yaml").
        """
        if format_type == "json":
            print(json.dumps(self.settings_registry.make_serializable(settings), indent=2))
        elif format_type == "yaml" and yaml:
            print(yaml.dump(self.settings_registry.make_serializable(settings), default_flow_style=False))
        else:
            # Table format (default)
            self._print_header(translate("headers.settings_list"))
            
            for setting in settings:
                # Group by category
                category_display_name = setting.get("category_display_name", setting["category_name"])
                self._print_subheader(f"[{category_display_name}] ({setting['category_name']})")

                # Format setting info
                display_name = setting.get("display_name", setting["name"])
                access_level = setting["access_level"].value if hasattr(setting["access_level"], "value") else setting["access_level"]
                
                self._print_info(f"  {display_name} ({setting['name']})")
                self._print_detail(f"    {translate('common.description')}: {setting['description']}")
                self._print_detail(f"    {translate('common.current')}: {setting['current_value']}")
                self._print_detail(f"    {translate('common.default')}: {setting['default_value']}")
                self._print_detail(f"    Access: {access_level}")
                
                if setting.get("hint"):
                    self._print_detail(f"    Hint: {setting['hint']}")
                print()
    
    def _output_setting_info(self, setting: Dict[str, Any]) -> None:
        """Output detailed information for a single setting.
        
        Args:
            setting (Dict[str, Any]): Setting information to output.
        """
        display_name = setting.get("display_name", setting["name"])
        category_name = setting.get("category_display_name", setting["category_name"])
        access_level = setting["access_level"].value if hasattr(setting["access_level"], "value") else setting["access_level"]
        
        self._print_header(f"{category_name}: {display_name}")
        self._print_info(f"{translate('common.name')}: {setting['name']}")
        self._print_info(f"{translate('common.category')}: {setting['category_name']}")
        self._print_info(f"{translate('common.description')}: {setting['description']}")
        self._print_info(f"{translate('common.current')}: {setting['current_value']}")
        self._print_info(f"{translate('common.default')}: {setting['default_value']}")
        self._print_info(f"Access Level: {access_level}")
        self._print_info(f"Type: {setting['type']}")
        
        if setting.get("hint"):
            self._print_info(f"Hint: {setting['hint']}")

    def _get_available_settings(self) -> List[str]:
        """Get a list of all available settings in the registry.

        Returns:
            List[str]: List of setting names.
        """
        if not self.settings_registry:
            return []

        return [f"{setting['category_name']}:{setting['name']}" for setting in self.settings_registry.list_settings()]
    
    def _print_header(self, text: str) -> None:
        """Print a formatted header."""
        print_formatted_text(FormattedText([("class:header", text)]), style=self.style)
    
    def _print_subheader(self, text: str) -> None:
        """Print a formatted subheader."""
        print_formatted_text(FormattedText([("class:subheader", text)]), style=self.style)
    
    def _print_info(self, text: str) -> None:
        """Print informational text."""
        print_formatted_text(FormattedText([("class:info", text)]), style=self.style)
    
    def _print_detail(self, text: str) -> None:
        """Print detail text."""
        print_formatted_text(FormattedText([("class:detail", text)]), style=self.style)
    
    def _print_success(self, text: str) -> None:
        """Print success message."""
        print_formatted_text(FormattedText([("class:success", f"✓ {text}")]), style=self.style)
    
    def _print_error(self, text: str) -> None:
        """Print error message."""
        self.logger.error(text)
        
    def _print_warning(self, text: str) -> None:
        """Print warning message."""
        self.logger.warning(text)
