import unittest
import time
import tkinter as tk

from src.pages.main.main_page import MainPage

class _Ctrl:
    def __init__(self, root):
        self.root = root
        self.default_folder = ""
        class _PH:
            def get_videos(self, *args, **kwargs):
                return {'videos': [], 'nextPageToken': None, 'prevPageToken': None}
        self.playlist_handler = _PH()


class PerfRenderTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_chunked_render_inserts_quickly(self):
        mp = MainPage(self.root, _Ctrl(self.root))
        mp.set_search_mode('Videos')
        N = 300
        mp.current_videos = [
            {'videoId': f'v{i}', 'title': f'T{i}', 'channelTitle': 'C', 'duration': '00:10', 'published': '2024-01-01T00:00:00Z', 'views': i}
            for i in range(N)
        ]
        t0 = time.time()
        mp._render_playlist_videos(N)
        dt = time.time() - t0
        self.assertLess(dt, 0.5)
        time.sleep(0.1)
        try:
            self.root.update()
        except Exception:
            pass
        cnt = len(mp.video.video_tree.get_children())
        self.assertEqual(cnt, N)


if __name__ == '__main__':
    unittest.main()
