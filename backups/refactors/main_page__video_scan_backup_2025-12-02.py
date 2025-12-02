# Backup of previous inline videos->playlists scanning logic in MainPage.execute_search
# This snapshot preserves the original _fetch_playlists implementation prior to refactor
# so future UI changes cannot inadvertently affect scanning behavior.

def _fetch_playlists_snapshot(self, query, videos):
    """Original threaded scanning implementation (snapshot)."""
    collected = []
    processed = 0
    total = len(videos)
    self._safe_ui(lambda t=total: self.video.show_scan(t))
    try:
        from src.playlist import Playlist as _Pl
    except ModuleNotFoundError:
        from playlist import Playlist as _Pl
    import threading as _t
    from concurrent.futures import ThreadPoolExecutor, as_completed
    lock = _t.Lock()
    unique = set()
    max_workers = 4
    def _register_playlist(pl):
        plid = pl.get('playlistId')
        if not plid:
            return None
        with lock:
            if plid in unique:
                return None
            unique.add(plid)
            collected.append(pl)
        try:
            pi = self.assign_playlist_index(plid)
        except Exception:
            pi = None
        self._safe_ui(lambda d=pl: self.playlist.update_playlist(d))
        def _prefetch(pid):
            try:
                ph2 = _Pl(self.controller.api_key)
                resp_pf = ph2.get_videos(pid, None, max_results=10)
                self._cache_playlist_videos(pid, None, resp_pf)
            except Exception:
                pass
        try:
            _t.Thread(target=_prefetch, args=(plid,), daemon=True).start()
        except Exception:
            pass
        return pi
    def _scan_one(v):
        nonlocal processed
        vid = v.get('videoId')
        cid = v.get('channelId')
        if not vid or not cid:
            with lock:
                processed += 1
                px = processed
            self._safe_ui(lambda x=px, t=total: self.video.update_scan_progress(x, t))
            return None
        try:
            ph = _Pl(self.controller.api_key)
            chpls = ph.get_channel_playlists(cid, max_results=50)
        except Exception:
            chpls = []
        first_index = None
        first_plid = None
        for pl in chpls:
            plid = pl.get('playlistId')
            if not plid:
                continue
            try:
                has = ph.playlist_contains_video(plid, vid)
            except Exception:
                has = False
            if not has:
                continue
            pi = _register_playlist(pl)
            if first_index is None and pi is not None:
                first_index = pi
                first_plid = plid
        if first_index and first_plid:
            try:
                v['playlistIndex'] = first_index
                self._safe_ui(lambda v_id=vid, p_id=first_plid: self._update_video_row_by_vid(v_id, p_id))
            except Exception:
                pass
        with lock:
            processed += 1
            px = processed
        self._safe_ui(lambda x=px, t=total: self.status_bar.configure(text=f"Collecting playlists from videos... {x}/{t}"))
        self._safe_ui(lambda x=px, t=total: self.video.update_scan_progress(x, t))
        return True
    try:
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futs = [ex.submit(_scan_one, v) for v in videos]
            for _ in as_completed(futs):
                pass
    except Exception:
        for v in videos:
            try:
                _scan_one(v)
            except Exception:
                pass
    try:
        from src.config_manager import ConfigManager
    except ModuleNotFoundError:
        from config_manager import ConfigManager
    try:
        ConfigManager.save_json(ConfigManager.get_last_search_path('videos'), {
            'query': query,
            'videos': videos,
            'playlists': collected,
            'nextPageToken': self.video_next_page_token,
            'prevPageToken': self.video_prev_page_token,
            'videoIds': list(self.video_search_ids)
        })
        self.collected_playlists = collected
        self._safe_ui(lambda n=len(collected): self.status_bar.configure(text=f"Collected {n} playlists"))
        self._safe_ui(lambda: self.video.finish_scan())
    except Exception:
        pass

