"""Development tests for Phase 2: Internationalization (i18n) Infrastructure.

Tests the translation loader, settings registry i18n integration, and language switching functionality.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from hatchling.config.settings import AppSettings
from hatchling.config.settings_registry import SettingsRegistry
from hatchling.config.i18n import TranslationLoader, init_translation_loader, translate, set_language, get_available_languages


class TestTranslationLoader(unittest.TestCase):
    """Test the translation loader functionality."""
    
    def setUp(self):
        """Set up test environment with temporary translation files."""
        # Create temporary directory for test translations
        self.temp_dir = Path(tempfile.mkdtemp())
        self.languages_dir = self.temp_dir / "languages"
        self.languages_dir.mkdir()
        
        # Create test English translation file
        en_content = '''[meta]
language_code = "en"
language_name = "English"
version = "1.0.0"

[settings.llm.model]
name = "Model"
description = "LLM model to use"

[settings.ui.language]
name = "Language"
description = "Interface language"

[errors]
invalid_setting = "Invalid setting: {setting}"

[info]
setting_updated = "Setting '{setting}' updated to '{value}'"
'''
        (self.languages_dir / "en.toml").write_text(en_content)
        
        # Create test French translation file
        fr_content = '''[meta]
language_code = "fr"
language_name = "Français"
version = "1.0.0"

[settings.llm.model]
name = "Modèle"
description = "Modèle LLM à utiliser"

[settings.ui.language]
name = "Langue"
description = "Langue de l'interface"

[errors]
invalid_setting = "Paramètre invalide : {setting}"

[info]
setting_updated = "Paramètre '{setting}' mis à jour vers '{value}'"
'''
        (self.languages_dir / "fr.toml").write_text(fr_content, encoding='utf-8')
        
        # Initialize translation loader with test directory
        self.loader = TranslationLoader(self.languages_dir, "en")
    
    def tearDown(self):
        """Clean up temporary test files."""
        shutil.rmtree(self.temp_dir)
    
    def test_translation_loader_initialization(self):
        """Test that translation loader initializes correctly."""
        self.assertEqual(self.loader.default_language, "en")
        self.assertEqual(self.loader.current_language, "en")
        self.assertEqual(self.loader.languages_dir, self.languages_dir)
    
    def test_get_available_languages(self):
        """Test getting list of available languages."""
        languages = self.loader.get_available_languages()
        self.assertEqual(len(languages), 2)
        
        codes = [lang["code"] for lang in languages]
        self.assertIn("en", codes)
        self.assertIn("fr", codes)
        
        # Check English language info
        en_lang = next(lang for lang in languages if lang["code"] == "en")
        self.assertEqual(en_lang["name"], "English", f"Could not find 'name=English' language info: {en_lang}")
        
        # Check French language info
        fr_lang = next(lang for lang in languages if lang["code"] == "fr")
        self.assertEqual(fr_lang["name"], "Français", f"Could not find 'name=Français' language info: {fr_lang}")

    def test_translate_basic_keys(self):
        """Test basic translation functionality."""
        # Test English (default)
        result = self.loader.translate("settings.llm.model.name")
        self.assertEqual(result, "Model")
        
        result = self.loader.translate("settings.llm.model.description")
        self.assertEqual(result, "LLM model to use")
    
    def test_translate_with_language_parameter(self):
        """Test translation with explicit language parameter."""
        # Test French translation
        result = self.loader.translate("settings.llm.model.name", language="fr")
        self.assertEqual(result, "Modèle")
        
        result = self.loader.translate("settings.llm.model.description", language="fr")
        self.assertEqual(result, "Modèle LLM à utiliser")
    
    def test_translate_with_formatting(self):
        """Test translation with string formatting."""
        result = self.loader.translate("errors.invalid_setting", setting="test_setting")
        self.assertEqual(result, "Invalid setting: test_setting")
        
        result = self.loader.translate("info.setting_updated", setting="model", value="gpt-4")
        self.assertEqual(result, "Setting 'model' updated to 'gpt-4'")
    
    def test_translate_missing_key_fallback(self):
        """Test fallback behavior for missing translation keys."""
        # Key that doesn't exist should return the key itself
        result = self.loader.translate("nonexistent.key")
        self.assertEqual(result, "nonexistent.key")
    
    def test_set_language(self):
        """Test language switching."""
        # Switch to French
        success = self.loader.set_language("fr")
        self.assertTrue(success)
        self.assertEqual(self.loader.get_current_language(), "fr")
        
        # Test that translations now return French
        result = self.loader.translate("settings.llm.model.name")
        self.assertEqual(result, "Modèle")
        
        # Switch back to English
        success = self.loader.set_language("en")
        self.assertTrue(success)
        self.assertEqual(self.loader.get_current_language(), "en")
        
        # Test that translations return English again
        result = self.loader.translate("settings.llm.model.name")
        self.assertEqual(result, "Model")
    
    def test_set_invalid_language(self):
        """Test setting an invalid language code."""
        success = self.loader.set_language("invalid")
        self.assertFalse(success)
        # Should remain on current language
        self.assertEqual(self.loader.get_current_language(), "en")


class TestSettingsRegistryI18n(unittest.TestCase):
    """Test settings registry integration with i18n system."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test translations
        self.temp_dir = Path(tempfile.mkdtemp())
        self.languages_dir = self.temp_dir / "languages"
        self.languages_dir.mkdir()
        
        # Create comprehensive test translation files
        en_content = '''[meta]
language_code = "en"
language_name = "English"
version = "1.0.0"

[settings.categories]
llm = "LLM Configuration"
ui = "User Interface"

[settings.llm]
category_name = "LLM Configuration"
category_description = "Settings for Large Language Model"

[settings.llm.model]
name = "Model"
description = "LLM model to use for chat"
hint = "Example: gpt-4"

[settings.ui]
category_name = "User Interface"
category_description = "User interface settings"

[settings.ui.language]
name = "Language"
description = "Interface language code"
hint = "Language code like en, fr"

[errors]
language_not_found = "Language not found: {language}"

[info]
language_changed = "Language changed to {language}"
'''
        (self.languages_dir / "en.toml").write_text(en_content)
        
        fr_content = '''[meta]
language_code = "fr"
language_name = "Français"
version = "1.0.0"

[settings.categories]
llm = "Configuration LLM"
ui = "Interface Utilisateur"

[settings.llm]
category_name = "Configuration LLM"
category_description = "Paramètres pour le modèle de langage"

[settings.llm.model]
name = "Modèle"
description = "Modèle LLM pour le chat"
hint = "Exemple : gpt-4"

[settings.ui]
category_name = "Interface Utilisateur"
category_description = "Paramètres de l'interface utilisateur"

[settings.ui.language]
name = "Langue"
description = "Code de langue de l'interface"
hint = "Code de langue comme en, fr"

[errors]
language_not_found = "Langue introuvable : {language}"

[info]
language_changed = "Langue changée vers {language}"
'''
        (self.languages_dir / "fr.toml").write_text(fr_content, encoding='utf-8')
        
        # Initialize translation loader with test directory
        init_translation_loader(self.languages_dir, "en")
        
        # Create app settings and registry
        self.app_settings = AppSettings()
        self.registry = SettingsRegistry(self.app_settings)
    
    def tearDown(self):
        """Clean up temporary test files."""
        shutil.rmtree(self.temp_dir)
    
    def test_settings_list_with_translations(self):
        """Test that settings list includes translated display names."""
        settings_list = self.registry.list_settings()
        
        # Find LLM model setting
        llm_model = next(s for s in settings_list if s['category_name'] == 'llm' and s['name'] == 'model')
        
        # Check that translated fields are present
        self.assertIn('display_name', llm_model)
        self.assertIn('category_display_name', llm_model)
        self.assertIn('category_description', llm_model)
        
        # Check English translations
        self.assertEqual(llm_model['display_name'], "Model")
        self.assertEqual(llm_model['category_display_name'], "LLM Configuration")
        self.assertEqual(llm_model['description'], "LLM model to use for chat")
    
    def test_language_switching_updates_translations(self):
        """Test that changing language updates all translated content."""
        # Get initial English translations
        settings_list = self.registry.list_settings()
        llm_model = next(s for s in settings_list if s['category_name'] == 'llm' and s['name'] == 'model')
        self.assertEqual(llm_model['display_name'], "Model")
        
        # Switch to French
        success = self.registry.set_language("fr")
        self.assertTrue(success)
        
        # Get updated translations
        settings_list = self.registry.list_settings()
        llm_model = next(s for s in settings_list if s['category_name'] == 'llm' and s['name'] == 'model')
        
        # Check French translations
        self.assertEqual(llm_model['display_name'], "Modèle")
        self.assertEqual(llm_model['category_display_name'], "Configuration LLM")
        self.assertEqual(llm_model['description'], "Modèle LLM pour le chat")
    
    def test_get_available_languages_from_registry(self):
        """Test getting available languages through registry."""
        languages = self.registry.get_available_languages()
        self.assertEqual(len(languages), 2)
        
        codes = [lang["code"] for lang in languages]
        self.assertIn("en", codes)
        self.assertIn("fr", codes)
    
    def test_get_current_language_from_registry(self):
        """Test getting current language through registry."""
        current = self.registry.get_current_language()
        self.assertEqual(current, "en")  # Should match UI settings default
    
    def test_invalid_language_handling(self):
        """Test handling of invalid language codes."""
        with self.assertRaises(ValueError) as context:
            self.registry.set_language("invalid")
        
        # Should contain error message about language not found
        self.assertIn("Language not found", str(context.exception))


