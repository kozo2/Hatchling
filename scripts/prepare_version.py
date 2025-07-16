#!/usr/bin/env python3
"""
Build helper script that prepares the VERSION file for setuptools.
This should be run before building the package.
"""

import os
import sys
from pathlib import Path

# Add the scripts directory to Python path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from version_manager import VersionManager

def main():
    """Convert VERSION file to simple format for setuptools."""
    try:
        vm = VersionManager()
        vm.write_simple_version()
        print("VERSION file prepared for build")
    except Exception as e:
        print(f"Error preparing VERSION file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()