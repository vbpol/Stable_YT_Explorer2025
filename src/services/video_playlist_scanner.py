from typing import Callable, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

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
        # Increased limit slightly as we have persistent caching now, 
        # but kept safe to prevent massive token usage on fresh runs.
        self._max_search_calls: int = 50 
        self._lock = threading.Lock()

    def scan(
        self,
        videos: List[Dict[str, Any]],
        on_playlist_found: Callable[[Dict[str, Any]], int],
        on_prefetch_page: Callable[[str], None],
        on_progress: Callable[[int, int], None],
        on_video_index: Callable[[str, str, int], None],
    ) -> List[Dict[str, Any]]:
        """Scan playlists for a list of videos and report findings.
        
        Optimized to batch by channelId to reduce API calls.
        """
        total = len(videos or [])
        collected: List[Dict[str, Any]] = []
        seen: set[str] = set()
        seen_lock = threading.Lock()
        
        # Group videos by channel
        by_channel: Dict[str, List[Dict[str, Any]]] = {}
        no_channel: List[Dict[str, Any]] = []
        
        for v in (videos or []):
            cid = v.get('channelId')
            if cid:
                by_channel.setdefault(cid, []).append(v)
            else:
                no_channel.append(v)
                
        processed_count = 0
        processed_lock = threading.Lock()
        
        def _update_progress(n=1):
            nonlocal processed_count
            with processed_lock:
                processed_count += n
                pc = processed_count
            try:
                on_progress(pc, total)
            except Exception:
                pass

        def _process_channel_batch(cid: str, chan_videos: List[Dict[str, Any]]):
            ph = Playlist(self.api_key)
            try:
                # 1. Fetch channel playlists (efficient batch)
                # This returns playlists OWNED by the channel, which covers most official organization
                playlists = ph.get_channel_playlists(cid, max_results=self.channel_playlist_limit)
                
                # 2. Check intersections locally
                # We need to know which videos are in these playlists.
                # Efficient approach: Fetch video list for each playlist and intersect IDs.
                
                chan_vid_ids = {v['videoId'] for v in chan_videos if v.get('videoId')}
                
                for pl in playlists:
                    plid = pl.get('playlistId')
                    if not plid: continue
                    
                    try:
                        # Fetch first page of playlist videos (usually 50)
                        # This is 1 API call per playlist found
                        resp = ph.get_videos(plid, max_results=self.prefetch_page_size)
                        pl_items = resp.get('videos', [])
                        pl_vid_ids = {pv['videoId'] for pv in pl_items if pv.get('videoId')}
                        
                        # Check intersection
                        matches = chan_vid_ids.intersection(pl_vid_ids)
                        
                        if matches:
                            # Found relevant playlist
                            idx = on_playlist_found(pl)
                            
                            with seen_lock:
                                if plid not in seen:
                                    seen.add(plid)
                                    collected.append(pl)
                            
                            try:
                                on_prefetch_page(plid)
                            except Exception:
                                pass
                                
                            # Update indices for matched videos
                            for vid in matches:
                                if isinstance(idx, int):
                                    on_video_index(vid, plid, idx)
                    except Exception:
                        pass
            except Exception:
                pass
            finally:
                _update_progress(len(chan_videos))

        def _scan_one_fallback(v: Dict[str, Any]):
            # Original logic for videos without channel ID
            ph = Playlist(self.api_key)
            vid = v.get('videoId')
            title = (v.get('title') or '').strip()
            channel = (v.get('channelTitle') or '').strip()
            if not vid:
                _update_progress(1)
                return
                
            queries = []
            if title: queries.append(title)
            if channel: queries.append(channel)
            
            if not queries:
                _update_progress(1)
                return

            first_index = None
            first_plid = None
            
            for q in queries:
                pls = []
                with self._lock:
                    if q in self._query_cache:
                        pls = self._query_cache[q]
                    elif self._search_calls < self._max_search_calls:
                        do_search = True
                        self._search_calls += 1
                    else:
                        do_search = False
                
                if 'do_search' in locals() and do_search:
                    try:
                        pls = ph.search_playlists(q, max_results=5)
                        with self._lock:
                            self._query_cache[q] = pls
                    except Exception:
                        pls = []
                elif q not in self._query_cache:
                    pls = []
                    
                for pl in pls:
                    plid = pl.get('playlistId')
                    if not plid: continue
                    try:
                        has = ph.playlist_contains_video(plid, vid)
                    except Exception:
                        has = False
                    if has:
                        # Attach intersection for fallback case too
                        pl['intersect_video_ids'] = [vid]
                        
                        idx = on_playlist_found(pl)
                        with seen_lock:
                            if plid not in seen:
                                seen.add(plid)
                                collected.append(pl)
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
                on_video_index(vid, first_plid, first_index)
            _update_progress(1)

        # Execute batches
        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            # Channel batches
            futs = [ex.submit(_process_channel_batch, cid, vids) for cid, vids in by_channel.items()]
            # Fallback for no-channel videos
            futs.extend([ex.submit(_scan_one_fallback, v) for v in no_channel])
            
            for _ in as_completed(futs):
                pass

        return collected
