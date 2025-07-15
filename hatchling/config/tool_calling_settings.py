"""Settings for tool calling behavior and limits.

Configures limits and parameters for tool call operations.
"""

from pydantic import BaseModel, Field

from .settings_access_level import SettingAccessLevel

class ToolCallingSettings(BaseModel):
    """Settings for tool calling behavior and limits."""

    max_iterations: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Maximum number of tool call iterations.",
        json_schema_extra={"access_level": SettingAccessLevel.NORMAL},
    )
    max_working_time: float = Field(
        default=30.0,
        gt=0.0,
        le=300.0,
        description="Maximum time in seconds for tool operations.",
        json_schema_extra={"access_level": SettingAccessLevel.NORMAL},
    )

    class Config:
        extra = "forbid"