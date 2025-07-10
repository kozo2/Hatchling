from enum import Enum

class SettingAccessLevel(str, Enum):
    """Defines access levels for settings."""
    NORMAL = "normal"
    PROTECTED = "protected"
    READ_ONLY = "read_only"