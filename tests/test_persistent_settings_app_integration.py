#!/usr/bin/env python3
"""Test script to verify app.py integration with persistent settings."""

import asyncio
import sys
import tempfile
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hatchling.config.settings import AppSettings
from hatchling.config.settings_registry import SettingsRegistry

async def test_app_integration():
    """Test that persistent settings work in app context."""
    print("Testing persistent settings integration...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set custom settings directory for testing
        import os
        original_env = os.environ.get('HATCHLING_SETTINGS_DIR')
        os.environ['HATCHLING_SETTINGS_DIR'] = str(Path(temp_dir) / "settings")
        
        try:
            # Create settings and registry (like app.py does)
            settings = AppSettings()
            registry = SettingsRegistry(settings)
            
            print(f"Cache dir: {settings.paths.hatchling_cache_dir}")
            print(f"Settings dir: {settings.paths.hatchling_settings_dir}")
            
            # Load persistent settings (should not exist yet)
            load_success = registry.load_persistent_settings()
            print(f"Load persistent settings (no file): {load_success}")
            
            # Modify a setting
            original_model = registry.get_setting('llm', 'model')['current_value']
            print(f"Original model: {original_model}")
            
            registry.set_setting('llm', 'model', 'integration-test-model')
            modified_model = registry.get_setting('llm', 'model')['current_value']
            print(f"Modified model: {modified_model}")
            
            # Save persistent settings
            save_success = registry.save_persistent_settings()
            print(f"Save persistent settings: {save_success}")
            
            # Check that file was created
            settings_file = registry.get_persistent_settings_file_path()
            print(f"Settings file exists: {settings_file.exists()}")
            print(f"Settings file path: {settings_file}")
            
            if settings_file.exists():
                # Read and display content
                with open(settings_file, 'r') as f:
                    content = f.read()
                print(f"Settings file content:\n{content}")
            
            # Reset setting and reload to test persistence
            registry.set_setting('llm', 'model', original_model)
            print(f"Reset model to: {registry.get_setting('llm', 'model')['current_value']}")
            
            # Load persistent settings again
            load_success = registry.load_persistent_settings()
            print(f"Load persistent settings (with file): {load_success}")
            
            final_model = registry.get_setting('llm', 'model')['current_value']
            print(f"Final model after reload: {final_model}")
            
            # Verify it matches what we saved
            if final_model == 'integration-test-model':
                print("✅ Integration test PASSED - Settings persisted correctly!")
                return True
            else:
                print(f"❌ Integration test FAILED - Expected 'integration-test-model', got '{final_model}'")
                return False
            
        finally:
            # Restore environment
            if original_env:
                os.environ['HATCHLING_SETTINGS_DIR'] = original_env
            else:
                os.environ.pop('HATCHLING_SETTINGS_DIR', None)

if __name__ == "__main__":
    success = asyncio.run(test_app_integration())
    sys.exit(0 if success else 1)
