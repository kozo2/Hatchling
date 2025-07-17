#!/usr/bin/env python3
"""
Version management script for Hatchling with dual-file system.

This script manages two version files:
- VERSION.meta: Structured, human-readable format with detailed version components
- VERSION: Simple format for setuptools compatibility

The dual-file system preserves detailed version information while maintaining
compatibility with Python packaging tools.
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
        self.version_meta_file = Path(str(version_file_path) + ".meta")
        
        # Check if we have a structured meta file, otherwise try to read from VERSION
        if not self.version_meta_file.exists() and not self.version_file.exists():
            raise FileNotFoundError(f"Neither VERSION file nor VERSION.meta found at {version_file_path}")
        
        # If VERSION.meta doesn't exist but VERSION does, create it from current VERSION
        if not self.version_meta_file.exists() and self.version_file.exists():
            self._create_meta_from_simple_version()
    
    def _create_meta_from_simple_version(self) -> None:
        """Create VERSION.meta from a simple VERSION file if it doesn't exist."""
        try:
            with open(self.version_file, 'r') as f:
                simple_version = f.read().strip()
            
            # Parse the simple version string to extract components
            # Example: "0.4.0.dev0+build0" -> MAJOR=0, MINOR=4, PATCH=0, DEV_NUMBER=0, BUILD_NUMBER=0
            version_parts = simple_version.replace('+build', '.build').replace('.dev', '.dev').split('.')
            
            major, minor, patch = version_parts[0], version_parts[1], version_parts[2]
            dev_number = ""
            build_number = ""
            
            for part in version_parts[3:]:
                if part.startswith('dev'):
                    dev_number = part[3:]
                elif part.startswith('build'):
                    build_number = part[5:]
            
            # Get current branch
            branch = self.get_current_branch()
            
            # Write structured format to VERSION.meta
            version_data = {
                'MAJOR': major,
                'MINOR': minor,
                'PATCH': patch,
                'DEV_NUMBER': dev_number,
                'BUILD_NUMBER': build_number,
                'BRANCH': branch
            }
            self.write_version_meta_file(version_data)
            
        except Exception as e:
            # If we can't parse, create a default meta file
            default_data = {
                'MAJOR': '0',
                'MINOR': '0',
                'PATCH': '0',
                'DEV_NUMBER': '',
                'BUILD_NUMBER': '',
                'BRANCH': self.get_current_branch()
            }
            self.write_version_meta_file(default_data)
    
    def read_version_file(self) -> Dict[str, str]:
        """Read the VERSION.meta file and parse version components."""
        version_data = {}
        
        # Always read from VERSION.meta for structured data
        if self.version_meta_file.exists():
            with open(self.version_meta_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        version_data[key.strip()] = value.strip()
        else:
            # Fallback: try to create from simple VERSION file
            self._create_meta_from_simple_version()
            return self.read_version_file()
        
        return version_data
    
    def write_version_file(self, version_data: Dict[str, str]) -> None:
        """Write version data to both VERSION.meta (structured) and VERSION (simple)."""
        # Write structured format to VERSION.meta
        self.write_version_meta_file(version_data)
        
        # Write simple format to VERSION for setuptools compatibility
        self.write_simple_version_file(version_data)
    
    def write_version_meta_file(self, version_data: Dict[str, str]) -> None:
        """Write version data to VERSION.meta in structured format."""
        with open(self.version_meta_file, 'w') as f:
            f.write("# Structured version file for human readability and CI/CD\n")
            f.write("# This file maintains detailed version component information\n")
            f.write("# The companion VERSION file contains the simple format for setuptools\n\n")
            for key in ['MAJOR', 'MINOR', 'PATCH', 'DEV_NUMBER', 'BUILD_NUMBER', 'BRANCH']:
                value = version_data.get(key, '')
                f.write(f"{key}={value}\n")
    
    def write_simple_version_file(self, version_data: Optional[Dict[str, str]] = None) -> None:
        """Write a simple version string to VERSION file for setuptools compatibility."""
        if version_data is None:
            version_data = self.read_version_file()
        
        version_string = self.get_version_string(version_data)
        # Remove 'v' prefix for setuptools
        simple_version = version_string.lstrip('v')
        
        # Write to VERSION file in simple format for setuptools
        with open(self.version_file, 'w') as f:
            f.write(simple_version)
    
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
        new_data = current_data.copy()

        if branch.startswith('feat/'):

            if current_data.get('BRANCH') == 'main': #it means we are creating a new feature branch
                #increment minor version
                new_data = self.increment_version('minor', branch) #takes care of incrementing and updating the branch field
                new_data['DEV_NUMBER'] = '0'  # Reset dev number for new feature branch
                new_data['BUILD_NUMBER'] = '0'  # Start with build0

            else: #it means we are updating an existing feature branch, whether from dev or `feat/`
                # Increment build number for the same feature branch
                new_data = self.increment_version('build', branch) 

        elif branch.startswith('fix/'):
            # If current branch is the same as the one in VERSION.meta,
            # increment the build number
            if current_data.get('BRANCH') == branch:
                # Increment build number for the same fix branch
                new_data = self.increment_version('build', branch)
            
            # If the current branch is a fix branch but not the same as the one in VERSION.meta,
            # increment the patch version, but don't change the build number
            elif current_data.get('BRANCH').startswith('fix/'):
                new_data = self.increment_version('patch', branch)
            
            else: #it means we are creating a new fix branch
                new_data = self.increment_version('patch', branch) #takes care of incrementing and updating the branch field
                new_data['BUILD_NUMBER'] = '0'  # Start with build0
        
        elif branch == 'main':
            # Main branch gets clean releases
            new_data = current_data.copy()
            new_data['DEV_NUMBER'] = ''
            new_data['BUILD_NUMBER'] = ''

        else: # Dev and other branches
            # If starting from main (there was a rebased dev on a clean
            # release), reset dev and build numbers
            if current_data.get('BRANCH') == 'main':
                new_data = self.increment_version('minor', branch)
                new_data['DEV_NUMBER'] = '0'
            
            # If updating from another branch (fix, feat, dev itself, or docs, etc.),
            # increment dev number and reset build number
            else:
                new_data = self.increment_version('dev', branch)
            
            new_data['BUILD_NUMBER'] = ''

        # Update branch field
        new_data['BRANCH'] = branch
        
        self.write_version_file(new_data)
        return self.get_version_string(new_data)
    
    def write_simple_version(self) -> None:
        """Write a simple version string for setuptools compatibility."""
        version_data = self.read_version_file()
        self.write_simple_version_file(version_data)


def main():
    parser = argparse.ArgumentParser(description='Manage project version using dual-file system (VERSION.meta + VERSION)')
    parser.add_argument('--get', action='store_true', help='Get current version string')
    parser.add_argument('--increment', choices=['major', 'minor', 'patch', 'dev', 'build'], 
                       help='Increment version component (updates both VERSION.meta and VERSION)')
    parser.add_argument('--update-for-branch', metavar='BRANCH', 
                       help='Update version for specific branch (updates both files)')
    parser.add_argument('--simple', action='store_true', 
                       help='Write simple version format to VERSION file (from VERSION.meta)')
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