class TestGlobalI18nFunctions(unittest.TestCase):
    """Test global i18n convenience functions."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test translations
        self.temp_dir = Path(tempfile.mkdtemp())
        self.languages_dir = self.temp_dir / "languages"
        self.languages_dir.mkdir()
        
        # Create minimal test translation
        en_content = '''[meta]
language_code = "en"
language_name = "English"

[test]
message = "Hello, {name}!"
'''
        (self.languages_dir / "en.toml").write_text(en_content)
        
        # Initialize with test directory
        init_translation_loader(self.languages_dir, "en")
    
    def tearDown(self):
        """Clean up temporary test files."""
        shutil.rmtree(self.temp_dir)
    
    def test_global_translate_function(self):
        """Test global translate function."""
        result = translate("test.message", name="World")
        self.assertEqual(result, "Hello, World!")
    
    def test_global_get_available_languages(self):
        """Test global get_available_languages function."""
        languages = get_available_languages()
        self.assertEqual(len(languages), 1)
        self.assertEqual(languages[0]["code"], "en")
    
    def test_global_set_language(self):
        """Test global set_language function."""
        # This should fail since we only have English
        success = set_language("fr")
        self.assertFalse(success)
        
        # English should work
        success = set_language("en")
        self.assertTrue(success)


def run_phase2_tests():
    """Run all Phase 2 development tests using unittest.
    
    Returns:
        bool: True if all tests passed, False otherwise.
    """
    import unittest
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestTranslationLoader))
    suite.addTests(loader.loadTestsFromTestCase(TestSettingsRegistryI18n))
    suite.addTests(loader.loadTestsFromTestCase(TestGlobalI18nFunctions))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    unittest.main()
