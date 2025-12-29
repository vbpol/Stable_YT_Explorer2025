import threading
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
        self._lock = threading.Lock()
        self._stopped = False
        self._executor = None

    def stop(self):
        """Signal the scanner to stop all background activities."""
        self._stopped = True
        if self._executor:
            try:
                # Attempt to shutdown but don't block
                self._executor.shutdown(wait=False, cancel_futures=True)
            except Exception:
                pass

    def _get_service(self):
        with self._lock:
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
        self._stopped = False
        total = len(videos or [])
        collected: List[Dict[str, Any]] = []
        seen: set[str] = set()
        ph = self._get_service()

        def _scan_one(v: Dict[str, Any]):
            if self._stopped:
                return None
            vid = v.get('videoId')
            cid = v.get('channelId')
            title = (v.get('title') or '').strip()
            channel = (v.get('channelTitle') or '').strip()
            if not vid:
                return None

            # Optimization 1: Try channel-level playlists first if we have channelId
            if cid:
                try:
                    if self._stopped: return None
                    chan_pls = []
                    with self._lock:
                        if cid in self._channel_cache:
                            chan_pls = self._channel_cache[cid]
                    
                    if not chan_pls:
                        chan_pls = ph.get_channel_playlists(cid, max_results=self.channel_playlist_limit)
                        with self._lock:
                            self._channel_cache[cid] = chan_pls
                    
                    for pl in chan_pls:
                        if self._stopped: return None
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
                if self._stopped: return None
                pls = []
                with self._lock:
                    if q in self._query_cache:
                        pls = self._query_cache[q]
                
                if not pls:
                    can_search = False
                    with self._lock:
                        if self._search_calls < self._max_search_calls:
                            can_search = True
                            self._search_calls += 1
                    
                    if can_search:
                        try:
                            if self._stopped: return None
                            pls = ph.search_playlists(q, max_results=5)
                            with self._lock:
                                self._query_cache[q] = pls
                        except Exception:
                            pls = []
                
                for pl in pls:
                    if self._stopped: return None
                    plid = pl.get('playlistId')
                    if plid and ph.playlist_contains_video(plid, vid):
                        return self._process_found_playlist(pl, vid, on_playlist_found, on_prefetch_page, on_video_index, seen, collected)
            return True

        self._run_parallel(videos, _scan_one, on_progress)
        return collected

    def _process_found_playlist(self, pl, vid, on_playlist_found, on_prefetch_page, on_video_index, seen, collected):
        if self._stopped:
            return False
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
        if self._stopped or not videos:
            return []
            
        try:
            # Create a localized executor to avoid state pollution
            with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
                with self._lock:
                    if self._stopped:
                        return []
                    self._executor = ex
                
                try:
                    futs = [ex.submit(scan_fn, v) for v in videos]
                    for i, _ in enumerate(as_completed(futs), 1):
                        if self._stopped:
                            # Shutdown immediately if possible
                            try:
                                ex.shutdown(wait=False, cancel_futures=True)
                            except Exception: pass
                            break
                        on_progress(i, total)
                finally:
                    with self._lock:
                        self._executor = None
        except Exception as e:
            logger.error(f"Parallel scan failed, falling back to sequential: {e}")
            for i, v in enumerate(videos, 1):
                if self._stopped:
                    break
                try:
                    scan_fn(v)
                except Exception:
                    pass
                on_progress(i, total)

        return []
