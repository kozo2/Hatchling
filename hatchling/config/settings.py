"""Modular settings configuration for Hatchling application.

Imports and combines all modular settings classes.
"""

import threading
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from .llm_settings import LLMSettings, ELLMProvider
from .openai_settings import OpenAISettings
from .ollama_settings import OllamaSettings
from .path_settings import PathSettings
from .tool_calling_settings import ToolCallingSettings
from .ui_settings import UISettings

class SettingAccessLevel(str, Enum):
    """Defines access levels for settings."""
    NORMAL = "normal"
    PROTECTED = "protected"
    READ_ONLY = "read_only"


# Global singleton state - outside the class to avoid Pydantic interference
_app_settings_instance: Optional['AppSettings'] = None
_app_settings_lock = threading.Lock()


class AppSettings(BaseModel):
    """Root settings model that aggregates all setting categories.
    
    Implemented as a thread-safe singleton to provide global access
    to application settings throughout the codebase.
    """
    
    llm: LLMSettings = Field(default_factory=LLMSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    paths: PathSettings = Field(default_factory=PathSettings)
    tool_calling: ToolCallingSettings = Field(default_factory=ToolCallingSettings)
    ui: UISettings = Field(default_factory=UISettings)
    
    def __new__(cls, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern).
        
        Returns:
            AppSettings: The singleton instance.
        """
        global _app_settings_instance
        if _app_settings_instance is None:
            with _app_settings_lock:
                # Double-check locking pattern
                if _app_settings_instance is None:
                    _app_settings_instance = super().__new__(cls)
        return _app_settings_instance
    
    @classmethod
    def get_instance(cls) -> 'AppSettings':
        """Get the singleton instance of AppSettings.
        
        Creates the instance if it doesn't exist.
        
        Returns:
            AppSettings: The singleton instance.
        """
        global _app_settings_instance
        if _app_settings_instance is None:
            cls()  # This will create the instance via __new__
        return _app_settings_instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance.
        
        This method is primarily for testing purposes.
        """
        global _app_settings_instance
        with _app_settings_lock:
            _app_settings_instance = None

    @property
    def api_base(self) -> str:
        """Get the base API URL for the configured LLM provider."""
        if self.llm.provider_enum == ELLMProvider.OPENAI:
            return self.openai.api_base
        elif self.llm.provider_enum == ELLMProvider.OLLAMA:
            return self.ollama.api_base
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm.provider_enum}")
    
    class Config:
        extra = "forbid"