"""
Hatchling - LLM with MCP Tool Calling

This package provides a CLI interface for interacting with LLMs 
with MCP Tool Calling capabilities.
"""

import os

def _read_version():
    version_file = os.path.join(os.path.dirname(__file__), '..', 'VERSION')
    try:
        with open(version_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception:
        return "unknown"

__version__ = _read_version()