"""
Unit tests for the versioning system.

Simple test script to verify the versioning system works correctly.
"""

import sys
import os
import unittest
from pathlib import Path
from unittest import mock

# Add scripts directory to path
script_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(script_dir))

# Import test decorators
sys.path.insert(0, str(Path(__file__).parent.parent))
from tests.test_decorators import regression_test

from version_manager import VersionManager

class TestVersionManager(unittest.TestCase):
    """Unit tests for VersionManager."""

    def setUp(self):
        # Patch file operations in VersionManager to use in-memory dict
        self.patcher_open = mock.patch("builtins.open", new_callable=mock.mock_open)
        self.mock_open = self.patcher_open.start()
        self.addCleanup(self.patcher_open.stop)
        self.version_data = {
            'MAJOR': '1', 'MINOR': '2', 'PATCH': '0',
            'DEV_NUMBER': '', 'BUILD_NUMBER': '', 'BRANCH': 'main'
        }
        # Patch VersionManager methods that read/write files
        self.patcher_read = mock.patch.object(VersionManager, 'read_version_file', return_value=self.version_data.copy())
        self.mock_read = self.patcher_read.start()
        self.addCleanup(self.patcher_read.stop)
        self.patcher_write = mock.patch.object(VersionManager, 'write_version_file')
        self.mock_write = self.patcher_write.start()
        self.addCleanup(self.patcher_write.stop)
        self.patcher_write_simple = mock.patch.object(VersionManager, 'write_simple_version_file')
        self.mock_write_simple = self.patcher_write_simple.start()
        self.addCleanup(self.patcher_write_simple.stop)
        # Patch os.path.exists and Path.exists to always return True
        self.patcher_exists = mock.patch("os.path.exists", return_value=True)
        self.mock_exists = self.patcher_exists.start()
        self.addCleanup(self.patcher_exists.stop)
        self.patcher_path_exists = mock.patch("pathlib.Path.exists", return_value=True)
        self.mock_path_exists = self.patcher_path_exists.start()
        self.addCleanup(self.patcher_path_exists.stop)

    @regression_test
    def test_get_version_string(self):
        vm = VersionManager()
        version = vm.get_version_string(self.version_data)
        self.assertEqual(version, 'v1.2.0')

    @regression_test
    def test_feature_branch_creation_from_main(self):
        vm = VersionManager()
        self.mock_read.return_value = {
            'MAJOR': '1', 'MINOR': '2', 'PATCH': '0',
            'DEV_NUMBER': '', 'BUILD_NUMBER': '', 'BRANCH': 'main'
        }
        feat_version = vm.update_version_for_branch('feat/test-feature')
        self.assertEqual(feat_version, 'v1.3.0.dev0+build0')

    @regression_test
    def test_feature_branch_update_build_increment(self):
        vm = VersionManager()
        self.mock_read.return_value = {
            'MAJOR': '1', 'MINOR': '3', 'PATCH': '0',
            'DEV_NUMBER': '0', 'BUILD_NUMBER': '0', 'BRANCH': 'feat/test-feature'
        }
        feat_version2 = vm.update_version_for_branch('feat/test-feature')
        self.assertEqual(feat_version2, 'v1.3.0.dev0+build1')

    @regression_test
    def test_fix_branch_creation_from_main(self):
        vm = VersionManager()
        self.mock_read.return_value = {
            'MAJOR': '1', 'MINOR': '2', 'PATCH': '0',
            'DEV_NUMBER': '', 'BUILD_NUMBER': '', 'BRANCH': 'main'
        }
        fix_version = vm.update_version_for_branch('fix/test-fix')
        self.assertEqual(fix_version, 'v1.2.1.dev0+build0')

    @regression_test
    def test_fix_branch_update_build_increment(self):
        vm = VersionManager()
        self.mock_read.return_value = {
            'MAJOR': '1', 'MINOR': '2', 'PATCH': '1',
            'DEV_NUMBER': '0', 'BUILD_NUMBER': '0', 'BRANCH': 'fix/test-fix'
        }
        fix_version2 = vm.update_version_for_branch('fix/test-fix')
        self.assertEqual(fix_version2, 'v1.2.1.dev0+build1')

    @regression_test
    def test_switching_between_fix_branches_patch_increment(self):
        vm = VersionManager()
        self.mock_read.return_value = {
            'MAJOR': '1', 'MINOR': '2', 'PATCH': '1',
            'DEV_NUMBER': '0', 'BUILD_NUMBER': '1', 'BRANCH': 'fix/test-fix'
        }
        fix_version3 = vm.update_version_for_branch('fix/another-fix')
        self.assertTrue(fix_version3.startswith('v1.2.2'))
    
    @regression_test
    def test_dev_branch_from_main(self):
        vm = VersionManager()
        self.mock_read.return_value = {
            'MAJOR': '1', 'MINOR': '2', 'PATCH': '0',
            'DEV_NUMBER': '', 'BUILD_NUMBER': '', 'BRANCH': 'main'
        }
        dev_version = vm.update_version_for_branch('dev')
        self.assertEqual(dev_version, 'v1.3.0.dev0')
    
    @regression_test
    def test_dev_branch_from_feature_increment_dev_number(self):
        vm = VersionManager()
        self.mock_read.return_value = {
            'MAJOR': '1', 'MINOR': '3', 'PATCH': '0',
            'DEV_NUMBER': '0', 'BUILD_NUMBER': '2', 'BRANCH': 'feat/test-feature'
        }
        dev_version2 = vm.update_version_for_branch('dev')
        self.assertEqual(dev_version2, 'v1.3.0.dev1')
    
    @regression_test
    def test_main_branch_clears_dev_build(self):
        vm = VersionManager()
        self.mock_read.return_value = {
            'MAJOR': '1', 'MINOR': '3', 'PATCH': '0',
            'DEV_NUMBER': '2', 'BUILD_NUMBER': '1', 'BRANCH': 'dev'
        }
        main_version = vm.update_version_for_branch('main')
        self.assertEqual(main_version, 'v1.3.0')

def run_regression_tests():
    """Run all regression tests for versioning system.

    Returns:
        bool: True if all tests passed, False otherwise.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestVersionManager))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_regression_tests()
    if success:
        print("All versioning regression tests passed!")
    else:
        print("Some versioning regression tests failed.")
    exit(0 if success else 1)