import unittest
import os
import shutil
import tempfile
from src.services.download_path_manager import DownloadPathManager

class TestDownloadPathManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_get_video_target_folder_playlist(self):
        # Mock ConfigManager to return test_dir
        # Since ConfigManager is static, we might need to patch it or just rely on default behavior logic
        # For this test, we test the subfolder logic relative to a base
        
        video_info = {
            'videoId': '123',
            'playlistId': 'PLabc',
            'playlist_title': 'My Playlist'
        }
        opts = {}
        
        # We can't easily mock ConfigManager without unittest.mock, assuming standard lib is avail
        from unittest.mock import patch
        with patch('src.services.download_path_manager.DownloadPathManager.get_default_download_folder', return_value=self.test_dir):
            path = DownloadPathManager.get_video_target_folder(video_info, opts)
            expected = os.path.join(self.test_dir, "Playlist - My Playlist")
            self.assertEqual(path, expected)

    def test_get_video_target_folder_fallback(self):
        video_info = {
            'videoId': '123',
            'channelTitle': 'Test Channel'
        }
        opts = {
            'fallback_videos': True,
            'use_channel_title_fallback': True,
            'query': 'Python'
        }
        
        from unittest.mock import patch
        with patch('src.services.download_path_manager.DownloadPathManager.get_default_download_folder', return_value=self.test_dir):
            path = DownloadPathManager.get_video_target_folder(video_info, opts)
            expected = os.path.join(self.test_dir, "Channel - Test Channel")
            self.assertEqual(path, expected)

    def test_sanitization(self):
        video_info = {
            'videoId': '123',
            'playlistId': 'PLabc',
            'playlist_title': 'My/Playlist:Cool?'
        }
        from unittest.mock import patch
        with patch('src.services.download_path_manager.DownloadPathManager.get_default_download_folder', return_value=self.test_dir):
            path = DownloadPathManager.get_video_target_folder(video_info, {})
            expected = os.path.join(self.test_dir, "Playlist - My_Playlist_Cool_")
            self.assertEqual(path, expected)

if __name__ == '__main__':
    unittest.main()
