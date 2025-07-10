import unittest
import json
from pathlib import Path
from hatchling.config.settings import AppSettings, LLMSettings, PathSettings, ToolCallingSettings, UISettings, SettingAccessLevel
from hatchling.config.settings_registry import SettingsRegistry
from pydantic import ValidationError

class TestSettingsModels(unittest.TestCase):
    def test_llm_settings_creation(self):
        llm_settings = LLMSettings()
        self.assertEqual(llm_settings.api_url, "http://localhost:11434/api")
        self.assertEqual(llm_settings.model, "mistral-small3.1")

    def test_path_settings_validation(self):
        path_settings = PathSettings()
        self.assertIsInstance(path_settings.envs_dir, Path)
        self.assertTrue(str(path_settings.envs_dir.as_posix()).endswith(".hatch/envs"), f"Expected envs_dir to end with '.hatch/envs', got {path_settings.envs_dir}")

    def test_tool_calling_settings_validation(self):
        tool_settings = ToolCallingSettings(max_iterations=10, max_working_time=60.0)
        self.assertEqual(tool_settings.max_iterations, 10)
        self.assertEqual(tool_settings.max_working_time, 60.0)
        with self.assertRaises(ValidationError):
            ToolCallingSettings(max_iterations=0)
        with self.assertRaises(ValidationError):
            ToolCallingSettings(max_iterations=150)
        with self.assertRaises(ValidationError):
            ToolCallingSettings(max_working_time=0.0)
        with self.assertRaises(ValidationError):
            ToolCallingSettings(max_working_time=400.0)

    def test_ui_settings_creation(self):
        ui_settings = UISettings()
        self.assertEqual(ui_settings.language, "en")
        ui_settings_custom = UISettings(language="fr")
        self.assertEqual(ui_settings_custom.language, "fr")

    def test_app_settings_aggregation(self):
        app_settings = AppSettings()
        self.assertIsInstance(app_settings.llm, LLMSettings)
        self.assertIsInstance(app_settings.paths, PathSettings)
        self.assertIsInstance(app_settings.tool_calling, ToolCallingSettings)
        self.assertIsInstance(app_settings.ui, UISettings)

class TestSettingsRegistry(unittest.TestCase):
    def setUp(self):
        self.app_settings = AppSettings()
        self.registry = SettingsRegistry(self.app_settings)

    def test_list_all_settings(self):
        settings_list = self.registry.list_settings()
        categories = {s['category'] for s in settings_list}
        expected_categories = {'llm', 'paths', 'tool_calling', 'ui'}
        self.assertEqual(categories, expected_categories)
        setting_names = {f"{s['category']}:{s['name']}" for s in settings_list}
        expected_settings = {
            'llm:api_url', 'llm:model',
            'paths:envs_dir',
            'tool_calling:max_iterations', 'tool_calling:max_working_time',
            'ui:language'
        }
        self.assertEqual(setting_names, expected_settings)

    def test_get_setting_valid(self):
        setting_info = self.registry.get_setting('llm', 'model')
        self.assertEqual(setting_info['category'], 'llm')
        self.assertEqual(setting_info['name'], 'model')
        self.assertEqual(setting_info['current_value'], 'mistral-small3.1')
        self.assertEqual(setting_info['access_level'], SettingAccessLevel.NORMAL)
        self.assertIn('description', setting_info)

    def test_get_setting_invalid(self):
        with self.assertRaises(ValueError):
            self.registry.get_setting('invalid', 'setting')

    def test_set_setting_normal_access(self):
        result = self.registry.set_setting('llm', 'model', 'gpt-4')
        self.assertTrue(result)
        updated_info = self.registry.get_setting('llm', 'model')
        self.assertEqual(updated_info['current_value'], 'gpt-4')

    def test_set_setting_protected_without_force(self):
        with self.assertRaises(ValueError):
            self.registry.set_setting('llm', 'api_url', 'http://new-url.com')

    def test_set_setting_protected_with_force(self):
        result = self.registry.set_setting('llm', 'api_url', 'http://new-url.com', force=True)
        self.assertTrue(result)
        updated_info = self.registry.get_setting('llm', 'api_url')
        self.assertEqual(updated_info['current_value'], 'http://new-url.com')

    def test_set_setting_read_only(self):
        with self.assertRaises(ValueError):
            self.registry.set_setting('paths', 'envs_dir', '/new/path')
        with self.assertRaises(ValueError):
            self.registry.set_setting('paths', 'envs_dir', '/new/path', force=True)

    def test_set_setting_invalid_value(self):
        with self.assertRaises(ValidationError):
            self.registry.set_setting('tool_calling', 'max_iterations', -1)

    def test_reset_setting(self):
        self.registry.set_setting('llm', 'model', 'gpt-4')
        result = self.registry.reset_setting('llm', 'model')
        self.assertTrue(result)
        updated_info = self.registry.get_setting('llm', 'model')
        self.assertEqual(updated_info['current_value'], 'mistral-small3.1')

    def test_export_settings_json(self):
        exported = self.registry.export_settings('json')
        parsed = json.loads(exported)
        self.assertIn('llm', parsed)
        self.assertIn('paths', parsed)
        self.assertIn('tool_calling', parsed)
        self.assertIn('ui', parsed)

    def test_import_settings_json(self):
        settings_data = {
            "llm": {"model": "gpt-4"},
            "ui": {"language": "fr"}
        }
        report = self.registry.import_settings(json.dumps(settings_data), 'json')
        self.assertIn('llm:model', report['successful'])
        self.assertIn('ui:language', report['successful'])
        llm_info = self.registry.get_setting('llm', 'model')
        self.assertEqual(llm_info['current_value'], 'gpt-4')
        ui_info = self.registry.get_setting('ui', 'language')
        self.assertEqual(ui_info['current_value'], 'fr')

    def test_search_exact_match(self):
        results = self.registry.list_settings('llm')
        categories = {s['category'] for s in results}
        self.assertEqual(categories, {'llm'})

    def test_search_fuzzy_match(self):
        results = self.registry.list_settings('model')
        setting_names = {f"{s['category']}:{s['name']}" for s in results}
        self.assertIn('llm:model', setting_names)


def run_phase1_tests():
    """Run all Phase 1 development tests using unittest."""
    import unittest
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestSettingsModels))
    suite.addTests(loader.loadTestsFromTestCase(TestSettingsRegistry))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    unittest.main()
