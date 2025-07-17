#!/usr/bin/env python3
"""
Simple test script to verify the versioning system works correctly.
"""

import sys
import os
from pathlib import Path

# Add scripts directory to path
script_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(script_dir))

from version_manager import VersionManager

def test_version_manager():
    """Test the version manager functionality."""
    print("Testing Version Manager...")
    
    vm = VersionManager()
    
    # Test getting version
    version = vm.get_version_string()
    print(f"Current version: {version}")
    
    # Test feature branch versioning
    print("\nTesting feature branch versioning...")
    feat_version = vm.update_version_for_branch('feat/test-feature')
    print(f"Feature branch version: {feat_version}")
    assert '.dev' in feat_version, f"Expected dev in feature version, got {feat_version}"
    
    # Test fix branch versioning
    print("\nTesting fix branch versioning...")
    fix_version = vm.update_version_for_branch('fix/test-fix')
    print(f"Fix branch version: {fix_version}")
    assert '.dev' in fix_version, f"Expected dev in fix version, got {fix_version}"
    
    # Test build increment
    print("\nTesting build increment...")
    build_data = vm.increment_version('build', 'feat/test-feature')
    build_version = vm.get_version_string(build_data)
    print(f"Build incremented version: {build_version}")
    assert '+build' in build_version, f"Expected +build in build version, got {build_version}"
    
    # Test dev branch
    print("\nTesting dev branch...")
    dev_data = {'MAJOR': '1', 'MINOR': '2', 'PATCH': '0', 'DEV_NUMBER': '3', 'BUILD_NUMBER': '', 'BRANCH': 'dev'}
    dev_version = vm.get_version_string(dev_data)
    print(f"Dev branch version: {dev_version}")
    assert dev_version == 'v1.2.0.dev3', f"Expected v1.2.0.dev3, got {dev_version}"
    
    # Test main branch
    print("\nTesting main branch...")
    main_data = {'MAJOR': '1', 'MINOR': '2', 'PATCH': '0', 'DEV_NUMBER': '', 'BUILD_NUMBER': '', 'BRANCH': 'main'}
    main_version = vm.get_version_string(main_data)
    print(f"Main branch version: {main_version}")
    assert main_version == 'v1.2.0', f"Expected v1.2.0, got {main_version}"
    
    print("\n✅ All version manager tests passed!")

def test_version_examples():
    """Test the examples from the issue description."""
    print("\nTesting issue examples...")
    
    vm = VersionManager()
    
    # Example 1: Feature Branch
    print("\nExample 1: Feature Branch")
    # Simulate dev version v1.2.0.dev0
    vm.write_version_file({'MAJOR': '1', 'MINOR': '2', 'PATCH': '0', 'DEV_NUMBER': '0', 'BUILD_NUMBER': '', 'BRANCH': 'dev'})
    
    # Create feature branch
    feat_version = vm.update_version_for_branch('feat/new-feature')
    print(f"Feature branch initial: {feat_version}")
    assert feat_version == 'v1.3.0.dev0+build0', f"Expected v1.3.0.dev0+build0, got {feat_version}"
    
    # Increment build
    incremented = vm.increment_version('build', 'feat/new-feature')
    vm.write_version_file(incremented)
    build_version = vm.get_version_string()
    print(f"After push: {build_version}")
    assert build_version == 'v1.3.0.dev0+build1', f"Expected v1.3.0.dev0+build1, got {build_version}"
    
    # Example 2: Fix Branch
    print("\nExample 2: Fix Branch")
    # Reset to dev version v1.2.0.dev0
    vm.write_version_file({'MAJOR': '1', 'MINOR': '2', 'PATCH': '0', 'DEV_NUMBER': '0', 'BUILD_NUMBER': '', 'BRANCH': 'dev'})
    
    # Create fix branch
    fix_version = vm.update_version_for_branch('fix/bug-fix')
    print(f"Fix branch initial: {fix_version}")
    assert fix_version == 'v1.2.1.dev0+build0', f"Expected v1.2.1.dev0+build0, got {fix_version}"
    
    # Increment build
    incremented = vm.increment_version('build', 'fix/bug-fix')
    vm.write_version_file(incremented)
    build_version = vm.get_version_string()
    print(f"After push: {build_version}")
    assert build_version == 'v1.2.1.dev0+build1', f"Expected v1.2.1.dev0+build1, got {build_version}"
    
    print("\n✅ All example tests passed!")

if __name__ == '__main__':
    try:
        test_version_manager()
        test_version_examples()
        print("\n🎉 All tests passed! Versioning system is working correctly.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)