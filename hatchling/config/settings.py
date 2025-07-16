"""Modular settings configuration for Hatchling application.

Imports and combines all modular settings classes.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Optional, Union

from pydantic import BaseModel, Field
from .llm_settings import LLMSettings
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
    paths: PathSettings = Field(default_factory=PathSettings)
    tool_calling: ToolCallingSettings = Field(default_factory=ToolCallingSettings)
    ui: UISettings = Field(default_factory=UISettings)
    
    class Config:
        extra = "forbid"