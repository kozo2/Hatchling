"""
Regression tests for the semantic-release versioning system.

Tests to verify the semantic-release configuration and integration works correctly.
"""

import sys
import os
import unittest
import json
import toml
from pathlib import Path

# Import test decorators
sys.path.insert(0, str(Path(__file__).parent.parent))
from tests.test_decorators import regression_test

class TestSemanticReleaseConfiguration(unittest.TestCase):
    """Regression tests for semantic-release configuration."""

    def setUp(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).parent.parent
        self.releaserc_path = self.project_root / ".releaserc.json"
        self.pyproject_path = self.project_root / "pyproject.toml"
        self.package_json_path = self.project_root / "package.json"

    @regression_test
    def test_releaserc_configuration_exists(self):
        """Test that .releaserc.json exists and is valid."""
        self.assertTrue(self.releaserc_path.exists(), 
                       ".releaserc.json configuration file should exist")
        
        with open(self.releaserc_path, 'r') as f:
            config = json.load(f)
        
        # Verify essential configuration
        self.assertIn("repositoryUrl", config, 
                     "repositoryUrl should be configured")
        self.assertIn("branches", config, 
                     "branches should be configured")
        self.assertIn("plugins", config, 
                     "plugins should be configured")

    @regression_test
    def test_branch_configuration(self):
        """Test that branch configuration includes main and dev branches."""
        with open(self.releaserc_path, 'r') as f:
            config = json.load(f)
        
        branches = config.get("branches", [])
        branch_names = []
        
        for branch in branches:
            if isinstance(branch, str):
                branch_names.append(branch)
            elif isinstance(branch, dict) and "name" in branch:
                branch_names.append(branch["name"])
        
        self.assertIn("main", branch_names, 
                     "main branch should be configured for releases")
        self.assertIn("dev", branch_names, 
                     "dev branch should be configured for pre-releases")

    @regression_test
    def test_required_plugins_configured(self):
        """Test that required semantic-release plugins are configured."""
        with open(self.releaserc_path, 'r') as f:
            config = json.load(f)
        
        plugins = config.get("plugins", [])
        plugin_names = []
        
        for plugin in plugins:
            if isinstance(plugin, str):
                plugin_names.append(plugin)
            elif isinstance(plugin, list) and len(plugin) > 0:
                plugin_names.append(plugin[0])
        
        # Essential plugins for semantic-release
        required_plugins = [
            "@semantic-release/commit-analyzer",
            "@semantic-release/release-notes-generator",
            "@semantic-release/changelog",
            "@semantic-release/git",
            "@semantic-release/github"
        ]
        
        for required_plugin in required_plugins:
            self.assertIn(required_plugin, plugin_names, 
                         f"Required plugin {required_plugin} should be configured")

    @regression_test
    def test_pyproject_toml_has_version(self):
        """Test that pyproject.toml contains a version field."""
        self.assertTrue(self.pyproject_path.exists(), 
                       "pyproject.toml should exist")
        
        with open(self.pyproject_path, 'r') as f:
            config = toml.load(f)
        
        self.assertIn("project", config, 
                     "project section should exist in pyproject.toml")
        self.assertIn("version", config["project"], 
                     "version should be specified in project section")
        
        version = config["project"]["version"]
        self.assertIsInstance(version, str, 
                            "version should be a string")
        self.assertTrue(version, 
                       "version should not be empty")

    @regression_test
    def test_package_json_has_semantic_release_dependencies(self):
        """Test that package.json includes semantic-release dependencies."""
        self.assertTrue(self.package_json_path.exists(), 
                       "package.json should exist for semantic-release")
        
        with open(self.package_json_path, 'r') as f:
            config = json.load(f)
        
        # Check devDependencies for semantic-release
        dev_deps = config.get("devDependencies", {})
        
        self.assertIn("semantic-release", dev_deps, 
                     "semantic-release should be in devDependencies")
        self.assertIn("@semantic-release/changelog", dev_deps, 
                     "@semantic-release/changelog should be in devDependencies")
        self.assertIn("@semantic-release/git", dev_deps, 
                     "@semantic-release/git should be in devDependencies")

    @regression_test
    def test_conventional_commits_configuration(self):
        """Test that conventional commits preset is configured."""
        with open(self.releaserc_path, 'r') as f:
            config = json.load(f)
        
        plugins = config.get("plugins", [])
        
        # Find commit-analyzer plugin configuration
        commit_analyzer_config = None
        for plugin in plugins:
            if isinstance(plugin, list) and len(plugin) >= 2:
                if plugin[0] == "@semantic-release/commit-analyzer":
                    commit_analyzer_config = plugin[1]
                    break
        
        self.assertIsNotNone(commit_analyzer_config, 
                           "commit-analyzer should have configuration")
        self.assertEqual(commit_analyzer_config.get("preset"), "conventionalcommits", 
                       "commit-analyzer should use conventionalcommits preset")

    @regression_test
    def test_version_format_is_semantic(self):
        """Test that the current version follows semantic versioning format."""
        with open(self.pyproject_path, 'r') as f:
            config = toml.load(f)
        
        version = config["project"]["version"]

        # Basic semantic version regex: MAJOR.MINOR.PATCH with optional pre-release and build
        import re
        # Use a simpler, well-formed pattern to validate semantic-like versions (covers common valid forms)
        semver_pattern = r'^\d+\.\d+\.\d+(?:-[0-9A-Za-z-.]+)?(?:\+[0-9A-Za-z-.]+)?$'

        self.assertTrue(re.match(semver_pattern, version),
                f"Version {version} should follow semantic versioning format")

def run_regression_tests():
    """Run all regression tests for semantic-release versioning system.

    Returns:
        bool: True if all tests passed, False otherwise.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestSemanticReleaseConfiguration))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_regression_tests()
    if success:
        print("All semantic-release versioning regression tests passed!")
    else:
        print("Some semantic-release versioning regression tests failed.")
    exit(0 if success else 1)