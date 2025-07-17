#!/usr/bin/env python3
"""
Version management script for Hatchling.
Handles reading and updating version information based on branch and changes.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import Dict, Tuple, Optional


class VersionManager:
    def __init__(self, version_file_path: str = "VERSION"):
        self.version_file = Path(version_file_path)
        if not self.version_file.exists():
            raise FileNotFoundError(f"VERSION file not found at {version_file_path}")
    
    def read_version_file(self) -> Dict[str, str]:
        """Read the VERSION file and parse version components."""
        version_data = {}
        with open(self.version_file, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    version_data[key.strip()] = value.strip()
        return version_data
    
    def write_version_file(self, version_data: Dict[str, str]) -> None:
        """Write version data back to the VERSION file."""
        with open(self.version_file, 'w') as f:
            for key in ['MAJOR', 'MINOR', 'PATCH', 'DEV_NUMBER', 'BUILD_NUMBER', 'BRANCH']:
                value = version_data.get(key, '')
                f.write(f"{key}={value}\n")
    
    def get_version_string(self, version_data: Optional[Dict[str, str]] = None) -> str:
        """Generate semantic version string from version data."""
        if version_data is None:
            version_data = self.read_version_file()
        
        major = version_data.get('MAJOR', '1')
        minor = version_data.get('MINOR', '0')
        patch = version_data.get('PATCH', '0')
        dev_number = version_data.get('DEV_NUMBER', '')
        build_number = version_data.get('BUILD_NUMBER', '')
        
        version = f"v{major}.{minor}.{patch}"
        
        if dev_number:
            version += f".dev{dev_number}"
        
        if build_number:
            version += f"+build{build_number}"
        
        return version
    
    def get_current_branch(self) -> str:
        """Get the current git branch."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "unknown"
    
    def increment_version(self, increment_type: str, branch: str = None) -> Dict[str, str]:
        """Increment version based on type and branch."""
        version_data = self.read_version_file()
        
        if branch is None:
            branch = self.get_current_branch()
        
        major = int(version_data.get('MAJOR', '1'))
        minor = int(version_data.get('MINOR', '0'))
        patch = int(version_data.get('PATCH', '0'))
        dev_number = int(version_data.get('DEV_NUMBER', '0')) if version_data.get('DEV_NUMBER', '') else 0
        build_number = int(version_data.get('BUILD_NUMBER', '0')) if version_data.get('BUILD_NUMBER', '') else 0
        
        # Handle different increment types
        if increment_type == 'major':
            major += 1
            minor = 0
            patch = 0
        elif increment_type == 'minor':
            minor += 1
            patch = 0
        elif increment_type == 'patch':
            patch += 1
        elif increment_type == 'dev':
            dev_number += 1
        elif increment_type == 'build':
            build_number += 1
        
        # Set dev_number and build_number based on branch
        dev_num_str = ""
        build_num_str = ""
        
        if branch == 'main':
            # Main branch gets clean releases
            dev_num_str = ""
            build_num_str = ""
        elif branch == 'dev':
            # Dev branch gets dev prerelease
            dev_num_str = str(dev_number) if dev_number > 0 else ""
            build_num_str = ""
        elif branch.startswith('feat/') or branch.startswith('fix/'):
            # Feature/fix branches get dev prerelease with build number
            dev_num_str = str(dev_number)  # Always include dev number for feat/fix branches
            build_num_str = str(build_number) if build_number > 0 else ""
        else:
            # Other branches get dev prerelease
            dev_num_str = str(dev_number) if dev_number > 0 else ""
            build_num_str = ""
        
        return {
            'MAJOR': str(major),
            'MINOR': str(minor),
            'PATCH': str(patch),
            'DEV_NUMBER': dev_num_str,
            'BUILD_NUMBER': build_num_str,
            'BRANCH': branch
        }
    
    def update_version_for_branch(self, branch: str = None) -> str:
        """Update version based on branch type."""
        if branch is None:
            branch = self.get_current_branch()
        
        current_data = self.read_version_file()
        
        if branch.startswith('feat/'):
            # Feature branch: increment minor version, set dev number
            new_data = self.increment_version('minor', branch)
            new_data['DEV_NUMBER'] = '0'  # Start with dev0
            new_data['BUILD_NUMBER'] = '0'  # Start with build0
        elif branch.startswith('fix/'):
            # Fix branch: increment patch version, set dev number
            new_data = self.increment_version('patch', branch)
            new_data['DEV_NUMBER'] = '0'  # Start with dev0
            new_data['BUILD_NUMBER'] = '0'  # Start with build0
        elif branch in ['main', 'dev']:
            # Main or dev branch: keep current version, update dev/build numbers
            new_data = current_data.copy()
            new_data['BRANCH'] = branch
            if branch == 'main':
                new_data['DEV_NUMBER'] = ''
                new_data['BUILD_NUMBER'] = ''
            elif branch == 'dev':
                # Keep existing dev number or set to 0 if empty
                if not new_data.get('DEV_NUMBER'):
                    new_data['DEV_NUMBER'] = '0'
                new_data['BUILD_NUMBER'] = ''
        else:
            # Other branches: treat as dev
            new_data = current_data.copy()
            new_data['BRANCH'] = branch
            new_data['DEV_NUMBER'] = '0'
            new_data['BUILD_NUMBER'] = ''
        
        self.write_version_file(new_data)
        return self.get_version_string(new_data)
    
    def write_simple_version(self) -> None:
        """Write a simple version string for setuptools compatibility."""
        version_data = self.read_version_file()
        version_string = self.get_version_string(version_data)
        # Remove 'v' prefix for setuptools
        simple_version = version_string.lstrip('v')
        
        # Write to VERSION file in simple format for setuptools
        with open(self.version_file, 'w') as f:
            f.write(simple_version)


def main():
    parser = argparse.ArgumentParser(description='Manage project version')
    parser.add_argument('--get', action='store_true', help='Get current version string')
    parser.add_argument('--increment', choices=['major', 'minor', 'patch', 'dev', 'build'], 
                       help='Increment version component')
    parser.add_argument('--update-for-branch', metavar='BRANCH', 
                       help='Update version for specific branch')
    parser.add_argument('--simple', action='store_true', 
                       help='Write simple version format for setuptools')
    parser.add_argument('--branch', help='Override current branch detection')
    
    args = parser.parse_args()
    
    try:
        vm = VersionManager()
        
        if args.get:
            print(vm.get_version_string())
        elif args.increment:
            new_data = vm.increment_version(args.increment, args.branch)
            vm.write_version_file(new_data)
            print(vm.get_version_string(new_data))
        elif args.update_for_branch is not None:
            version = vm.update_version_for_branch(args.update_for_branch)
            print(version)
        elif args.simple:
            vm.write_simple_version()
            print("Simple version written to VERSION file")
        else:
            print(vm.get_version_string())
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()