import tkinter as tk
from src.main import YouTubeApp
from src.pages.main.main_page import MainPage


def _contiguous_indices(map_):
    vals = sorted([v for v in map_.values() if isinstance(v, int)])
    return vals == list(range(1, len(vals) + 1))


def main():
    root = tk.Tk()
    app = YouTubeApp(root)
    mp = app.frames.get(MainPage)
    app.show_frame(MainPage)
    mp.set_search_mode('Videos')
    mp.back_to_video_results()
    ok_vid = _contiguous_indices(mp.playlist_index_map)
    print(f"videos_mode_indices_contiguous={ok_vid}")
    mp.set_search_mode('Playlists')
    reset_ok = (mp.video_playlist_cache == {})
    cont_pl = _contiguous_indices(mp.playlist_index_map)
    print(f"playlists_mode_caches_cleared={reset_ok}")
    print(f"playlists_mode_indices_contiguous={cont_pl}")
    try:
        root.destroy()
    except Exception:
        pass


if __name__ == '__main__':
    main()
