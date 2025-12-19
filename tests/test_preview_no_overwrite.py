import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch
import json
import os

from src.pages.main.main_page import MainPage

class TestPreviewNoOverwrite(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.mock_controller = MagicMock()
        self.mock_controller.api_key = "dummy_key"
        self.mock_controller.default_folder = "dummy_folder"

    def tearDown(self):
        self.root.destroy()

    @patch('src.config_manager.ConfigManager.save_json')
    @patch('src.config_manager.ConfigManager.get_last_search_path')
    def test_persist_skips_during_preview(self, mock_get_path, mock_save_json):
        mock_get_path.return_value = "dummy_path.json"
        
        mp = MainPage(self.root, self.mock_controller)
        
        # Scenario 1: Not in preview mode
        mp._preview_active = False
        mp.current_videos = [{"id": "v1"}]
        mp._persist_last_videos_result()
        self.assertTrue(mock_save_json.called, "Should save when NOT in preview mode")
        
        mock_save_json.reset_mock()
        
        # Scenario 2: In preview mode
        mp._preview_active = True
        mp.current_videos = [{"id": "v_preview"}]
        mp._persist_last_videos_result()
        self.assertFalse(mock_save_json.called, "Should NOT save when in preview mode")

if __name__ == '__main__':
    unittest.main()
