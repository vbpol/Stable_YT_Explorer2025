import unittest
import tkinter as tk

from src.pages.main.main_page import MainPage


class _PH:
    def __init__(self, mapping):
        self.mapping = dict(mapping or {})
    def playlist_contains_video(self, pid, vid):
        return self.mapping.get(vid) == pid
    def get_videos(self, *args, **kwargs):
        return {'videos': [], 'nextPageToken': None, 'prevPageToken': None}

class _Ctrl:
    def __init__(self, root, mapping=None):
        self.root = root
        self.default_folder = ""
        self.playlist_handler = _PH(mapping or {})


class HighlightFallbackTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_fallback_marks_when_index_empty(self):
        mapping = {'v1': 'p1', 'v2': 'p1'}
        mp = MainPage(self.root, _Ctrl(self.root, mapping))
        mp.set_search_mode('Videos')
        mp.current_videos = [
            {'videoId': 'v1', 'title': 'T1', 'channelTitle': 'C'},
            {'videoId': 'v2', 'title': 'T2', 'channelTitle': 'C'},
        ]
        mp.video.video_tree.delete(*mp.video.video_tree.get_children())
        for v in mp.current_videos:
            mp.video.video_tree.insert('', 'end', values=mp._video_row(v))
        mp.highlight_videos_for_playlist('p1')
        items = mp.video.video_tree.get_children()
        for i, item in enumerate(items):
            tags = mp.video.video_tree.item(item).get('tags', ())
            self.assertIn('search_hit', tags)


if __name__ == '__main__':
    unittest.main()
