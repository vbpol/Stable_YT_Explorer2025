from typing import Callable, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# VideoPlaylistScanner centralizes the logic that scans channel playlists
# for each video result, maps videos to playlists, and reports progress.
# It isolates this behavior from UI code so later UI refactors do not
# impact the scanning/mapping functionality.

try:
    from src.playlist import Playlist
except ModuleNotFoundError:
    from playlist import Playlist


class VideoPlaylistScanner:
    def __init__(self, api_key: str, max_workers: int = 4, channel_playlist_limit: int = 50, prefetch_page_size: int = 10):
        self.api_key = api_key
        self.max_workers = max_workers
        self.channel_playlist_limit = channel_playlist_limit
        self.prefetch_page_size = prefetch_page_size
        self._query_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._channel_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._search_calls: int = 0
        self._max_search_calls: int = 40  # Increased default
        self._playlist_service = None

    def _get_service(self):
        if self._playlist_service is None:
            self._playlist_service = Playlist(self.api_key)
        return self._playlist_service

    def scan(
        self,
        videos: List[Dict[str, Any]],
        on_playlist_found: Callable[[Dict[str, Any]], int],
        on_prefetch_page: Callable[[str], None],
        on_progress: Callable[[int, int], None],
        on_video_index: Callable[[str, str, int], None],
    ) -> List[Dict[str, Any]]:
        total = len(videos or [])
        collected: List[Dict[str, Any]] = []
        seen: set[str] = set()
        ph = self._get_service()

        def _scan_one(v: Dict[str, Any]):
            vid = v.get('videoId')
            cid = v.get('channelId')
            title = (v.get('title') or '').strip()
            channel = (v.get('channelTitle') or '').strip()
            if not vid:
                return None

            # Optimization 1: Try channel-level playlists first if we have channelId
            if cid:
                try:
                    chan_pls = []
                    if cid in self._channel_cache:
                        chan_pls = self._channel_cache[cid]
                    else:
                        chan_pls = ph.get_channel_playlists(cid, max_results=self.channel_playlist_limit)
                        self._channel_cache[cid] = chan_pls
                    
                    for pl in chan_pls:
                        plid = pl.get('playlistId')
                        if plid and ph.playlist_contains_video(plid, vid):
                            return self._process_found_playlist(pl, vid, on_playlist_found, on_prefetch_page, on_video_index, seen, collected)
                except Exception:
                    pass

            # Optimization 2: Keyword search (original logic)
            queries = []
            if title: queries.append(title)
            if channel and title: queries.append(f"{channel} {title}")
            
            for q in queries:
                pls = []
                if q in self._query_cache:
                    pls = self._query_cache[q]
                elif self._search_calls < self._max_search_calls:
                    try:
                        pls = ph.search_playlists(q, max_results=5)
                        self._query_cache[q] = pls
                        self._search_calls += 1
                    except Exception:
                        pls = []
                
                for pl in pls:
                    plid = pl.get('playlistId')
                    if plid and ph.playlist_contains_video(plid, vid):
                        return self._process_found_playlist(pl, vid, on_playlist_found, on_prefetch_page, on_video_index, seen, collected)
            return True

        self._run_parallel(videos, _scan_one, on_progress)
        return collected

    def _process_found_playlist(self, pl, vid, on_playlist_found, on_prefetch_page, on_video_index, seen, collected):
        plid = pl.get('playlistId')
        idx = on_playlist_found(pl)
        if plid not in seen:
            seen.add(plid)
            collected.append(pl)
        try:
            on_prefetch_page(plid)
        except Exception:
            pass
        if isinstance(idx, (int, str)):
            on_video_index(vid, plid, idx)
        return True

    def _run_parallel(self, videos, scan_fn, on_progress):
        total = len(videos or [])
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
                futs = [ex.submit(scan_fn, v) for v in (videos or [])]
                for i, _ in enumerate(as_completed(futs), 1):
                    # Potential optimization: batch progress updates?
                    on_progress(i, total)
        except Exception:
            for i, v in enumerate(videos or [], 1):
                try:
                    scan_fn(v)
                except Exception:
                    pass
                on_progress(i, total)

        return collected
