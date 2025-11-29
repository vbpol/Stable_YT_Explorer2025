import unittest
import tkinter as tk

from src.pages.main.main_page import MainPage


class MockPlaylistHandler:
    def playlist_contains_video(self, playlist_id, video_id):
        return False
    def get_details(self, playlist_id):
        return 0


class MockDatastore:
    def __init__(self, data):
        self.data = data
    def load_last_videos_result(self):
        return dict(self.data)
    def get_playlist_videos(self, playlist_id, limit, offset):
        vids = []
        for v in self.data.get('videos', []):
            pi = v.get('playlistIndex')
            rev = {1: 'plA', 2: 'plB'}
            if rev.get(pi) == playlist_id:
                vids.append({'videoId': v.get('videoId')})
        return vids


class MockController:
    def __init__(self, ph, ds, root):
        self.playlist_handler = ph
        self.datastore = ds
        self.default_folder = ""
        self.root = root
    def show_frame(self, *args, **kwargs):
        return None


class BackToResultsTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_back_to_results_restores_indices_and_cache(self):
        data = {
            'query': 'q',
            'videos': [
                {'videoId': 'v1', 'title': 'T1', 'channelTitle': 'C1', 'playlistIndex': 1},
                {'videoId': 'v2', 'title': 'T2', 'channelTitle': 'C2', 'playlistIndex': 2},
            ],
            'playlists': [
                {'playlistId': 'plA', 'title': 'A', 'channelTitle': 'C1', 'video_count': 10},
                {'playlistId': 'plB', 'title': 'B', 'channelTitle': 'C2', 'video_count': 5},
            ]
        }
        ph = MockPlaylistHandler()
        ds = MockDatastore(data)
        ctrl = MockController(ph, ds, self.root)
        mp = MainPage(self.root, ctrl)
        mp.set_search_mode('Videos')
        mp.back_to_video_results()
        self.assertEqual(mp.playlist_index_map.get('plA'), 1)
        self.assertEqual(mp.playlist_index_map.get('plB'), 2)
        self.assertEqual(mp.video_playlist_cache.get('v1'), 'plA')
        self.assertEqual(mp.video_playlist_cache.get('v2'), 'plB')
        items = mp.video.video_tree.get_children()
        vals1 = mp.video.video_tree.item(items[0]).get('values', [])
        vals2 = mp.video.video_tree.item(items[1]).get('values', [])
        self.assertEqual(vals1[1], 1)
        self.assertEqual(vals2[1], 2)


if __name__ == '__main__':
    unittest.main()
