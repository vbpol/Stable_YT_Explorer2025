import unittest
import time
import tkinter as tk

from src.pages.main.main_page import MainPage


class _PH:
    def __init__(self, mapping=None):
        self.mapping = dict(mapping or {})
    def playlist_contains_video(self, pid, vid):
        return self.mapping.get(vid) == pid


class _Ctrl:
    def __init__(self, root, mapping=None):
        self.root = root
        self.default_folder = ""
        self.playlist_handler = _PH(mapping or {})
        self.datastore = None


class PlaylistClickBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_click_playlist_assigns_correct_index(self):
        mp = MainPage(self.root, _Ctrl(self.root, {'v1': 'pl4', 'v2': 'pl4'}))
        mp.set_search_mode('Videos')
        mp.playlist.update_playlist({'playlistId': 'pl4', 'title': 'P4', 'channelTitle': 'C', 'video_count': 2})
        mp.playlist_index_map = {'pl4': 4}
        mp.current_videos = [
            {'videoId': 'v1', 'title': 'T1', 'channelTitle': 'C'},
            {'videoId': 'v2', 'title': 'T2', 'channelTitle': 'C'},
            {'videoId': 'v3', 'title': 'T3', 'channelTitle': 'C'},
        ]
        mp.video.video_tree.delete(*mp.video.video_tree.get_children())
        for v in mp.current_videos:
            mp.video.video_tree.insert('', 'end', values=mp._video_row(v))
        mp._update_results_ids()
        mp.highlight_videos_for_playlist('pl4')
        try:
            self.root.update()
        except Exception:
            pass
        items = mp.video.video_tree.get_children()
        vals1 = mp.video.video_tree.item(items[0]).get('values', [])
        vals2 = mp.video.video_tree.item(items[1]).get('values', [])
        self.assertEqual(vals1[1], 4)
        self.assertEqual(vals2[1], 4)
        tags1 = mp.video.video_tree.item(items[0]).get('tags', ())
        tags2 = mp.video.video_tree.item(items[1]).get('tags', ())
        self.assertIn('search_hit', tags1)
        self.assertIn('search_hit', tags2)

    def test_highlight_latency_under_threshold(self):
        mp = MainPage(self.root, _Ctrl(self.root, {}))
        mp.set_search_mode('Videos')
        mp.playlist.update_playlist({'playlistId': 'pl4', 'title': 'P4', 'channelTitle': 'C', 'video_count': 500})
        mp.playlist_index_map = {'pl4': 4}
        N = 500
        mp.current_videos = [{'videoId': f'v{i}', 'title': f'T{i}', 'channelTitle': 'C'} for i in range(N)]
        mp.video.video_tree.delete(*mp.video.video_tree.get_children())
        for v in mp.current_videos:
            mp.video.video_tree.insert('', 'end', values=mp._video_row(v))
        mp.video_results_ids = {f'v{i}' for i in range(N)}
        mp.playlist_video_ids = {'pl4': {f'v{i}' for i in range(N)}}
        mp.media_index = None
        t0 = time.time()
        mp.highlight_videos_for_playlist('pl4')
        dt = time.time() - t0
        self.assertLess(dt, 0.2)
        time.sleep(0.2)
        try:
            self.root.update()
        except Exception:
            pass
        items = mp.video.video_tree.get_children()
        for i in range(N):
            tags = mp.video.video_tree.item(items[i]).get('tags', ())
            self.assertIn('search_hit', tags)


if __name__ == '__main__':
    unittest.main()
