"""Settings registry for centralized management of all application settings.

This module provides a central registry that aggregates all settings, enforces access control,
and provides listing, getting, setting, resetting, import/export, and search capabilities.
"""

import re
import json
try:
    import tomli_w as toml_write
    import tomllib as toml_read
except ImportError:
    try:
        import toml
        toml_write = toml
        toml_read = toml
    except ImportError:
        toml_write = None
        toml_read = None

try:
    import yaml
except ImportError:
    yaml = None
from typing import Dict, List, Tuple, Any, Optional, Union
from difflib import SequenceMatcher

from pydantic import ValidationError

from hatchling.config.settings import AppSettings, SettingAccessLevel
from hatchling.core.logging.logging_manager import logging_manager
from hatchling.config.i18n import get_translation_loader, translate


class SettingsRegistry:
    """Central registry for all settings categories and fields.
    
    This class provides a frontend-agnostic API for all settings operations,
    including access control enforcement, validation, and audit logging.
    """
    
    def __init__(self, app_settings: AppSettings):
        """Initialize the settings registry.
        
        Args:
            app_settings (AppSettings): The application settings instance to manage.
        """
        self.app_settings = app_settings
        self.logger = logging_manager.get_session("hatchling.config.settings_registry")
        
        # Initialize translation loader with current language
        translation_loader = get_translation_loader()
        current_language = self.app_settings.ui.language
        if current_language != translation_loader.get_current_language():
            translation_loader.set_language(current_language)
    
    def list_settings(self, filter_regex: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all settings with optional filtering.
        
        Implements staged search: exact match, category match, regex search, then fuzzy search.
        
        Args:
            filter_regex (str, optional): Filter pattern for settings. Defaults to None.
            
        Returns:
            List[Dict[str, Any]]: List of setting information dictionaries.
        """
        all_settings = self._get_all_settings_metadata()
        
        if not filter_regex:
            return all_settings
        
        # Stage 1: Exact match (category or setting name)
        exact_matches = []
        for setting in all_settings:
            if setting['category_name']+":"+setting['name'] == filter_regex:
                exact_matches.append(setting)
        
        if exact_matches:
            return exact_matches
        
        # Stage 2: Category-wide listing
        category_matches = []
        for setting in all_settings:
            if setting['category_name'] == filter_regex:
                category_matches.append(setting)
        
        if category_matches:
            return category_matches
        
        # Stage 3: Regex search
        try:
            regex_pattern = re.compile(filter_regex, re.IGNORECASE)
            regex_matches = []
            for setting in all_settings:
                if (regex_pattern.search(setting['category_name']) or 
                    regex_pattern.search(setting['name']) or 
                    regex_pattern.search(setting['description'])):
                    regex_matches.append(setting)
            
            if regex_matches:
                return regex_matches
        except re.error:
            # Invalid regex, fall through to fuzzy search
            pass
        
        # Stage 4: Fuzzy search
        fuzzy_matches = []
        for setting in all_settings:
            search_text = f"{setting['category_name']} {setting['name']} {setting['description']}"
            similarity = SequenceMatcher(None, filter_regex.lower(), search_text.lower()).ratio()
            if similarity > 0.3:  # Minimum similarity threshold
                setting['_similarity'] = similarity
                fuzzy_matches.append(setting)
        
        # Sort by similarity (highest first)
        fuzzy_matches.sort(key=lambda x: x.get('_similarity', 0), reverse=True)
        
        # Remove similarity score from results
        for match in fuzzy_matches:
            match.pop('_similarity', None)
        
        return fuzzy_matches
    
    def get_setting(self, category: str, name: str) -> Dict[str, Any]:
        """Get metadata and value for a specific setting.
        
        Args:
            category (str): Setting category name.
            name (str): Setting name.
            
        Returns:
            Dict[str, Any]: Setting information including current and default values.
            
        Raises:
            ValueError: If the setting is not found.
        """
        setting_info = self._get_setting_info(category, name)
        if not setting_info:
            raise ValueError(f"Setting '{category}:{name}' not found")
        
        return setting_info
    
    def set_setting(self, category: str, name: str, value: Any, force: bool = False) -> bool:
        """Set a setting value with access control enforcement.
        
        Args:
            category (str): Setting category name.
            name (str): Setting name.
            value (Any): New value for the setting.
            force (bool, optional): Force setting protected values. Defaults to False.
            
        Returns:
            bool: True if setting was successful.
            
        Raises:
            ValueError: If setting is not found or access is denied.
            ValidationError: If the value is invalid.
        """
        setting_info = self._get_setting_info(category, name)
        if not setting_info:
            raise ValueError(f"Setting '{category}:{name}' not found")
        
        access_level = setting_info['access_level']
        old_value = setting_info['current_value']
        
        # Enforce access control
        if access_level == SettingAccessLevel.READ_ONLY:
            raise ValueError(f"Setting '{category}:{name}' is read-only and cannot be modified")
        
        if access_level == SettingAccessLevel.PROTECTED and not force:
            raise ValueError(f"Setting '{category}:{name}' is protected. Use --force to override")
        
        # Validate and set the value
        try:
            self._set_setting_value(category, name, value)
            new_value = self._get_setting_value(category, name)
            # Log the change
            self.logger.info(f"Setting '{category}:{name}' changed from '{old_value}' to '{new_value}'")
            return True
        except ValidationError as e:
            # Re-raise the original ValidationError for correct error reporting
            raise
    
    def reset_setting(self, category: str, name: str, force: bool = False) -> bool:
        """Reset a setting to its default value.
        
        Args:
            category (str): Setting category name.
            name (str): Setting name.
            force (bool, optional): Force resetting protected values. Defaults to False.
            
        Returns:
            bool: True if reset was successful.
            
        Raises:
            ValueError: If setting is not found or access is denied.
        """
        setting_info = self._get_setting_info(category, name)
        if not setting_info:
            raise ValueError(f"Setting '{category}:{name}' not found")
        
        default_value = setting_info['default_value']
        return self.set_setting(category, name, default_value, force)
    
    def export_settings(self, format: str = "toml") -> str:
        """Export all settings to a formatted string.
        
        Args:
            format (str, optional): Export format ('toml', 'json', 'yaml'). Defaults to "toml".
            
        Returns:
            str: Serialized settings data.
            
        Raises:
            ValueError: If format is not supported.
        """
        settings_dict = self.app_settings.model_dump()
        
        if format.lower() == "toml":
            if toml_write is None:
                raise ValueError("TOML support not available. Install 'tomli-w' or 'toml'")
            return toml_write.dumps(settings_dict)
        elif format.lower() == "json":
            return json.dumps(self.app_settings.model_dump_json(), indent=2)
        elif format.lower() == "yaml":
            if yaml is None:
                raise ValueError("YAML support not available. Install 'PyYAML'")
            return yaml.dump(settings_dict, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def import_settings(self, data: str, format: str = "toml", force: bool = False) -> Dict[str, Any]:
        """Import settings from a formatted string.
        
        Args:
            data (str): Serialized settings data.
            format (str, optional): Import format ('toml', 'json', 'yaml'). Defaults to "toml".
            force (bool, optional): Force importing protected values. Defaults to False.
            
        Returns:
            Dict[str, Any]: Import report with success, skipped, and failed settings.
            
        Raises:
            ValueError: If format is not supported or data is invalid.
        """
        # Parse the data
        try:
            if format.lower() == "toml":
                if toml_read is None:
                    raise ValueError("TOML support not available. Install 'tomllib' or 'toml'")
                parsed_data = toml_read.loads(data)
            elif format.lower() == "json":
                parsed_data = json.loads(data)
            elif format.lower() == "yaml":
                if yaml is None:
                    raise ValueError("YAML support not available. Install 'PyYAML'")
                parsed_data = yaml.safe_load(data)
            else:
                raise ValueError(f"Unsupported import format: {format}")
        except Exception as e:
            raise ValueError(f"Failed to parse {format} data: {e}")
        
        report = {
            "successful": [],
            "skipped": [],
            "failed": []
        }
        
        # Import each category
        for category_name, category_data in parsed_data.items():
            if not isinstance(category_data, dict):
                continue
                
            for setting_name, value in category_data.items():
                try:
                    self.set_setting(category_name, setting_name, value, force)
                    report["successful"].append(f"{category_name}:{setting_name}")
                except ValueError as e:
                    if "read-only" in str(e) or ("protected" in str(e) and not force):
                        report["skipped"].append(f"{category_name}:{setting_name} ({str(e)})")
                    else:
                        report["failed"].append(f"{category_name}:{setting_name} ({str(e)})")
                except Exception as e:
                    report["failed"].append(f"{category_name}:{setting_name} ({str(e)})")
        
        # Log the import operation
        self.logger.info(f"Settings import completed: {len(report['successful'])} successful, "
                        f"{len(report['skipped'])} skipped, {len(report['failed'])} failed")
        
        return report
    
    def _get_all_settings_metadata(self) -> List[Dict[str, Any]]:
        """Get metadata for all settings with internationalized display names and descriptions.

        Returns:
            List[Dict[str, Any]]: List of metadata dictionaries for each setting.
        """
        from pydantic import BaseModel

        settings_list = []

        # Iterate over the main settings model fields to get category names
        for category_name, _category_model in iter(self.app_settings):
            if not isinstance(_category_model, BaseModel):
                continue  # Skip non-model fields

            category_model_class = type(_category_model)
            
            # Get translated category information
            category_display_name = translate(f"settings.{category_name}.category_name")
            category_description = translate(f"settings.{category_name}.category_description")
            
            for field_name, field_info in category_model_class.model_fields.items():
                current_value = getattr(_category_model, field_name)
                default_value = field_info.default

                # Handle default_factory
                if hasattr(field_info, 'default_factory') and field_info.default_factory:
                    default_value = field_info.default_factory()

                # Get access level from field info
                access_level = SettingAccessLevel.NORMAL
                if hasattr(field_info, 'json_schema_extra') and field_info.json_schema_extra:
                    access_level = field_info.json_schema_extra.get('access_level', SettingAccessLevel.NORMAL)
                elif hasattr(field_info, 'extra') and 'access_level' in field_info.extra:
                    access_level = field_info.extra['access_level']

                # Get translated setting information
                setting_name_key = f"settings.{category_name}.{field_name}.name"
                setting_desc_key = f"settings.{category_name}.{field_name}.description"
                setting_hint_key = f"settings.{category_name}.{field_name}.hint"
                
                setting_display_name = translate(setting_name_key)
                setting_description = translate(setting_desc_key)
                setting_hint = translate(setting_hint_key)
                
                # Fall back to original description if translation key doesn't exist
                if setting_description == setting_desc_key:
                    setting_description = field_info.description or ""

                settings_list.append({
                    "category_name": category_name,
                    "category_display_name": category_display_name,
                    "category_description": category_description,
                    "name": field_name,
                    "display_name": setting_display_name,
                    "current_value": current_value,
                    "default_value": default_value,
                    "description": setting_description,
                    "hint": setting_hint if setting_hint != setting_hint_key else "",
                    "access_level": access_level,
                    "type": str(field_info.annotation) if hasattr(field_info, 'annotation') else str(type(current_value).__name__)
                })
        return settings_list
        
    def _get_setting_info(self, category: str, name: str) -> Optional[Dict[str, Any]]:
        """Get information for a specific setting."""
        all_settings = self._get_all_settings_metadata()
        for setting in all_settings:
            if setting['category_name'] == category and setting['name'] == name:
                return setting
        return None
    
    def _get_setting_value(self, category: str, name: str) -> Any:
        """Get the current value of a setting."""
        category_model = getattr(self.app_settings, category, None)
        if category_model is None:
            raise ValueError(f"Unknown category: {category}")
        
        return getattr(category_model, name, None)
    
    def _set_setting_value(self, category: str, name: str, value: Any) -> None:
        """Set the value of a setting with validation."""
        category_model = getattr(self.app_settings, category, None)
        if category_model is None:
            raise ValueError(f"Unknown category: {category}")
        
        if not hasattr(category_model, name):
            raise ValueError(f"Unknown setting: {name}")
        
        # Use Pydantic's validation by creating a new instance
        category_dict = category_model.model_dump()
        category_dict[name] = value
        
        # This will raise ValidationError if the value is invalid
        new_category_model = type(category_model)(**category_dict)
        
        # If validation passes, update the actual model
        setattr(category_model, name, value)

    # Language management methods
    
    def get_available_languages(self) -> List[Dict[str, str]]:
        """Get list of available languages for the interface.
        
        Returns:
            List[Dict[str, str]]: List of available languages with code and name.
        """
        translation_loader = get_translation_loader()
        return translation_loader.get_available_languages()
    
    def get_current_language(self) -> str:
        """Get the current interface language.
        
        Returns:
            str: Current language code.
        """
        # Get from UI settings
        return self.app_settings.ui.language
    
    def set_language(self, language_code: str) -> bool:
        """Set the interface language.
        
        Args:
            language_code (str): Language code to set.
            
        Returns:
            bool: True if language was successfully set.
            
        Raises:
            ValueError: If language is not available.
        """
        translation_loader = get_translation_loader()
        
        # Check if language is available
        available_languages = [lang["code"] for lang in translation_loader.get_available_languages()]
        if language_code not in available_languages:
            available_str = ", ".join(available_languages)
            error_msg = translate("errors.language_not_found", language=language_code)
            raise ValueError(f"{error_msg}. Available: {available_str}")
        
        # Set in translation loader
        if translation_loader.set_language(language_code):
            # Update UI settings
            try:
                self.set_setting("ui", "language", language_code)
                self.logger.info(translate("info.language_changed", language=language_code))
                return True
            except Exception as e:
                self.logger.error(f"Failed to update language setting: {e}")
                return False
        return False
    
    def reload_translations(self) -> None:
        """Reload translation files from disk."""
        translation_loader = get_translation_loader()
        translation_loader.reload_translations()
        self.logger.info("Translations reloaded")

    # File-based import/export methods
    
    def export_settings_to_file(self, file_path: str, format: Optional[str] = None) -> bool:
        """Export settings to a file.
        
        Args:
            file_path (str): Path to export file.
            format (Optional[str]): Export format. If None, detected from file extension.
            
        Returns:
            bool: True if export was successful.
        """
        try:
            from pathlib import Path
            path = Path(file_path)
            
            if format is None:
                # Detect format from file extension
                suffix = path.suffix.lower()
                if suffix == ".json":
                    format = "json"
                elif suffix in (".yaml", ".yml"):
                    format = "yaml"
                else:
                    format = "toml"  # Default
            
            # Export settings to string
            settings_data = self.export_settings(format)
            
            # Write to file
            with open(path, 'w', encoding='utf-8') as f:
                f.write(settings_data)
            
            self.logger.info(f"Settings exported to {file_path} in {format} format")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export settings to {file_path}: {e}")
            return False
    
    def import_settings_from_file(self, file_path: str, format: Optional[str] = None, force: bool = False) -> bool:
        """Import settings from a file.
        
        Args:
            file_path (str): Path to import file.
            format (Optional[str]): Import format. If None, detected from file extension.
            force (bool): Force importing protected values.
            
        Returns:
            bool: True if import was successful.
        """
        try:
            from pathlib import Path
            path = Path(file_path)
            
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if format is None:
                # Detect format from file extension
                suffix = path.suffix.lower()
                if suffix == ".json":
                    format = "json"
                elif suffix in (".yaml", ".yml"):
                    format = "yaml"
                else:
                    format = "toml"  # Default
            
            # Read file content
            with open(path, 'r', encoding='utf-8') as f:
                data = f.read()
            
            # Import settings from string
            result = self.import_settings(data, format, force)
            
            self.logger.info(f"Settings imported from {file_path} in {format} format")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import settings from {file_path}: {e}")
            return False
