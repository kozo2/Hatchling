"""Modular settings configuration for Hatchling application.

Imports and combines all modular settings classes.
"""

from enum import Enum

from pydantic import BaseModel, Field
from .llm_settings import LLMSettings
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


class AppSettings(BaseModel):
    """Root settings model that aggregates all setting categories."""
    
    llm: LLMSettings = Field(default_factory=LLMSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    paths: PathSettings = Field(default_factory=PathSettings)
    tool_calling: ToolCallingSettings = Field(default_factory=ToolCallingSettings)
    ui: UISettings = Field(default_factory=UISettings)
    
    class Config:
        extra = "forbid"