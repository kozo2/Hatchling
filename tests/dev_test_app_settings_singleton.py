#!/usr/bin/env python3
"""Test script to verify the AppSettings singleton implementation."""

import sys
import threading
import time
from pathlib import Path

# Add the hatchling module to the path
sys.path.insert(0, str(Path(__file__).parent / "hatchling"))

from hatchling.config.settings import AppSettings

def test_singleton_basic():
    """Test basic singleton functionality."""
    print("Testing basic singleton functionality...")
    
    # Test that multiple instantiations return the same object
    settings1 = AppSettings()
    settings2 = AppSettings()
    settings3 = AppSettings.get_instance()
    
    print(f"settings1 id: {id(settings1)}")
    print(f"settings2 id: {id(settings2)}")
    print(f"settings3 id: {id(settings3)}")
    
    assert settings1 is settings2, "settings1 and settings2 should be the same object"
    assert settings2 is settings3, "settings2 and settings3 should be the same object"
    assert settings1 is settings3, "settings1 and settings3 should be the same object"
    
    print("✓ Basic singleton test passed!")
    return True

def test_thread_safety():
    """Test thread safety of the singleton."""
    print("\nTesting thread safety...")
    
    results = []
    
    def create_instance():
        settings = AppSettings.get_instance()
        results.append(id(settings))
        time.sleep(0.01)  # Small delay to increase chance of race condition
    
    # Create multiple threads that create instances
    threads = []
    for i in range(10):
        thread = threading.Thread(target=create_instance)
        threads.append(thread)
    
    # Start all threads at roughly the same time
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # All results should be the same object ID
    unique_ids = set(results)
    print(f"Thread results: {results}")
    print(f"Unique IDs: {unique_ids}")
    
    assert len(unique_ids) == 1, f"Expected 1 unique ID, got {len(unique_ids)}: {unique_ids}"
    print("✓ Thread safety test passed!")
    return True

def test_state_persistence():
    """Test that state is maintained across singleton access."""
    print("\nTesting state persistence...")
    
    # Reset the singleton for a clean test
    AppSettings.reset_instance()
    
    # Create first instance and modify a setting
    settings1 = AppSettings.get_instance()
    original_model = settings1.llm.model
    settings1.llm.model = "test-model-singleton"
    
    # Get second instance and check the state
    settings2 = AppSettings.get_instance()
    
    print(f"Original model: {original_model}")
    print(f"Settings1 model: {settings1.llm.model}")
    print(f"Settings2 model: {settings2.llm.model}")
    
    assert settings2.llm.model == "test-model-singleton", "State should persist across instances"
    assert settings1 is settings2, "Should be the same object"
    
    print("✓ State persistence test passed!")
    return True

def test_reset_functionality():
    """Test the reset functionality."""
    print("\nTesting reset functionality...")
    
    # Create instance
    settings1 = AppSettings.get_instance()
    id1 = id(settings1)
    
    # Reset the singleton
    AppSettings.reset_instance()
    
    # Create new instance - should be different object
    settings2 = AppSettings.get_instance()
    id2 = id(settings2)
    
    print(f"Before reset ID: {id1}")
    print(f"After reset ID: {id2}")
    
    assert id1 != id2, "After reset, should get a new instance"
    
    print("✓ Reset functionality test passed!")
    return True

if __name__ == "__main__":
    print("Testing AppSettings singleton implementation...")
    print("=" * 50)
    
    try:
        test_singleton_basic()
        test_thread_safety()
        test_state_persistence() 
        test_reset_functionality()
        
        print("\n" + "=" * 50)
        print("✅ All singleton tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
