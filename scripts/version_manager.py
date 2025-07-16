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
            for key in ['MAJOR', 'MINOR', 'PATCH', 'PRERELEASE', 'BUILD', 'BRANCH']:
                value = version_data.get(key, '')
                f.write(f"{key}={value}\n")
    
    def get_version_string(self, version_data: Optional[Dict[str, str]] = None) -> str:
        """Generate semantic version string from version data."""
        if version_data is None:
            version_data = self.read_version_file()
        
        major = version_data.get('MAJOR', '1')
        minor = version_data.get('MINOR', '0')
        patch = version_data.get('PATCH', '0')
        prerelease = version_data.get('PRERELEASE', '')
        build = version_data.get('BUILD', '')
        
        version = f"v{major}.{minor}.{patch}"
        
        if prerelease:
            version += f"-{prerelease}"
        
        if build:
            version += f".{build}"
        
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
        build_str = version_data.get('BUILD', '')
        if build_str.startswith('b'):
            build_num = int(build_str[1:]) if build_str[1:] else 0
        else:
            build_num = int(build_str) if build_str else 0
        
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
        elif increment_type == 'build':
            build_num += 1
        
        # Set prerelease based on branch
        prerelease = ""
        build = ""
        
        if branch == 'main':
            # Main branch gets clean releases
            prerelease = ""
            build = ""
        elif branch == 'dev':
            # Dev branch gets dev prerelease
            prerelease = "dev"
            build = ""
        elif branch.startswith('feat/'):
            # Feature branches get dev prerelease with build number
            prerelease = "dev"
            if increment_type == 'build':
                build = f"b{build_num}"
            else:
                build = f"b{build_num}"
        elif branch.startswith('fix/'):
            # Fix branches get dev prerelease with build number
            prerelease = "dev"
            if increment_type == 'build':
                build = f"b{build_num}"
            else:
                build = f"b{build_num}"
        else:
            # Other branches get dev prerelease
            prerelease = "dev"
            build = ""
        
        return {
            'MAJOR': str(major),
            'MINOR': str(minor),
            'PATCH': str(patch),
            'PRERELEASE': prerelease,
            'BUILD': build,
            'BRANCH': branch
        }
    
    def update_version_for_branch(self, branch: str = None) -> str:
        """Update version based on branch type."""
        if branch is None:
            branch = self.get_current_branch()
        
        current_data = self.read_version_file()
        
        if branch.startswith('feat/'):
            # Feature branch: increment minor version
            new_data = self.increment_version('minor', branch)
        elif branch.startswith('fix/'):
            # Fix branch: increment patch version
            new_data = self.increment_version('patch', branch)
        elif branch in ['main', 'dev']:
            # Main or dev branch: keep current version, update prerelease
            new_data = current_data.copy()
            new_data['BRANCH'] = branch
            if branch == 'main':
                new_data['PRERELEASE'] = ''
                new_data['BUILD'] = ''
            elif branch == 'dev':
                new_data['PRERELEASE'] = 'dev'
                new_data['BUILD'] = ''
        else:
            # Other branches: treat as dev
            new_data = current_data.copy()
            new_data['BRANCH'] = branch
            new_data['PRERELEASE'] = 'dev'
            new_data['BUILD'] = ''
        
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
    parser.add_argument('--increment', choices=['major', 'minor', 'patch', 'build'], 
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