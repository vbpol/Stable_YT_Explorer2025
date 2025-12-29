import sys
import os

# quick hack to path
sys.path.append(os.getcwd())

from src.config_manager import ConfigManager

def test_validation():
    print("Testing ConfigManager Validation Logic...")
    
    # manual test with dummy key
    invalid_key = "AIzaSy_DummyKey_Invalid"
    status = ConfigManager.validate_api_key(invalid_key)
    print(f"Key: {invalid_key} -> Status: {status}")
    assert status in ["INVALID", "ERROR"]

    # Test loading keys
    keys = ConfigManager.get_available_api_keys()
    print(f"Available keys: {len(keys)}")
    for k in keys:
        print(f" - {k[:10]}...")

    print("Verification script finished.")

if __name__ == "__main__":
    test_validation()
