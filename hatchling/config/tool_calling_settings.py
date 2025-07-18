"""Settings for tool calling behavior and limits.

Configures limits and parameters for tool call operations.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator

from .settings_access_level import SettingAccessLevel

class ToolCallingSettings(BaseModel):
    """Settings for tool calling behavior and limits."""

    max_iterations: int = Field(
        default=5,
        ge=1,
        description="Maximum number of tool call iterations.",
        json_schema_extra={"access_level": SettingAccessLevel.NORMAL},
    )

    max_working_time: Optional[float] = Field(
        default=60.0,
        description="Maximum time in seconds for tool operations. If None, no limit is enforced. This is checked upon tool call, not during the tool call. Hence if a single tool call takes longer than this, it will not be interrupted.",
        json_schema_extra={"access_level": SettingAccessLevel.NORMAL},
    )

    max_tool_working_time: Optional[float] = Field(
        default=12.0,
        description="Maximum time in seconds for a single tool operation. If None, no limit is enforced.",
        json_schema_extra={"access_level": SettingAccessLevel.NORMAL},
    )

    @field_validator("max_working_time", "max_tool_working_time")
    @classmethod
    def _positive_or_none(cls, v):
        if v is not None and v <= 0.0:
            raise ValueError("Value must be positive or None")
        return v

    class Config:
        extra = "forbid"