"""Settings for user interface configuration.

Handles UI-related configuration such as language selection.
"""

from pydantic import BaseModel, Field

from .settings_access_level import SettingAccessLevel

class UISettings(BaseModel):
    """Settings for user interface configuration."""

    language: str = Field(
        default="en",
        description="Language code for user interface localization.",
        json_schema_extra={"access_level": SettingAccessLevel.NORMAL},
    )

    class Config:
        extra = "forbid"