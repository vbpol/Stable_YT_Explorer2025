import unittest
from unittest.mock import MagicMock, patch, ANY
import tkinter as tk

# Mocking tk classes to avoid GUI requirements
class MockTreeview(MagicMock):
    pass

class MockMainPage:
    def __init__(self):
        self.video = MagicMock()
        self.video.video_tree = MockTreeview()
        # Setup default return values
        self.video.video_tree.get_children.return_value = []
        self.video.video_tree.item.return_value = {}
        
        self.playlist = MagicMock()
        self.playlist.playlist_tree = MockTreeview()
        self.playlist.playlist_tree.get_children.return_value = []
        self.playlist.playlist_tree.item.return_value = {}
        
        self.status_bar = MagicMock()
        self.controller = MagicMock()
        self.controller.playlist_handler = MagicMock()
        self.playlist_matcher = MagicMock()
        self.media_index = MagicMock()
        self.current_videos = []
        self.video_results_ids = set()
        self.playlist_index_map = {}
        self.playlist_video_ids = {}
        self.search_mode = 'videos'
        self.collected_playlists = []
        self._preview_only_hits = False
        self._preview_active = False
        self.video.page_size_var = MagicMock()
        self.video.page_size_var.get.return_value = 10
        self.video._panel = MagicMock() # For update_pages
        self.video.prev_page_btn = MagicMock()
        self.video.next_page_btn = MagicMock()
        self.video.page_indicator = MagicMock()
        self.video.total_label = MagicMock()
        
    def _video_row(self, v):
        return (v.get('title'),)
    
    def _set_pinned_playlist(self, pid): pass
    def _persist_playlist_caches_only(self): pass
    def _safe_ui(self, fn): fn()
    def after(self, ms, fn): fn()
    def print_playlist_videos_to_terminal(self, pid): pass
    def assign_playlist_index(self, pid): return 1
    def _get_cached_playlist_page(self, pid, token): return None
    def _cache_playlist_videos(self, pid, token, resp): pass
    def _render_playlist_videos(self, total): pass
    # Mock these as MagicMock to allow assertions if needed, or simple methods
    def _load_last_results_data(self): return {}
    def _restore_search_state(self, data): return [], []
    def _restore_ui_state(self, v, p, d): pass
    def _async_recollect_playlists(self): pass
    def _log(self, msg): pass

from src.pages.main.videos_mode_handler import VideosModeHandler

class TestVideosModeFullFlow(unittest.TestCase):
    def setUp(self):
        self.mp = MockMainPage()
        self.mp._load_last_results_data = MagicMock(return_value={})
        self.mp._restore_search_state = MagicMock(return_value=([], []))
        self.mp._restore_ui_state = MagicMock()
        
        self.handler = VideosModeHandler(self.mp)
        
        # Setup sample data
        self.mp.current_videos = [
            {'videoId': 'v1', 'title': 'Video 1'},
            {'videoId': 'v2', 'title': 'Video 2'},
            {'videoId': 'v3', 'title': 'Video 3'}
        ]
        self.mp.video_results_ids = {'v1', 'v2', 'v3'}
        
        # Mock tree items
        self.mp.video.video_tree.get_children.return_value = ['i1', 'i2', 'i3']
        
    def test_highlight_videos_for_playlist(self):
        # Scenario: Playlist 'p1' contains 'v1' and 'v3' (intersecting with current results)
        playlist_id = 'p1'
        
        # Mock intersection result
        self.mp.playlist_matcher.get_intersection.return_value = {'v1', 'v3'}
        
        # Mock playlist item values so update logic triggers
        # We need to mock get_playlist_values because the handler uses it, 
        # and since self.mp.playlist is a Mock, we must define its return value.
        self.mp.playlist.get_playlist_values.return_value = ['1', 'Title', 'Channel', '10', 'Status', 'X']
        
        # Call highlight
        self.handler.highlight_videos_for_playlist(playlist_id)
        
        # Verify intersection call
        self.mp.playlist_matcher.get_intersection.assert_called()
        
        # Verify rows updated
        # Item i1 (v1) should be hit
        # Item i2 (v2) should NOT be hit
        # Item i3 (v3) should be hit
        
        # We check calls to video_tree.item
        # i1 update
        self.mp.video.video_tree.item.assert_any_call('i1', values=ANY, tags=('search_hit',))
        # i2 update
        self.mp.video.video_tree.item.assert_any_call('i2', values=ANY, tags=())
        # i3 update
        self.mp.video.video_tree.item.assert_any_call('i3', values=ANY, tags=('search_hit',))
        
        # Verify playlist tree update (intersection count)
        # We assert that update_playlist_item was called on the playlist section
        self.mp.playlist.update_playlist_item.assert_called_with(playlist_id, ANY)
        
    def test_on_videos_mode_playlist_click(self):
        # Mock highlight call
        with patch.object(self.handler, 'highlight_videos_for_playlist') as mock_highlight:
            self.handler.on_videos_mode_playlist_click('p1')
            
            # Verify status bar
            self.mp.status_bar.configure.assert_any_call(text="Loading playlist context…")
            
            # Verify highlight called
            mock_highlight.assert_called_with('p1')
            
    def test_populate_videos_table_preview(self):
        # Scenario: Clicking "Preview" on a playlist
        playlist_id = 'p1'
        playlist_videos = [{'videoId': 'pv1', 'title': 'PV 1'}, {'videoId': 'v1', 'title': 'Video 1'}] # v1 is in search results
        
        # Mock API response
        self.mp.controller.playlist_handler.get_details.return_value = 2
        self.mp.controller.playlist_handler.get_videos.return_value = {
            'videos': playlist_videos,
            'nextPageToken': None,
            'prevPageToken': None
        }
        
        self.handler.populate_videos_table_preview(playlist_id)
        
        # Verify current_videos replaced
        self.assertEqual(self.mp.current_videos, playlist_videos)
        
        # Verify preview mode flags
        self.assertTrue(self.mp._preview_only_hits)
        self.assertTrue(self.mp._preview_active)
        
        # Verify status bar
        self.mp.status_bar.configure.assert_any_call(text=f"Preview: {playlist_id}")
        
    def test_back_to_video_results(self):
        # Scenario: Returning from preview to search results
        self.mp.search_mode = 'videos'
        
        # Mock restore
        self.mp._load_last_results_data.return_value = {'some': 'data'}
        self.mp._restore_search_state.return_value = ([{'videoId': 'v1'}], [])
        
        self.handler.back_to_video_results()
        
        # Verify restore calls
        self.mp._load_last_results_data.assert_called()
        self.mp._restore_search_state.assert_called_with({'some': 'data'})
        # _restore_ui_state is no longer used; logic is inline/delegated
        # self.mp._restore_ui_state.assert_called()
        
        # Verify that current_videos was updated to the restored value
        self.assertEqual(self.mp.current_videos, [{'videoId': 'v1'}])
        
        # Verify status bar updated
        self.mp.status_bar.configure.assert_any_call(text="Back to video results")

if __name__ == '__main__':
    unittest.main()
