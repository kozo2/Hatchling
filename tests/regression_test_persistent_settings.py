"""Regression tests for persistent settings functionality in Hatchling.

These tests ensure that persistent settings (load/save) and cache/settings directory configuration
work as expected and remain stable across updates.
"""


import os
import tempfile
from pathlib import Path
import unittest

from tests.test_decorators import regression_test

from hatchling.config.settings import AppSettings
from hatchling.config.settings_registry import SettingsRegistry


class TestPersistentSettingsRegression(unittest.TestCase):
    """Regression tests for persistent settings and directory configuration."""

    def setUp(self):
        """Set up a temporary directory and patch environment variables before each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self._original_env = dict(os.environ)

    def tearDown(self):
        """Clean up the temporary directory and restore environment variables after each test."""
        self.temp_dir.cleanup()
        # Restore environment variables
        os.environ.clear()
        os.environ.update(self._original_env)

    @regression_test
    def test_persistent_settings_save_and_load(self):
        """Test that settings are saved and loaded persistently across sessions."""
        os.environ['HATCHLING_SETTINGS_DIR'] = str(Path(self.temp_dir.name) / "settings")
        registry = SettingsRegistry()

        # Change Ollama ip and port and save
        original_ip = registry.get_setting('ollama', 'ip')['current_value']
        original_port = registry.get_setting('ollama', 'port')['current_value']
        registry.set_setting('ollama', 'ip', 'regression-test-ip', True)
        registry.set_setting('ollama', 'port', 12345, True)
        self.assertTrue(registry.save_persistent_settings(), "Should save persistent settings successfully")

        # Reset and reload
        registry.set_setting('ollama', 'ip', original_ip, True)
        registry.set_setting('ollama', 'port', original_port, True)
        self.assertTrue(registry.load_persistent_settings(), "Should load settings from file after save")
        self.assertEqual(registry.get_setting('ollama', 'ip')['current_value'], 'regression-test-ip', "IP should persist after reload")
        self.assertEqual(registry.get_setting('ollama', 'port')['current_value'], 12345, "Port should persist after reload")

    @regression_test
    def test_cache_and_settings_dir_env_vars(self):
        """Test that cache and settings directories are settable via environment variables and are read-only after init."""
        cache_dir = Path(self.temp_dir.name) / "mycache"
        settings_dir = Path(self.temp_dir.name) / "mysettings"
        os.environ['HATCHLING_CACHE_DIR'] = str(cache_dir)
        os.environ['HATCHLING_SETTINGS_DIR'] = str(settings_dir)
        settings = AppSettings()
        self.assertEqual(settings.paths.hatchling_cache_dir, cache_dir)
        self.assertEqual(settings.paths.hatchling_settings_dir, settings_dir)
        # Try to change after init (should not change)
        os.environ['HATCHLING_CACHE_DIR'] = str(Path(self.temp_dir.name) / "othercache")
        self.assertEqual(settings.paths.hatchling_cache_dir, cache_dir, "Cache dir should be read-only after init")

    @regression_test
    def test_persistent_settings_file_content(self):
        """Test that the persistent settings file contains the expected data."""
        os.environ['HATCHLING_SETTINGS_DIR'] = str(Path(self.temp_dir.name) / "settings")
        registry = SettingsRegistry()
        registry.set_setting('ollama', 'ip', 'file-content-test-ip', True)
        registry.set_setting('ollama', 'port', 54321, True)
        registry.save_persistent_settings()
        settings_file = registry.get_persistent_settings_file_path()
        self.assertTrue(settings_file.exists(), "Settings file should exist after save")
        content = settings_file.read_text()
        self.assertIn('file-content-test-ip', content, "Saved IP value should appear in settings file")
        self.assertIn('54321', content, "Saved port value should appear in settings file")

def run_regression_tests():
    """Run all regression tests for persistent settings."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestPersistentSettingsRegression))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_regression_tests()
    if success:
        print("All regression tests passed!")
    else:
        print("Some regression tests failed.")
    exit(0 if success else 1)
