import tkinter as tk
from src.pages.main.main_page import MainPage


class MockPlaylistHandler:
    def playlist_contains_video(self, playlist_id, video_id):
        return False
    def get_details(self, playlist_id):
        return 0


class MockDatastore:
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


def main():
    root = tk.Tk()
    ph = MockPlaylistHandler()
    ds = MockDatastore()
    ctrl = MockController(ph, ds, root)
    mp = MainPage(root, ctrl)
    mp.set_search_mode('Videos')
    mp.playlist.playlist_tree.delete(*mp.playlist.playlist_tree.get_children())
    mp.playlist.update_playlist({'playlistId': 'plA', 'title': 'A', 'channelTitle': 'C1', 'video_count': 10})
    mp.playlist.update_playlist({'playlistId': 'plB', 'title': 'B', 'channelTitle': 'C2', 'video_count': 5})
    mp.current_videos = [
        {'videoId': 'v1', 'title': 'T1', 'channelTitle': 'C1', 'playlistId': 'plA'},
        {'videoId': 'v2', 'title': 'T2', 'channelTitle': 'C2', 'playlistId': 'plB'},
    ]
    mp.video.video_tree.delete(*mp.video.video_tree.get_children())
    for v in mp.current_videos:
        mp.video.video_tree.insert('', 'end', values=mp._video_row(v))
    mp.normalize_playlist_indices()
    items = mp.video.video_tree.get_children()
    for it in items:
        print(mp.video.video_tree.item(it).get('values'))
    try:
        root.destroy()
    except Exception:
        pass


if __name__ == '__main__':
    main()
