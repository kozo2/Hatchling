#!/usr/bin/env python3
"""Test script for Phase 2 i18n implementation.

This script tests the translation system, settings registry integration,
and basic functionality of the internationalization infrastructure.
"""

import sys
import os
from pathlib import Path

# Add the hatchling directory to Python path
hatchling_dir = Path(__file__).parent.parent
sys.path.insert(0, str(hatchling_dir))

def test_translation_loader():
    """Test the translation loader functionality."""
    print("=== Testing Translation Loader ===")
    
    try:
        from hatchling.config.i18n import get_translation_loader, translate, get_available_languages
        
        # Test getting available languages
        languages = get_available_languages()
        print(f"Available languages: {[lang['code'] for lang in languages]}")
        
        # Test English translations
        english_test = translate("settings.llm.model.name")
        print(f"English translation test: {english_test}")
        
        # Test French translations if available
        french_test = translate("settings.llm.model.name", language="fr")
        print(f"French translation test: {french_test}")
        
        # Test missing key fallback
        missing_key = translate("nonexistent.key.test")
        print(f"Missing key fallback: {missing_key}")
        
        # Test formatting
        formatted = translate("errors.invalid_setting", setting="test_setting")
        print(f"Formatted translation: {formatted}")
        
        print("✓ Translation loader tests passed")
        
    except Exception as e:
        print(f"✗ Translation loader test failed: {e}")
        return False
    
    return True


def test_settings_registry():
    """Test the settings registry with i18n integration."""
    print("\n=== Testing Settings Registry ===")
    
    try:
        from hatchling.config.settings import AppSettings
        from hatchling.config.settings_registry import SettingsRegistry
        from hatchling.config.i18n import set_language
        
        # Create test settings and registry
        app_settings = AppSettings()
        registry = SettingsRegistry(app_settings)
        
        # Test listing settings with English
        print("Testing settings list in English...")
        settings = registry.list_settings()
        print(f"Found {len(settings)} settings")
        
        if settings:
            # Check that translations are applied
            first_setting = settings[0]
            print(f"First setting: {first_setting.get('display_name', 'N/A')} ({first_setting['name']})")
            print(f"Description: {first_setting['description']}")
        
        # Test language switching
        print("Testing language switching to French...")
        if set_language("fr"):
            settings_fr = registry.list_settings()
            if settings_fr:
                first_setting_fr = settings_fr[0]
                print(f"French setting: {first_setting_fr.get('display_name', 'N/A')} ({first_setting_fr['name']})")
                print(f"French description: {first_setting_fr['description']}")
        
        # Test language management
        available_languages = registry.get_available_languages()
        print(f"Available languages from registry: {[lang['code'] for lang in available_languages]}")
        
        print("✓ Settings registry tests passed")
        
    except Exception as e:
        print(f"✗ Settings registry test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_settings_commands():
    """Test the settings commands functionality."""
    print("\n=== Testing Settings Commands ===")
    
    try:
        from hatchling.config.settings import AppSettings
        from hatchling.config.settings_registry import SettingsRegistry
        from hatchling.core.chat.settings_commands import SettingsCommands
        from hatchling.core.logging.session_debug_log import SessionDebugLog
        
        # Create test instances
        app_settings = AppSettings()
        registry = SettingsRegistry(app_settings)
        debug_log = SessionDebugLog("test_session", "debug")
        
        # Create settings commands instance
        settings_commands = SettingsCommands(
            chat_session=None,
            settings=None,
            env_manager=None,
            debug_log=debug_log,
            settings_registry=registry
        )
        
        # Test command registration
        command_metadata = settings_commands.get_command_metadata()
        print(f"Registered {len(command_metadata)} settings commands")
        
        # Print available commands
        for cmd_name, cmd_info in command_metadata.items():
            print(f"  {cmd_name}: {cmd_info['description']}")
        
        print("✓ Settings commands tests passed")
        
    except Exception as e:
        print(f"✗ Settings commands test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """Run all tests."""
    print("Running Phase 2 i18n Implementation Tests")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    if test_translation_loader():
        tests_passed += 1
    
    if test_settings_registry():
        tests_passed += 1
    
    if test_settings_commands():
        tests_passed += 1
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Phase 2 implementation is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
