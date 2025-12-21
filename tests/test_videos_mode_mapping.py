import unittest
import tkinter as tk

from src.pages.main.main_page import MainPage


class MockPlaylistHandler:
    def __init__(self, video_to_playlist, details_map=None):
        self.video_to_playlist = dict(video_to_playlist or {})
        self.details_map = dict(details_map or {})

    def playlist_contains_video(self, playlist_id, video_id):
        return self.video_to_playlist.get(video_id) == playlist_id

    def get_details(self, playlist_id):
        return int(self.details_map.get(playlist_id, 0))


class MockDatastore:
    def __init__(self):
        self.links = []

    def link_video_to_playlist(self, playlist_id, video_id, position=None):
        self.links.append((playlist_id, video_id))

    def load_last_videos_result(self):
        return {}

    def get_playlist_videos(self, playlist_id, limit, offset):
        return []


class MockController:
    def __init__(self, ph, ds, root):
        self.playlist_handler = ph
        self.datastore = ds
        self.default_folder = ""
        self.root = root
    def show_frame(self, *args, **kwargs):
        return None


class VideosModeMappingTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_mapping_assigns_indices_without_gaps(self):
        vmap = {
            'v1': 'plA',
            'v2': 'plB',
            'v3': 'plA',
        }
        dmap = {'plA': 10, 'plB': 5}
        ph = MockPlaylistHandler(vmap, dmap)
        ds = MockDatastore()
        ctrl = MockController(ph, ds, self.root)
        mp = MainPage(self.root, ctrl)
        mp.set_search_mode('Videos')

        mp.playlist.update_playlist({'playlistId': 'plA', 'title': 'A', 'channelTitle': 'C1', 'video_count': 10})
        mp.playlist.update_playlist({'playlistId': 'plB', 'title': 'B', 'channelTitle': 'C2', 'video_count': 5})

        videos = [
            {'videoId': 'v1', 'title': 'T1', 'channelTitle': 'C1'},
            {'videoId': 'v2', 'title': 'T2', 'channelTitle': 'C2'},
            {'videoId': 'v3', 'title': 'T3', 'channelTitle': 'C1'},
        ]

        from src.services.media_index import MediaIndex
        mp.media_index = MediaIndex()
        mp.media_index.add_playlists([{'playlistId': 'plA'}, {'playlistId': 'plB'}])
        mp.media_index.link_video_to_playlist('plA', 'v1')
        mp.media_index.link_video_to_playlist('plA', 'v3')
        mp.media_index.link_video_to_playlist('plB', 'v2')
        
        collected = mp.map_videos_to_playlists(videos)

        self.assertEqual(set([p['playlistId'] for p in collected]), {'plA', 'plB'})
        idxs = set(mp.playlist_index_map.values())
        self.assertEqual(idxs, set(range(1, len(idxs) + 1)))
        for v in videos:
            self.assertTrue(v.get('playlistId'))
            self.assertTrue(v.get('playlistIndex'))

    def test_no_gaps_in_videos_table_playlist_column(self):
        ph = MockPlaylistHandler({}, {})
        ds = MockDatastore()
        ctrl = MockController(ph, ds, self.root)
        mp = MainPage(self.root, ctrl)
        mp.set_search_mode('Videos')
        try:
            mp.playlist.playlist_tree.delete(*mp.playlist.playlist_tree.get_children())
        except Exception:
            pass
        mp.playlist.update_playlist({'playlistId': 'plA', 'title': 'A', 'channelTitle': 'C1', 'video_count': 10})
        mp.playlist.update_playlist({'playlistId': 'plB', 'title': 'B', 'channelTitle': 'C2', 'video_count': 5})
        mp.playlist_index_map = {'plA': 1, 'plB': 3}
        mp.current_videos = [
            {'videoId': 'v1', 'title': 'T1', 'channelTitle': 'C1', 'playlistId': 'plA'},
            {'videoId': 'v2', 'title': 'T2', 'channelTitle': 'C2', 'playlistId': 'plB'},
        ]
        if not hasattr(mp, '_video_row'):
            mp.set_search_mode('Videos')
        mp.video.video_tree.delete(*mp.video.video_tree.get_children())
        for v in mp.current_videos:
            mp.video.video_tree.insert('', 'end', values=mp._video_row(v))
        mp.normalize_playlist_indices()
        items = mp.video.video_tree.get_children()
        vals1 = mp.video.video_tree.item(items[0]).get('values', [])
        vals2 = mp.video.video_tree.item(items[1]).get('values', [])
        self.assertEqual(vals1[1], 1)
        self.assertEqual(vals2[1], 2)

    def test_normalize_numbers_updates_tree_no_column(self):
        ph = MockPlaylistHandler({}, {})
        ds = MockDatastore()
        ctrl = MockController(ph, ds, self.root)
        mp = MainPage(self.root, ctrl)
        mp.set_search_mode('Videos')
        try:
            mp.playlist.playlist_tree.delete(*mp.playlist.playlist_tree.get_children())
        except Exception:
            pass
        mp.playlist_index_map = {'plA': 1, 'plB': 2}
        mp.playlist.update_playlist({'playlistId': 'plA', 'title': 'A', 'channelTitle': 'C1', 'video_count': 10})
        mp.playlist.update_playlist({'playlistId': 'plB', 'title': 'B', 'channelTitle': 'C2', 'video_count': 5})

        # Before normalize, numbers should be present
        for iid in mp.playlist.playlist_tree.get_children():
            vals = mp.playlist.playlist_tree.item(iid).get('values', [])
            n = int(str(vals[0] or '0')) if vals else 0
            self.assertIn(n, {1, 2})
        # After normalize, they should remain consistent
        mp.playlist.normalize_numbers()
        for iid in mp.playlist.playlist_tree.get_children():
            vals = mp.playlist.playlist_tree.item(iid).get('values', [])
            n = int(str(vals[0] or '0')) if vals else 0
            self.assertIn(n, {1, 2})


    def test_pin_to_top_does_not_change_numbers(self):
        ph = MockPlaylistHandler({}, {})
        ds = MockDatastore()
        ctrl = MockController(ph, ds, self.root)
        mp = MainPage(self.root, ctrl)
        mp.set_search_mode('Videos')
        try:
            mp.playlist.playlist_tree.delete(*mp.playlist.playlist_tree.get_children())
        except Exception:
            pass
        mp.playlist_index_map = {'plA': 1, 'plB': 2}
        mp.playlist.update_playlist({'playlistId': 'plA', 'title': 'A', 'channelTitle': 'C1', 'video_count': 10})
        mp.playlist.update_playlist({'playlistId': 'plB', 'title': 'B', 'channelTitle': 'C2', 'video_count': 5})
        mp._bring_playlist_to_top('plB')
        for iid in mp.playlist.playlist_tree.get_children():
            vals = mp.playlist.playlist_tree.item(iid).get('values', [])
            n = int(str(vals[0] or '0')) if vals else 0
            self.assertIn(n, {1, 2})
        self.assertEqual(mp.playlist_index_map.get('plA'), 1)
        self.assertEqual(mp.playlist_index_map.get('plB'), 2)

    def test_sort_does_not_renumber(self):
        ph = MockPlaylistHandler({}, {})
        ds = MockDatastore()
        ctrl = MockController(ph, ds, self.root)
        mp = MainPage(self.root, ctrl)
        mp.set_search_mode('Videos')
        mp.playlist_index_map = {'plA': 1, 'plB': 2}
        mp.playlist.update_playlist({'playlistId': 'plB', 'title': 'B', 'channelTitle': 'C2', 'video_count': 5})
        mp.playlist.update_playlist({'playlistId': 'plA', 'title': 'A', 'channelTitle': 'C1', 'video_count': 10})
        mp.sort_playlists_by('Title')
        self.assertEqual(mp.playlist_index_map.get('plA'), 1)
        self.assertEqual(mp.playlist_index_map.get('plB'), 2)

if __name__ == '__main__':
    unittest.main()
