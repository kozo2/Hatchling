"""Settings for LLM (Large Language Model) configuration."""

import os
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

from .settings_access_level import SettingAccessLevel

class ELLMProvider(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"

class LLMSettings(BaseModel):
    """Settings for LLM (Large Language Model) configuration."""

    # Provider selection
    provider: ELLMProvider = Field(
        default_factory=lambda: os.environ.get("LLM_PROVIDER", ELLMProvider.OLLAMA),
        description="LLM provider to use ('ollama' or 'openai').",
        json_schema_extra={"access_level": SettingAccessLevel.NORMAL},
    )

    model: str = Field(
        default_factory=lambda: os.environ.get("LLM_MODEL", "llama3.2"),
        description="Default model to use for the selected provider.",
        json_schema_extra={"access_level": SettingAccessLevel.NORMAL},
    )

    @property
    def get_provider(self) -> str:
        """Return the current LLM provider."""
        return self.provider.value

    class Config:
        extra = "forbid"