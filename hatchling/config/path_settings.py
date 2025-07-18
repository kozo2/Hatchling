"""Settings for file and directory paths.

Handles configuration for environment directories and related paths.
"""

import os
from pathlib import Path
from typing import Union
from pydantic import BaseModel, Field, field_validator

from .settings_access_level import SettingAccessLevel

class PathSettings(BaseModel):
    """Settings for file and directory paths."""

    hatchling_source_dir: Union[str, Path] = Field(
        default_factory=lambda: Path(os.environ.get("HATCHLING_SOURCE_DIR", str(Path.home() / "Hatchling"))),
        description="Directory where Hatchling source code is located.",
        json_schema_extra={"access_level": SettingAccessLevel.READ_ONLY},
    )

    envs_dir: Union[str, Path] = Field(
        default_factory=lambda: Path(os.environ.get("HATCH_ENVS_DIR", str(Path.home() / ".hatch" / "envs"))),
        description="Directory for Hatch environments.",
        json_schema_extra={"access_level": SettingAccessLevel.READ_ONLY},
    )

    hatchling_cache_dir: Union[str, Path] = Field(
        default_factory=lambda: Path(os.environ.get("HATCHLING_CACHE_DIR", str(Path.home() / ".hatch"))),
        description="Directory for Hatchling cache and data storage.",
        json_schema_extra={"access_level": SettingAccessLevel.READ_ONLY},
    )

    hatchling_settings_dir: Union[str, Path] = Field(
        default_factory=lambda: Path(os.environ.get("HATCHLING_SETTINGS_DIR", 
                                                   str(Path(os.environ.get("HATCHLING_CACHE_DIR", str(Path.home() / ".hatch"))) / "settings"))),
        description="Directory for Hatchling settings storage.",
        json_schema_extra={"access_level": SettingAccessLevel.READ_ONLY},
    )

    @field_validator('envs_dir', mode='before')
    @classmethod
    def validate_envs_dir(cls, v):
        """Validate and resolve environment directory path. Always return a Path object.

        Args:
            v (str or Path): The input value for the environment directory.

        Returns:
            Path: The resolved Path object.

        Raises:
            TypeError: If the input is not a str or Path.
        """
        if isinstance(v, Path):
            return v
        if isinstance(v, str):
            if os.path.isabs(v):
                return Path(v)
            else:
                return Path.home() / v
        raise TypeError(f"envs_dir must be a str or Path, got {type(v)}")

    @field_validator('hatchling_cache_dir', mode='before')
    @classmethod
    def validate_cache_dir(cls, v):
        """Validate and resolve cache directory path. Always return a Path object.

        Args:
            v (str or Path): The input value for the cache directory.

        Returns:
            Path: The resolved Path object.

        Raises:
            TypeError: If the input is not a str or Path.
        """
        if isinstance(v, Path):
            return v
        if isinstance(v, str):
            if os.path.isabs(v):
                return Path(v)
            else:
                return Path.home() / v
        raise TypeError(f"hatchling_cache_dir must be a str or Path, got {type(v)}")

    @field_validator('hatchling_settings_dir', mode='before')
    @classmethod
    def validate_settings_dir(cls, v):
        """Validate and resolve settings directory path. Always return a Path object.

        Args:
            v (str or Path): The input value for the settings directory.

        Returns:
            Path: The resolved Path object.

        Raises:
            TypeError: If the input is not a str or Path.
        """
        if isinstance(v, Path):
            return v
        if isinstance(v, str):
            if os.path.isabs(v):
                return Path(v)
            else:
                return Path.home() / v
        raise TypeError(f"hatchling_settings_dir must be a str or Path, got {type(v)}")

    class Config:
        extra = "forbid"