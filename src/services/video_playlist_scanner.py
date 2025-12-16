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
        self._search_calls: int = 0
        self._max_search_calls: int = 20

    def scan(
        self,
        videos: List[Dict[str, Any]],
        on_playlist_found: Callable[[Dict[str, Any]], int],
        on_prefetch_page: Callable[[str], None],
        on_progress: Callable[[int, int], None],
        on_video_index: Callable[[str, str, int], None],
    ) -> List[Dict[str, Any]]:
        """Scan playlists for a list of videos and report findings.

        Parameters:
        - videos: list of video dicts
        - on_playlist_found: callback when a playlist contains the video; returns assigned index
        - on_prefetch_page: callback to prefetch first page for a discovered playlist
        - on_progress: callback with (processed, total)
        - on_video_index: callback to update the video's playlist assignment (vid, pid, index)

        Returns: list of discovered unique playlists
        """
        total = len(videos or [])
        collected: List[Dict[str, Any]] = []
        seen: set[str] = set()

        def _scan_one(v: Dict[str, Any]):
            ph = Playlist(self.api_key)
            vid = v.get('videoId')
            title = (v.get('title') or '').strip()
            channel = (v.get('channelTitle') or '').strip()
            if not vid:
                return None
            queries = []
            try:
                if title:
                    queries.append(title)
                if channel and title:
                    queries.append(f"{channel} {title}")
                if channel and not title:
                    queries.append(channel)
            except Exception:
                pass
            if not queries:
                return None
            first_index = None
            first_plid = None
            for q in queries:
                pls = []
                try:
                    if q in self._query_cache:
                        pls = self._query_cache[q]
                    elif self._search_calls < self._max_search_calls:
                        pls = ph.search_playlists(q, max_results=5)
                        self._query_cache[q] = pls
                        self._search_calls += 1
                    else:
                        pls = []
                except Exception:
                    pls = []
                for pl in pls:
                    plid = pl.get('playlistId')
                    if not plid:
                        continue
                    try:
                        has = ph.playlist_contains_video(plid, vid)
                    except Exception:
                        has = False
                    if not has:
                        continue
                    idx = on_playlist_found(pl)
                    try:
                        pid = plid
                        if pid and pid not in seen:
                            seen.add(pid)
                            collected.append(pl)
                    except Exception:
                        pass
                    try:
                        on_prefetch_page(plid)
                    except Exception:
                        pass
                    if first_index is None and isinstance(idx, int):
                        first_index = idx
                        first_plid = plid
                    break
                if first_plid:
                    break
            if first_index and first_plid:
                try:
                    on_video_index(vid, first_plid, first_index)
                except Exception:
                    pass
            return True

        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
                futs = [ex.submit(_scan_one, v) for v in (videos or [])]
                processed = 0
                for _ in as_completed(futs):
                    processed += 1
                    try:
                        on_progress(processed, total)
                    except Exception:
                        pass
        except Exception:
            # Fallback sequential
            processed = 0
            for v in (videos or []):
                try:
                    _scan_one(v)
                except Exception:
                    pass
                processed += 1
                try:
                    on_progress(processed, total)
                except Exception:
                    pass

        return collected
