"""Settings for LLM (Large Language Model) configuration."""

import os
from pydantic import BaseModel, Field

from .settings_access_level import SettingAccessLevel

class LLMSettings(BaseModel):
    """Settings for LLM (Large Language Model) configuration."""

    api_url: str = Field(
        default_factory=lambda: os.environ.get("OLLAMA_HOST_API", "http://localhost:11434/api"),
        description="URL for the Ollama API endpoint.",
        json_schema_extra={"access_level": SettingAccessLevel.PROTECTED},
    )
    model: str = Field(
        default_factory=lambda: os.environ.get("OLLAMA_MODEL", "mistral-small3.1"),
        description="LLM model to use for chat interactions.",
        json_schema_extra={"access_level": SettingAccessLevel.NORMAL},
    )

    class Config:
        extra = "forbid"