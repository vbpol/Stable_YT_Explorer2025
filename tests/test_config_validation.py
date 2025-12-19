import unittest
import os
import json
from src.config_manager import ConfigManager, CONFIG_FILE

class TestConfigManagerValidation(unittest.TestCase):
    def setUp(self):
        # Backup existing config if any
        self.original_config = None
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                self.original_config = f.read()
        
    def tearDown(self):
        # Restore config
        if self.original_config:
            with open(CONFIG_FILE, 'w') as f:
                f.write(self.original_config)
        elif os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)

    def test_save_config_validation(self):
        # Test valid inputs
        ConfigManager.save_config("valid_key", "valid_folder")
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
        self.assertEqual(data.get("api_key"), "valid_key")
        self.assertEqual(data.get("default_folder"), "valid_folder")

        # Test invalid api_key
        with self.assertRaises(ValueError):
            ConfigManager.save_config("", "folder")
        with self.assertRaises(ValueError):
            ConfigManager.save_config(None, "folder")
        with self.assertRaises(ValueError):
            ConfigManager.save_config(123, "folder")

        # Test invalid default_folder
        with self.assertRaises(ValueError):
            ConfigManager.save_config("key", None)
        with self.assertRaises(ValueError):
            ConfigManager.save_config("key", 123)

if __name__ == '__main__':
    unittest.main()
