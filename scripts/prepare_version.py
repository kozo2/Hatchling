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
    """Convert VERSION.meta to simple VERSION format for setuptools."""
    try:
        vm = VersionManager()
        
        # Read from VERSION.meta (structured format)
        version_data = vm.read_version_file()
        version_string = vm.get_version_string(version_data)
        
        # Write both files: keep VERSION.meta unchanged, update VERSION for setuptools
        vm.write_simple_version_file(version_data)
        
        print(f"VERSION file prepared for build: {version_string.lstrip('v')}")
        print("VERSION.meta preserved with structured format")
        
    except Exception as e:
        print(f"Error preparing VERSION file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()