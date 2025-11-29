import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import webbrowser
import os
import csv
import sys
import subprocess
import threading  # Add this for download threading
from .menu_section import MenuSection
from src.config_manager import ConfigManager
from .search_section import SearchSection
from .playlist_section import PlaylistSection
from .video_section import VideoSection
from .status_bar import StatusBar
from .video_player import VideoPlayer
from .download_options_dialog import DownloadOptionsDialog
from .download_manager import DownloadManager
from src.logger import get_logger

class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_videos = []
        self.current_playlist_info = {}
        self.current_page_token = None
        self.search_mode = 'playlists'
        self.last_videos_search = {}
        self.video_playlist_cache = {}
        self.playlist_index_map = {}
        self.video_matched_playlists = {}
        self.video_local_index_map = {}
        self._membership_cache = {}
        self.log = get_logger('MainPage')
        self._initialize_components()

    def _initialize_components(self):
        """Initialize and pack GUI components."""
        self._create_sections()
        self._pack_sections()

    def assign_playlist_index(self, playlist_id):
        if playlist_id in self.playlist_index_map:
            return self.playlist_index_map[playlist_id]
        idx = len(self.playlist_index_map) + 1
        self.playlist_index_map[playlist_id] = idx
        return idx

    def _create_sections(self):
        """Create sections for the main page."""
        self.menu = MenuSection(self)
        self.search = SearchSection(self)
        self.playlist = PlaylistSection(self)
        self.video = VideoSection(self)
        self.status_bar = StatusBar(self)

    def _pack_sections(self):
        """Pack sections into the main page."""
        self.search.pack(fill="x", padx=10, pady=5)
        self.playlist.pack(fill="both", expand=True, padx=10, pady=5)
        self.video.pack(fill="both", expand=True, padx=10, pady=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _resolve_video_playlist(self, video):
        vid = (video or {}).get('videoId')
        if not vid:
            return None
        try:
            self.log.info(f'resolve_video_playlist start vid={vid}')
        except Exception:
            pass
        try:
            spmap = getattr(self, '_store_video_playlist_map', None)
        except Exception:
            spmap = None
        if spmap is None:
            spmap = {}
            try:
                setattr(self, '_store_video_playlist_map', spmap)
            except Exception:
                pass
        try:
            if getattr(self.controller, 'datastore', None):
                if not spmap:
                    pls = list(getattr(self, 'collected_playlists', []) or [])
                    if not pls:
                        try:
                            data_last = self.controller.datastore.load_last_videos_result() or {}
                            pls = list(data_last.get('playlists', []) or [])
                        except Exception:
                            pls = []
                    for pl in pls:
                        try:
                            pid = pl.get('playlistId')
                            vids = self.controller.datastore.get_playlist_videos(pid, 1000, 0) or []
                            for vv in vids:
                                vvid = vv.get('videoId')
                                if vvid and pid:
                                    spmap[vvid] = pid
                        except Exception:
                            pass
        except Exception:
            pass
        try:
            pid_store = spmap.get(vid)
        except Exception:
            pid_store = None
        if pid_store:
            try:
                self.video_playlist_cache[vid] = pid_store
                video['playlistId'] = pid_store
                pi = self.assign_playlist_index(pid_store)
                video['playlistIndex'] = pi
            except Exception:
                pass
            try:
                self.log.info(f'resolve hit store vid={vid} pid={pid_store} pi={video.get("playlistIndex")}')
            except Exception:
                pass
            return pid_store
        try:
            pid = self.video_playlist_cache.get(vid)
        except Exception:
            pid = None
        if pid:
            try:
                video['playlistId'] = pid
                pi = self.assign_playlist_index(pid)
                video['playlistIndex'] = pi
            except Exception:
                pass
            try:
                self.log.info(f'resolve hit cache vid={vid} pid={pid} pi={video.get("playlistIndex")}')
            except Exception:
                pass
            return pid
        found = None
        cands = set()
        try:
            for p in list(getattr(self, 'collected_playlists', []) or []):
                pid = p.get('playlistId')
                if pid:
                    cands.add(pid)
        except Exception:
            pass
        try:
            if getattr(self.controller, 'datastore', None) and not cands:
                try:
                    data_last = self.controller.datastore.load_last_videos_result() or {}
                    for p in data_last.get('playlists', []) or []:
                        pid = p.get('playlistId')
                        if pid:
                            cands.add(pid)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            items = self.playlist.playlist_tree.get_children()
            for it in items:
                try:
                    cands.add(it)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            self.log.info(f'resolve candidates vid={vid} count={len(cands)}')
        except Exception:
            pass
        for plid in list(cands):
            try:
                key = (plid, vid)
                if key in self._membership_cache:
                    has = self._membership_cache[key]
                else:
                    has = self.controller.playlist_handler.playlist_contains_video(plid, vid)
                    self._membership_cache[key] = has
            except Exception:
                has = False
            if not has:
                continue
            try:
                self.video_matched_playlists.setdefault(vid, set()).add(plid)
            except Exception:
                pass
            if found is None:
                found = plid
            try:
                if getattr(self.controller, 'datastore', None):
                    self.controller.datastore.link_video_to_playlist(plid, vid)
            except Exception:
                pass
            try:
                if not self.playlist_index_map.get(plid):
                    idx = len(self.playlist_index_map) + 1
                    self.playlist_index_map[plid] = idx
            except Exception:
                pass
            try:
                if plid and not any(p.get('playlistId') == plid for p in getattr(self, 'collected_playlists', [])):
                    try:
                        pd = self._get_playlist_info(plid)
                    except Exception:
                        pd = {'playlistId': plid, 'title': '', 'channelTitle': '', 'video_count': 'N/A'}
                    try:
                        self.collected_playlists = getattr(self, 'collected_playlists', [])
                    except Exception:
                        self.collected_playlists = []
                    self.collected_playlists.append(pd)
                    try:
                        self.after(0, lambda d=pd: self.playlist.update_playlist(d))
                    except Exception:
                        pass
            except Exception:
                pass
        if found:
            try:
                self.video_playlist_cache[vid] = found
                video['playlistId'] = found
                pi = self.playlist_index_map.get(found)
                if pi:
                    video['playlistIndex'] = pi
            except Exception:
                pass
            try:
                self.log.info(f'resolve found vid={vid} pid={found} pi={video.get("playlistIndex")}')
            except Exception:
                pass
        if not found:
            try:
                ch = (video.get('channelTitle') or '').strip()
                ttl = (video.get('title') or '').strip()
                q = ch or ttl
                pls = []
                if q:
                    try:
                        pls = self.controller.playlist_handler.search_playlists(q, max_results=5)
                    except Exception:
                        pls = []
                for pl in pls or []:
                    plid = pl.get('playlistId')
                    if not plid:
                        continue
                    try:
                        key = (plid, vid)
                        if key in self._membership_cache:
                            has = self._membership_cache[key]
                        else:
                            has = self.controller.playlist_handler.playlist_contains_video(plid, vid)
                            self._membership_cache[key] = has
                    except Exception:
                        has = False
                    if not has:
                        continue
                    found = plid
                    try:
                        self.video_matched_playlists.setdefault(vid, set()).add(plid)
                    except Exception:
                        pass
                    try:
                        if getattr(self.controller, 'datastore', None):
                            self.controller.datastore.link_video_to_playlist(plid, vid)
                    except Exception:
                        pass
                    try:
                        if not self.playlist_index_map.get(plid):
                            idx = len(self.playlist_index_map) + 1
                            self.playlist_index_map[plid] = idx
                    except Exception:
                        pass
                    try:
                        pd = self._get_playlist_info(plid)
                        self.collected_playlists = getattr(self, 'collected_playlists', [])
                        if not any(p.get('playlistId') == plid for p in self.collected_playlists):
                            self.collected_playlists.append(pd)
                            self.after(0, lambda d=pd: self.playlist.update_playlist(d))
                    except Exception:
                        pass
                    break
                if found:
                    try:
                        self.video_playlist_cache[vid] = found
                        video['playlistId'] = found
                        pi = self.playlist_index_map.get(found)
                        if pi:
                            video['playlistIndex'] = pi
                    except Exception:
                        pass
            except Exception:
                pass
        return found

    def map_videos_to_playlists(self, videos, progress_hook=None):
        try:
            self.log.info(f'Start map_videos_to_playlists videos={len(videos)}')
        except Exception:
            pass
        try:
            self.collected_playlists = []
        except Exception:
            self.collected_playlists = []
        total = len(videos) or 1
        processed = 0
        for v in videos:
            pid = self._resolve_video_playlist(v)
            try:
                items = self.video.video_tree.get_children()
                for i, vv in enumerate(videos):
                    if vv.get('videoId') == v.get('videoId') and i < len(items):
                        self.video.video_tree.item(items[i], values=self._video_row(vv))
                        break
            except Exception:
                pass
            processed += 1
            if progress_hook:
                try:
                    progress_hook(processed, total)
                except Exception:
                    pass
        try:
            n = len(self.collected_playlists or [])
        except Exception:
            n = 0
        try:
            self.log.info(f'Finish map_videos_to_playlists collected={n}')
        except Exception:
            pass
        return list(self.collected_playlists or [])

    def set_search_mode(self, mode_display):
        m = (mode_display or '').strip().lower()
        if m not in ('playlists', 'videos'):
            m = 'playlists'
        self.search_mode = m
        try:
            self.log.info(f'set_search_mode mode={m}')
        except Exception:
            pass
        try:
            if m == 'playlists':
                try:
                    self.log.info('reset caches for playlists mode')
                except Exception:
                    pass
                self.playlist_index_map = {}
                self.video_playlist_cache = {}
                self.pinned_playlist_id = None
                self.video_matched_playlists = {}
        except Exception:
            pass
        try:
            self.playlist.playlist_tree.delete(*self.playlist.playlist_tree.get_children())
        except Exception:
            pass
        try:
            self.video.video_tree.delete(*self.video.video_tree.get_children())
        except Exception:
            pass
        if m == 'videos':
            try:
                self.video.update_back_button_state(False)
            except Exception:
                pass
            try:
                data = {}
                if getattr(self.controller, 'datastore', None):
                    data = self.controller.datastore.load_last_videos_result() or {}
                try:
                    if not data.get('playlists'):
                        j = ConfigManager.load_json(ConfigManager.get_last_search_path('videos')) or {}
                        if j.get('playlists'):
                            data['playlists'] = j.get('playlists')
                            if not data.get('query'):
                                data['query'] = j.get('query')
                except Exception:
                    pass
                q = (data.get('query') or '').strip()
                try:
                    self.search.search_entry.delete(0, 'end')
                    if q:
                        self.search.search_entry.insert(0, q)
                except Exception:
                    pass
                try:
                    self.log.info(f'Videos mode restore query q="{q}"')
                except Exception:
                    pass
                try:
                    # Preserve playlist numbering in Videos mode
                    pass
                except Exception:
                    pass
                if not hasattr(self, '_video_row'):
                    def _fmt_date(s):
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat((s or '').replace('Z', '+00:00'))
                            return dt.strftime('%y-%m-%d-%H')
                        except Exception:
                            return (s or '')[:10]
                    def _video_row(v):
                        vid = v.get('videoId')
                        plid = self.video_playlist_cache.get(vid)
                        try:
                            idx = self.video_local_index_map.get(plid)
                            if not idx:
                                idx = self.playlist_index_map.get(plid, '') if plid else (v.get('playlistIndex') or '')
                        except Exception:
                            idx = self.playlist_index_map.get(plid, '') if plid else (v.get('playlistIndex') or '')
                        views = v.get('views', '0')
                        try:
                            views = f"{int(views):,}"
                        except Exception:
                            pass
                        return (
                            v.get('title',''),
                            idx,
                            v.get('channelTitle',''),
                            v.get('duration','N/A'),
                            _fmt_date(v.get('published','')),
                            views
                        )
                    self._video_row = _video_row
                try:
                    self.video.video_tree.delete(*self.video.video_tree.get_children())
                except Exception:
                    pass
                try:
                    self.playlist.playlist_tree.delete(*self.playlist.playlist_tree.get_children())
                except Exception:
                    pass
                self.current_videos = data.get('videos', [])
                for v in (self.current_videos or []):
                    try:
                        self.video.video_tree.insert('', 'end', values=self._video_row(v))
                    except Exception:
                        pass
                try:
                    self.recompute_video_local_indices()
                except Exception:
                    pass
                try:
                    self.seed_playlists_from_store(self.current_videos)
                except Exception:
                    pass
                try:
                    self.build_videos_mode_dataset(self.current_videos)
                except Exception:
                    pass
                try:
                    rev = {idx: pid for pid, idx in self.playlist_index_map.items()}
                    for v in (self.current_videos or []):
                        vid = v.get('videoId')
                        pi = v.get('playlistIndex')
                        if vid and pi:
                            pid = rev.get(pi)
                            if pid:
                                self.video_playlist_cache[vid] = pid
                except Exception:
                    pass
                try:
                    self.playlist.normalize_numbers()
                except Exception:
                    pass
                try:
                    if getattr(self.controller, 'datastore', None):
                        pmap = {}
                        # Build reverse map from persisted last videos result only for the current videos
                        vids_ids = set([v.get('videoId') for v in (self.current_videos or []) if v.get('videoId')])
                        data_last = self.controller.datastore.load_last_videos_result() or {}
                        for pl in data_last.get('playlists', []) or []:
                            pid = pl.get('playlistId')
                            try:
                                vids = self.controller.datastore.get_playlist_videos(pid, 1000, 0) or []
                            except Exception:
                                vids = []
                            for vv in vids:
                                vid = vv.get('videoId')
                                if vid and vid in vids_ids:
                                    pmap[vid] = pid
                        items = self.video.video_tree.get_children()
                        for i, v in enumerate(self.current_videos or []):
                            try:
                                vid = v.get('videoId')
                                pid = pmap.get(vid)
                                if pid:
                                    if not self.video_playlist_cache.get(vid):
                                        self.video_playlist_cache[vid] = pid
                                    pi = self.playlist_index_map.get(pid)
                                    if pi and not v.get('playlistIndex'):
                                        v['playlistIndex'] = pi
                                        if i < len(items):
                                            self.video.video_tree.item(items[i], values=self._video_row(v))
                            except Exception:
                                pass
                        try:
                            self._store_video_playlist_map = dict(pmap)
                        except Exception:
                            pass
                        try:
                            self.log.info(f'videos mode init store_map size={len(getattr(self, "_store_video_playlist_map", {}) or {})}')
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    self.validate_videos_mode_state()
                except Exception:
                    pass
            except Exception:
                pass
            try:
                self.normalize_playlist_indices()
            except Exception:
                pass
        else:
            try:
                data = {'playlists': [], 'query': ''}
                if getattr(self.controller, 'datastore', None):
                    data = self.controller.datastore.load_last_playlists_result() or {'playlists': [], 'query': ''}
                try:
                    if not data.get('playlists'):
                        j = ConfigManager.load_json(ConfigManager.get_last_search_path('playlists')) or {}
                        if j.get('playlists'):
                            data['playlists'] = j.get('playlists')
                            if not data.get('query'):
                                data['query'] = j.get('query')
                except Exception:
                    pass
                q = (data.get('query') or '').strip()
                try:
                    self.search.search_entry.delete(0, 'end')
                    if q:
                        self.search.search_entry.insert(0, q)
                except Exception:
                    pass
                try:
                    self.log.info(f'Playlists mode restore query q="{q}"')
                except Exception:
                    pass
                try:
                    self.playlist_index_map = {}
                except Exception:
                    pass
                for pl in data.get('playlists', []):
                    self.playlist.update_playlist(pl)
                self.video.update_back_button_state(False)
                try:
                    self.playlist.normalize_numbers()
                except Exception:
                    pass
            except Exception:
                pass

    # Core functionality methods
    def execute_search(self, query, mode_display):
        q = (query or '').strip()
        if not q:
            messagebox.showerror("Error", "Please enter a keyword.")
            return
        m = (mode_display or '').strip().lower()
        if m not in ('playlists', 'videos'):
            m = 'playlists'
        self.search_mode = m
        try:
            self.log.info(f'execute_search mode={m} q="{q}"')
        except Exception:
            pass
        try:
            if m == 'playlists':
                self.playlist_index_map = {}
                self.video_playlist_cache = {}
                self.pinned_playlist_id = None
                self.video_matched_playlists = {}
        except Exception:
            pass
        try:
            if m == 'playlists':
                self.playlist_index_map = {}
                self.video_playlist_cache = {}
                self.pinned_playlist_id = None
        except Exception:
            pass
        try:
            self.playlist.playlist_tree.delete(*self.playlist.playlist_tree.get_children())
            self.video.video_tree.delete(*self.video.video_tree.get_children())
        except Exception:
            pass
        if m == 'playlists':
            try:
                playlists = self.controller.playlist_handler.search_playlists(q)
                for pl in playlists:
                    try:
                        video_count = self.controller.playlist_handler.get_details(pl.get('playlistId'))
                        pl['video_count'] = video_count
                    except Exception:
                        pl['video_count'] = 'N/A'
                    self.playlist.update_playlist(pl)
            except Exception as e:
                try:
                    messagebox.showerror("Error", f"Failed to fetch playlists: {e}")
                except KeyboardInterrupt:
                    try:
                        self.status_bar.configure(text="Interrupted while showing error dialog")
                    except Exception:
                        pass
                except Exception:
                    pass
            try:
                self.video.update_back_button_state(False)
            except Exception:
                pass
            try:
                if getattr(self.controller, 'datastore', None):
                    self.controller.datastore.save_last_playlists_result(q, playlists)
                try:
                    ConfigManager.save_last_mode('playlists')
                except Exception:
                    pass
            except Exception:
                pass
            return
        try:
            resp = self.controller.playlist_handler.search_videos(q, max_results=int(self.video.page_size_var.get()))
            videos = resp.get('videos', [])
            self.current_videos = videos
            self.last_videos_search = {'query': q, 'videos': videos}
            try:
                self.video_search_ids = set([v.get('videoId') for v in videos if v.get('videoId')])
            except Exception:
                self.video_search_ids = set()
            def _fmt_date(s):
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat((s or '').replace('Z', '+00:00'))
                    return dt.strftime('%y-%m-%d-%H')
                except Exception:
                    return (s or '')[:10]
            def _video_row(v):
                vid = v.get('videoId')
                plid = self.video_playlist_cache.get(vid)
                try:
                    idx = self.video_local_index_map.get(plid)
                    if not idx:
                        idx = self.playlist_index_map.get(plid, '') if plid else (v.get('playlistIndex') or '')
                except Exception:
                    idx = self.playlist_index_map.get(plid, '') if plid else (v.get('playlistIndex') or '')
                views = v.get('views', '0')
                try:
                    views = f"{int(views):,}"
                except Exception:
                    pass
                return (
                    v.get('title',''),
                    idx,
                    v.get('channelTitle',''),
                    v.get('duration','N/A'),
                    _fmt_date(v.get('published','')),
                    views
                )
            self._video_row = _video_row
            self.video.video_tree.delete(*self.video.video_tree.get_children())
            for v in videos:
                try:
                    vid = v.get('videoId')
                    tags = ('search_hit',) if vid in getattr(self, 'video_search_ids', set()) else ()
                    self.video.video_tree.insert('', 'end', values=self._video_row(v), tags=tags)
                except Exception:
                    self.video.video_tree.insert('', 'end', values=self._video_row(v))
            try:
                self.recompute_video_local_indices()
            except Exception:
                pass
            try:
                self.seed_playlists_from_store(videos)
            except Exception:
                pass
            try:
                self.build_videos_mode_dataset(self.current_videos)
            except Exception:
                pass
            try:
                self.video.update_back_button_state(False)
            except Exception:
                pass
            try:
                self.log.info(f'videos loaded count={len(videos)}')
            except Exception:
                pass
            try:
                if getattr(self.controller, 'datastore', None):
                    self.controller.datastore.save_last_videos_result(q, videos, [], resp.get('nextPageToken'), resp.get('prevPageToken'), list(self.video_search_ids))
                try:
                    ConfigManager.save_last_mode('videos')
                except Exception:
                    pass
            except Exception:
                pass
            try:
                ConfigManager.save_json(ConfigManager.get_last_search_path('videos'), {
                    'videos': videos,
                    'playlists': [],
                    'nextPageToken': resp.get('nextPageToken'),
                    'prevPageToken': resp.get('prevPageToken'),
                    'videoIds': [v.get('videoId') for v in videos if v.get('videoId')],
                    'query': q
                })
            except Exception:
                pass
            def _collect():
                try:
                    def _hook(done, tot):
                        try:
                            pct = int((done * 100) / (tot or 1))
                            if hasattr(self, '_collect_progress_bar') and self._collect_progress_bar:
                                self.after(0, lambda p=pct: self._collect_progress_bar.configure(value=p))
                            if hasattr(self, '_collect_progress_label') and self._collect_progress_label:
                                msg = f"Collecting related playlists... {pct}% ({done}/{tot})"
                                self.after(0, lambda m=msg: self._collect_progress_label.configure(text=m))
                        except Exception:
                            pass
                    collected = self.map_videos_to_playlists(videos, progress_hook=_hook)
                    try:
                        if getattr(self.controller, 'datastore', None):
                            self.controller.datastore.save_last_videos_result(q, videos, collected, resp.get('nextPageToken'), resp.get('prevPageToken'), list(self.video_search_ids))
                    except Exception:
                        pass
                    ConfigManager.save_json(ConfigManager.get_last_search_path('videos'), {
                        'videos': videos,
                        'playlists': collected,
                        'nextPageToken': resp.get('nextPageToken'),
                        'prevPageToken': resp.get('prevPageToken'),
                        'videoIds': list(self.video_search_ids)
                    })
                    try:
                        self.after(0, lambda: self.build_videos_mode_dataset(self.current_videos))
                    except Exception:
                        pass
                    try:
                        self.after(0, lambda n=len(collected): self.status_bar.configure(text=f"Collected {n} playlists"))
                    except Exception:
                        pass
                    try:
                        self.after(0, lambda: self.update_status_summary(len(collected or []), len(videos or [])))
                    except Exception:
                        pass
                    try:
                        self.after(0, self.playlist.normalize_numbers)
                    except Exception:
                        pass
                    try:
                        self.after(0, self.normalize_playlist_indices)
                    except Exception:
                        pass
                    try:
                        sp = {}
                        try:
                            for v in videos:
                                vid = v.get('videoId')
                                pid = self.video_playlist_cache.get(vid)
                                if vid and pid:
                                    sp[vid] = pid
                        except Exception:
                            pass
                        if getattr(self.controller, 'datastore', None):
                            for pl in collected:
                                try:
                                    pid = pl.get('playlistId')
                                    vids = self.controller.datastore.get_playlist_videos(pid, 1000, 0) or []
                                    for vv in vids:
                                        vvid = vv.get('videoId')
                                        if vvid and pid:
                                            sp[vvid] = pid
                                except Exception:
                                    pass
                        self._store_video_playlist_map = sp
                    except Exception:
                        pass
                    try:
                        self.after(0, self.validate_videos_mode_state)
                    except Exception:
                        pass
                finally:
                    try:
                        win = getattr(self, '_collect_progress', None)
                        self._collect_progress = None
                        self._collect_progress_bar = None
                        self._collect_progress_label = None
                        if win:
                            try:
                                self.after(0, lambda w=win: w.grab_release())
                            except Exception:
                                pass
                            try:
                                self.after(0, lambda w=win: w.destroy())
                            except Exception:
                                pass
                    except Exception:
                        pass
            try:
                try:
                    self._collect_progress = tk.Toplevel(self)
                    self._collect_progress.title("Loading")
                    self._collect_progress.geometry("360x120")
                    self._collect_progress_bar = ttk.Progressbar(self._collect_progress, orient="horizontal", length=320, mode="determinate", maximum=100)
                    self._collect_progress_bar.pack(pady=(16,8))
                    try:
                        self._collect_progress_label = ttk.Label(self._collect_progress, text="Collecting related playlists... 0%")
                        self._collect_progress_label.pack()
                    except Exception:
                        self._collect_progress_label = None
                    try:
                        self._collect_progress.transient(self.winfo_toplevel())
                        self._collect_progress.grab_set()
                    except Exception:
                        pass
                except Exception:
                    self._collect_progress = None
                    self._collect_progress_bar = None
                    self._collect_progress_label = None
                import threading
                threading.Thread(target=_collect, daemon=True).start()
            except Exception:
                pass
            try:
                if getattr(self.controller, 'datastore', None):
                    self.controller.datastore.save_last_videos_result(q, videos, [], resp.get('nextPageToken'), resp.get('prevPageToken'), list(self.video_search_ids))
            except Exception:
                pass
            try:
                ConfigManager.save_json(ConfigManager.get_last_search_path('videos'), {
                    'videos': videos,
                    'playlists': [],
                    'nextPageToken': resp.get('nextPageToken'),
                    'prevPageToken': resp.get('prevPageToken'),
                    'videoIds': [v.get('videoId') for v in videos if v.get('videoId')],
                    'query': q
                })
            except Exception:
                pass
        except Exception as e:
            try:
                msg = str(e).lower()
                if ('ssl' in msg) or ('cipher' in msg) or ('wrong version' in msg):
                    try:
                        self.status_bar.configure(text="SSL error while fetching playlist videos; fallback not available")
                    except Exception:
                        pass
                    return
            except Exception:
                pass
            messagebox.showerror("Error", f"Failed to fetch videos: {e}")

    def back_to_video_results(self):
        if self.search_mode != 'videos':
            return
        data = {}
        try:
            if getattr(self.controller, 'datastore', None):
                data = self.controller.datastore.load_last_videos_result() or {}
        except Exception:
            data = self.last_videos_search or {}
        vids = data.get('videos', [])
        try:
            self.playlist_index_map = {}
        except Exception:
            pass
        try:
            self.video.video_tree.delete(*self.video.video_tree.get_children())
        except Exception:
            pass
        self.video.video_tree.delete(*self.video.video_tree.get_children())
        try:
            self.playlist.playlist_tree.delete(*self.playlist.playlist_tree.get_children())
        except Exception:
            pass
        try:
            self.collected_playlists = []
        except Exception:
            self.collected_playlists = []
        if not hasattr(self, '_video_row'):
            def _fmt_date(s):
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat((s or '').replace('Z', '+00:00'))
                    return dt.strftime('%y-%m-%d-%H')
                except Exception:
                    return (s or '')[:10]
            def _video_row(v):
                vid = v.get('videoId')
                plid = self.video_playlist_cache.get(vid)
                idx = self.playlist_index_map.get(plid, '') if plid else (v.get('playlistIndex') or '')
                views = v.get('views', '0')
                try:
                    views = f"{int(views):,}"
                except Exception:
                    pass
                return (
                    v.get('title',''),
                    idx,
                    v.get('channelTitle',''),
                    v.get('duration','N/A'),
                    _fmt_date(v.get('published','')),
                    views
                )
            self._video_row = _video_row
        for v in vids:
            try:
                self.video.video_tree.insert('', 'end', values=self._video_row(v))
            except Exception:
                pass
        try:
            self.recompute_video_local_indices()
        except Exception:
            pass
        try:
            self.build_videos_mode_dataset(vids)
        except Exception:
            pass
        try:
            rev = {idx: pid for pid, idx in self.playlist_index_map.items()}
            for v in vids:
                vid = v.get('videoId')
                pi = v.get('playlistIndex')
                if vid and pi:
                    pid = rev.get(pi)
                    if pid:
                        self.video_playlist_cache[vid] = pid
        except Exception:
            pass
        try:
            if getattr(self.controller, 'datastore', None):
                pmap = {}
                for pl in data.get('playlists', []):
                    pid = pl.get('playlistId')
                    try:
                        vidsl = self.controller.datastore.get_playlist_videos(pid, 1000, 0) or []
                    except Exception:
                        vidsl = []
                    for vv in vidsl:
                        vid = vv.get('videoId')
                        if vid:
                            pmap[vid] = pid
                items = self.video.video_tree.get_children()
                for i, v in enumerate(vids):
                    try:
                        vid = v.get('videoId')
                        pid = pmap.get(vid)
                        if pid:
                            if not self.video_playlist_cache.get(vid):
                                self.video_playlist_cache[vid] = pid
                            v['playlistId'] = pid
                            pi = self.playlist_index_map.get(pid)
                            if pi and not v.get('playlistIndex'):
                                v['playlistIndex'] = pi
                                if i < len(items):
                                    self.video.video_tree.item(items[i], values=self._video_row(v))
                    except Exception:
                        pass
                try:
                    self._store_video_playlist_map = dict(pmap)
                except Exception:
                    pass
                try:
                    self.recompute_video_local_indices()
                except Exception:
                    pass
                try:
                    self.build_videos_mode_dataset(vids)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            self.normalize_playlist_indices()
        except Exception:
            pass
        try:
            self.video.update_back_button_state(False)
        except Exception:
            pass
    def on_video_select(self, event=None):
        if self.search_mode != 'videos':
            return
        sel = self.video.video_tree.selection()
        if not sel:
            return
        idx = self.video.video_tree.index(sel[0])
        if idx < 0 or idx >= len(self.current_videos):
            return
        video = self.current_videos[idx]
        vid = video.get('videoId')
        if not vid:
            return
        try:
            self.log.info(f'on_video_select idx={idx} vid={vid}')
        except Exception:
            pass
        if vid in self.video_playlist_cache:
            plid = self.video_playlist_cache[vid]
            try:
                self.playlist.playlist_tree.selection_set(plid)
                self.playlist.playlist_tree.see(plid)
                self.playlist.playlist_tree.move(plid, '', 0)
            except Exception:
                pass
            return
        def _worker(video_id, row_index):
            found = None
            try:
                vobj = self.current_videos[row_index]
            except Exception:
                vobj = {'videoId': video_id}
            try:
                found = self._resolve_video_playlist(vobj)
            except Exception:
                found = None
            def _update():
                try:
                    if found:
                        try:
                            self.playlist.playlist_tree.selection_set(found)
                            self.playlist.playlist_tree.see(found)
                            self.playlist.playlist_tree.move(found, '', 0)
                        except Exception:
                            pass
                        try:
                            pi = self.assign_playlist_index(found)
                            self.current_videos[row_index]['playlistIndex'] = pi
                            self.current_videos[row_index]['playlistId'] = found
                        except Exception:
                            pass
                        try:
                            items = self.video.video_tree.get_children()
                            if 0 <= row_index < len(items):
                                self.video.video_tree.item(items[row_index], values=self._video_row(self.current_videos[row_index]))
                        except Exception:
                            pass
                        try:
                            self.highlight_videos_for_playlist(found)
                        except Exception:
                            pass
                        try:
                            self.log.info(f'on_video_select mapped vid={video_id} pid={found} pi={self.current_videos[row_index].get("playlistIndex")}')
                        except Exception:
                            pass
                        try:
                            self.validate_videos_mode_state()
                        except Exception:
                            pass
                except Exception:
                    pass
            try:
                self.after(0, _update)
            except Exception:
                pass
        try:
            import threading
            threading.Thread(target=_worker, args=(vid, idx), daemon=True).start()
        except Exception:
            pass
    def highlight_videos_for_playlist(self, playlist_id):
        if self.search_mode != 'videos':
            return
        try:
            pi = self.assign_playlist_index(playlist_id)
        except Exception:
            pi = None
        try:
            items = self.video.video_tree.get_children()
        except Exception:
            items = []
        to_check = []
        for i, item in enumerate(items):
            try:
                v = self.current_videos[i] if i < len(self.current_videos) else {}
                vid = v.get('videoId')
                matched = False
                try:
                    if self.video_playlist_cache.get(vid) == playlist_id:
                        matched = True
                    elif pi and (v.get('playlistIndex') == pi):
                        matched = True
                    elif playlist_id in (self.video_matched_playlists.get(vid) or set()):
                        matched = True
                except Exception:
                    matched = False
                if not matched and vid:
                    to_check.append((i, item, vid))
                try:
                    info = self.video.video_tree.item(item)
                    base_tags = tuple(info.get('tags', ()))
                    if matched:
                        try:
                            if pi and not v.get('playlistIndex'):
                                v['playlistIndex'] = pi
                            if vid and not self.video_playlist_cache.get(vid):
                                self.video_playlist_cache[vid] = playlist_id
                            if vid:
                                v['playlistId'] = playlist_id
                        except Exception:
                            pass
                        new_tags = tuple(set(base_tags) | {'pl_match'})
                    else:
                        new_tags = tuple(t for t in base_tags if t != 'pl_match')
                    self.video.video_tree.item(item, tags=new_tags, values=self._video_row(v))
                except Exception:
                    pass
            except Exception:
                pass
        def _worker(plid, items_to_check):
            try:
                for (idx, item_id, video_id) in items_to_check:
                    try:
                        has = self.controller.playlist_handler.playlist_contains_video(plid, video_id)
                    except Exception:
                        has = False
                    if has:
                        try:
                            self.video_matched_playlists.setdefault(video_id, set()).add(plid)
                        except Exception:
                            pass
                        try:
                            v = self.current_videos[idx]
                            try:
                                pi_local = self.assign_playlist_index(plid)
                                if pi_local and not v.get('playlistIndex'):
                                    v['playlistIndex'] = pi_local
                                if not self.video_playlist_cache.get(video_id):
                                    self.video_playlist_cache[video_id] = plid
                                v['playlistId'] = plid
                            except Exception:
                                pass
                            info = self.video.video_tree.item(item_id)
                            base_tags = tuple(info.get('tags', ()))
                            new_tags = tuple(set(base_tags) | {'pl_match'})
                            self.after(0, lambda it=item_id, vv=v, nt=new_tags: self.video.video_tree.item(it, tags=nt, values=self._video_row(vv)))
                            try:
                                self.after(0, lambda pid=plid: (self.playlist.playlist_tree.selection_set(pid), self.playlist.playlist_tree.see(pid), self.playlist.playlist_tree.move(pid, '', 0)))
                            except Exception:
                                pass
                        except Exception:
                            pass
            except Exception:
                pass
        try:
            import threading
            if to_check:
                threading.Thread(target=_worker, args=(playlist_id, to_check), daemon=True).start()
        except Exception:
            pass

    def clear_video_playlist_highlights(self):
        try:
            items = self.video.video_tree.get_children()
        except Exception:
            items = []
        for i, item in enumerate(items):
            try:
                v = self.current_videos[i] if i < len(self.current_videos) else {}
                info = self.video.video_tree.item(item)
                base = tuple(t for t in info.get('tags', ()) if t != 'pl_match')
                self.video.video_tree.item(item, tags=base, values=self._video_row(v))
            except Exception:
                pass
    def sort_videos_by(self, column_name):
        col_map = {
            "Title": (lambda v: str(v.get('title','')).lower()),
            "Playlist": (lambda v: int(v.get('playlistIndex') or 0)),
            "Channel": (lambda v: str(v.get('channelTitle','')).lower()),
            "Duration": (lambda v: str(v.get('duration',''))),
            "Published": (lambda v: v.get('published','') or ''),
            "Views": (lambda v: int(v.get('views') or 0)),
        }
        keyfunc = col_map.get(column_name)
        if not keyfunc:
            return
        if not hasattr(self, 'video_sort_state'):
            self.video_sort_state = {}
        asc = self.video_sort_state.get(column_name, False)
        try:
            self.current_videos.sort(key=keyfunc, reverse=not asc)
        except Exception:
            pass
        self.video_sort_state[column_name] = not asc
        try:
            self.video.video_tree.delete(*self.video.video_tree.get_children())
            for v in self.current_videos:
                self.video.video_tree.insert('', 'end', values=self._video_row(v))
        except Exception:
            pass

    def on_video_header_double_click(self, column_name, query):
        ql = (query or '').strip().lower()
        if not ql:
            return
        items = []
        for v in self.current_videos:
            val = ''
            if column_name == 'Title':
                val = str(v.get('title',''))
            elif column_name == 'Playlist':
                val = str(v.get('playlistIndex') or '')
            elif column_name == 'Channel':
                val = str(v.get('channelTitle',''))
            elif column_name == 'Duration':
                val = str(v.get('duration',''))
            elif column_name == 'Published':
                val = str(v.get('published',''))
            elif column_name == 'Views':
                val = str(v.get('views',''))
            if ql in val.lower():
                items.append(v)
        try:
            self.video.video_tree.delete(*self.video.video_tree.get_children())
            for v in items:
                self.video.video_tree.insert('', 'end', values=self._video_row(v))
        except Exception:
            pass

    def sort_playlists_by(self, column_name):
        idx_map = {"No": 0, "Title": 1, "Channel": 2, "Videos": 3, "Status": 4, "Actions": 5}
        idx = idx_map.get(column_name)
        if idx is None:
            return
        if not hasattr(self, 'playlist_sort_state'):
            self.playlist_sort_state = {}
        asc = self.playlist_sort_state.get(column_name, False)
        rows = []
        try:
            for item in self.playlist.playlist_tree.get_children(''):
                vals = self.playlist.playlist_tree.item(item).get('values', [])
                rows.append((item, vals))
        except Exception:
            return
        def _key(row):
            v = row[1][idx] if idx < len(row[1]) else ''
            if column_name in ('Videos','No'):
                try:
                    return int(v)
                except Exception:
                    return -1
            return str(v).lower()
        rows.sort(key=_key, reverse=not asc)
        for item, _ in rows:
            try:
                self.playlist.playlist_tree.detach(item)
                self.playlist.playlist_tree.reattach(item, '', 'end')
            except Exception:
                pass
        self.playlist_sort_state[column_name] = not asc

    def on_playlist_header_double_click(self, column_name, query):
        ql = (query or '').strip().lower()
        if not ql:
            return
        idx_map = {"No": 0, "Title": 1, "Channel": 2, "Videos": 3, "Status": 4, "Actions": 5}
        idx = idx_map.get(column_name)
        if idx is None:
            return
        try:
            for item in self.playlist.playlist_tree.get_children(''):
                vals = self.playlist.playlist_tree.item(item).get('values', [])
                s = str(vals[idx]) if idx < len(vals) else ''
                if ql and ql not in s.lower():
                    self.playlist.playlist_tree.detach(item)
                else:
                    self.playlist.playlist_tree.reattach(item, '', 'end')
        except Exception:
            pass
    def search_playlists(self):
        """Search for playlists based on the keyword."""
        query = self.search.search_entry.get()
        if not query:
            messagebox.showerror("Error", "Please enter a keyword.")
            return

        try:
            # Clear existing items
            self.playlist.playlist_tree.delete(
                *self.playlist.playlist_tree.get_children()
            )

            # Search for playlists
            playlists = self.controller.playlist_handler.search_playlists(query)
            
            # Update each playlist with video count and status
            for playlist in playlists:
                try:
                    video_count = self.controller.playlist_handler.get_details(
                        playlist["playlistId"]
                    )
                    playlist["video_count"] = video_count
                except Exception as e:
                    # If we can't get details, just use the playlist without video count
                    print(f"Note: Could not get details for playlist {playlist['title']}")
                    playlist["video_count"] = "N/A"
                
                self.playlist.update_playlist(playlist)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch playlists: {e}")

    def show_playlist_videos(self, event=None, page_token=None):
        """Show videos in the selected playlist with pagination."""
        try:
            self.log.info("Starting show_playlist_videos")
        except Exception:
            pass
        
        if event:
            selected_item = self.playlist.get_selected_playlist()
        else:
            selected_item = self.playlist.playlist_tree.selection()[0]

        try:
            self.log.info(f"Selected playlist ID: {selected_item}")
        except Exception:
            pass
        
        if not selected_item:
            print("No playlist selected")  # Debug print
            return

        playlist_id = selected_item
        playlist_values = self.playlist.playlist_tree.item(selected_item)["values"]
        try:
            self.log.info(f"Playlist values: {playlist_values}")
        except Exception:
            pass
        
        try:
            playlist_title = playlist_values[1]
        except Exception:
            playlist_title = playlist_values[0] if playlist_values else ''
        try:
            channel_title = playlist_values[2]
        except Exception:
            channel_title = ''
        try:
            total_videos = int(playlist_values[3])
        except Exception:
            try:
                total_videos = int(self.controller.playlist_handler.get_details(playlist_id))
            except Exception:
                total_videos = 0
        
        self.current_playlist_info = {
            "title": playlist_title,
            "channel": channel_title,
            "id": playlist_id
        }

        try:
            # Get selected page size
            max_results = int(self.video.page_size_var.get())
            try:
                self.log.info(f"Fetching {max_results} videos")
            except Exception:
                pass
            
            # Get videos for current page
            response = self.controller.playlist_handler.get_videos(
                playlist_id, 
                page_token,
                max_results=max_results
            )
            try:
                self.log.info(f"API Response keys: {list(response.keys())}")
            except Exception:
                pass
            
            self.current_videos = response["videos"]
            self.current_page_token = response.get("nextPageToken")
            self.prev_page_token = response.get("prevPageToken")

            if not self.current_videos:
                try:
                    if getattr(self.controller, 'datastore', None):
                        stored = self.controller.datastore.get_playlist_videos(playlist_id, max_results, 0) or []
                        self.current_videos = stored
                        self.current_page_token = None
                        self.prev_page_token = None
                        print(f"Fallback to stored videos: {len(stored)}")
                except Exception:
                    pass

            # Update video tree with full columns and playlist index
            self.video.video_tree.delete(*self.video.video_tree.get_children())
            try:
                self.log.info(f"Loading {len(self.current_videos)} videos into tree")
            except Exception:
                pass
            try:
                pi = self.assign_playlist_index(playlist_id)
            except Exception:
                pi = None
            for video in self.current_videos:
                try:
                    if pi is not None:
                        video['playlistIndex'] = pi
                    video['playlistId'] = playlist_id
                    self.video_playlist_cache[video.get('videoId')] = playlist_id
                    try:
                        vid = video.get('videoId')
                        tags = ('search_hit',) if vid in getattr(self, 'video_search_ids', set()) else ()
                    except Exception:
                        tags = ()
                    self.video.video_tree.insert('', 'end', values=self._video_row(video), tags=tags)
                except Exception:
                    try:
                        self.video.video_tree.insert('', 'end', values=(video.get('title',''), video.get('duration','N/A')))
                    except Exception:
                        pass

            # Update pagination info
            total_pages = (total_videos + max_results - 1) // max_results
            if not hasattr(self, 'current_page') or page_token is None:
                self.current_page = 1
            elif page_token == self.current_page_token:
                self.current_page = min(self.current_page + 1, total_pages)
            elif page_token == self.prev_page_token:
                self.current_page = max(1, self.current_page - 1)
            
            self.video.total_label["text"] = f"Total videos: {total_videos}"
            self.video.page_indicator["text"] = f"Page {self.current_page} of {total_pages}"
            
            # Update pagination buttons
            self.video.next_page_btn["state"] = "normal" if self.current_page_token else "disabled"
            self.video.prev_page_btn["state"] = "normal" if self.prev_page_token else "disabled"
            try:
                if self.search_mode == 'videos':
                    self.video.update_back_button_state(True)
            except Exception:
                pass
            try:
                self._mark_search_hits_in_playlist_view()
            except Exception:
                pass

        except Exception as e:
            try:
                self.log.error(f"Error fetching videos: {e}")
            except Exception:
                pass
            try:
                if getattr(self.controller, 'datastore', None):
                    max_results = int(self.video.page_size_var.get())
                    stored = self.controller.datastore.get_playlist_videos(playlist_id, max_results, 0) or []
                    self.current_videos = stored
                    self.current_page_token = None
                    self.prev_page_token = None
                    try:
                        self.log.info(f"Fallback to stored videos: {len(stored)}")
                    except Exception:
                        pass
                    self.video.video_tree.delete(*self.video.video_tree.get_children())
                    try:
                        pi = self.assign_playlist_index(playlist_id)
                    except Exception:
                        pi = None
                    for video in stored:
                        try:
                            if pi is not None:
                                video['playlistIndex'] = pi
                            try:
                                self.video_playlist_cache[video.get('videoId')] = playlist_id
                            except Exception:
                                pass
                            tags = ('search_hit',) if video.get('videoId') in getattr(self, 'video_search_ids', set()) else ()
                            self.video.video_tree.insert('', 'end', values=self._video_row(video), tags=tags)
                        except Exception:
                            pass
                    total_videos = len(stored)
                    total_pages = 1
                    self.video.total_label["text"] = f"Total videos: {total_videos}"
                    self.video.page_indicator["text"] = f"Page 1 of {total_pages}"
                    self.video.next_page_btn["state"] = "disabled"
                    self.video.prev_page_btn["state"] = "disabled"
                    try:
                        if self.search_mode == 'videos':
                            self.video.update_back_button_state(True)
                    except Exception:
                        pass
                    try:
                        self._mark_search_hits_in_playlist_view()
                    except Exception:
                        pass
                    try:
                        self.update_status_summary(len(self.playlist.playlist_tree.get_children()), len(self.current_videos or []))
                    except Exception:
                        pass
                    return
            except Exception:
                pass
            try:
                max_results = int(self.video.page_size_var.get())
                alt_q = (playlist_title or channel_title or '').strip()
                if alt_q:
                    try:
                        self.log.info(f"Search-based fallback q='{alt_q}' max={max_results}")
                    except Exception:
                        pass
                    try:
                        cand_resp = self.controller.playlist_handler.search_videos(alt_q, max_results=max_results)
                        cand = []
                        for v in cand_resp.get('videos', []):
                            try:
                                vid_local = v.get('videoId')
                                if vid_local and self.controller.playlist_handler.playlist_contains_video(playlist_id, vid_local):
                                    cand.append(v)
                            except Exception:
                                pass
                        if cand:
                            self.current_videos = cand
                            self.current_page_token = cand_resp.get('nextPageToken')
                            self.prev_page_token = cand_resp.get('prevPageToken')
                            self.video.video_tree.delete(*self.video.video_tree.get_children())
                            try:
                                pi = self.assign_playlist_index(playlist_id)
                            except Exception:
                                pi = None
                            for video in cand:
                                try:
                                    if pi is not None:
                                        video['playlistIndex'] = pi
                                    video['playlistId'] = playlist_id
                                    self.video_playlist_cache[video.get('videoId')] = playlist_id
                                    tags = ('search_hit',) if video.get('videoId') in getattr(self, 'video_search_ids', set()) else ()
                                    self.video.video_tree.insert('', 'end', values=self._video_row(video), tags=tags)
                                except Exception:
                                    pass
                            try:
                                self.update_status_summary(len(self.playlist.playlist_tree.get_children()), len(self.current_videos or []))
                            except Exception:
                                pass
                            return
                    except Exception:
                        pass
            except Exception:
                pass
            messagebox.showerror("Error", f"Failed to fetch videos: {e}")

    def _mark_search_hits_in_playlist_view(self):
        try:
            ids = getattr(self, 'video_search_ids', set())
        except Exception:
            ids = set()
        try:
            items = self.video.video_tree.get_children()
        except Exception:
            items = []
        for i, item in enumerate(items):
            try:
                v = self.current_videos[i] if i < len(self.current_videos) else {}
                vid = v.get('videoId')
                t = ('search_hit',) if vid in ids else ()
                self.video.video_tree.item(item, tags=t, values=self._video_row(v))
            except Exception:
                pass

    def validate_videos_mode_state(self):
        if self.search_mode != 'videos':
            return
        try:
            total = len(self.current_videos or [])
        except Exception:
            total = 0
        try:
            mapped_cache = 0
            mapped_index = 0
            mismatches = 0
            rev = {idx: pid for pid, idx in (self.playlist_index_map or {}).items()}
            for v in list(self.current_videos or []):
                vid = v.get('videoId')
                if vid and self.video_playlist_cache.get(vid):
                    mapped_cache += 1
                pi = v.get('playlistIndex')
                if pi:
                    mapped_index += 1
                try:
                    pid_from_index = rev.get(pi)
                    pid_from_cache = self.video_playlist_cache.get(vid)
                    if pid_from_index and pid_from_cache and pid_from_index != pid_from_cache:
                        mismatches += 1
                except Exception:
                    pass
            self.log.info(f'validate videos: total={total} cache_mapped={mapped_cache} index_mapped={mapped_index} mismatches={mismatches}')
        except Exception:
            pass

    def normalize_playlist_indices(self):
        try:
            if getattr(self, 'video_local_index_map', None):
                new_map = dict(self.video_local_index_map)
            else:
                ids = list(self.playlist.playlist_tree.get_children())
                new_map = {}
                c = 1
                for pid in ids:
                    new_map[pid] = c
                    c += 1
        except Exception:
            new_map = {}
        try:
            self.playlist_index_map = new_map
        except Exception:
            pass
        try:
            self.playlist.normalize_numbers()
        except Exception:
            pass
        try:
            items = self.video.video_tree.get_children()
        except Exception:
            items = []
        for i, item in enumerate(items):
            try:
                v = self.current_videos[i] if i < len(self.current_videos) else {}
                pid = v.get('playlistId') or self.video_playlist_cache.get(v.get('videoId'))
                if pid:
                    pi = self.playlist_index_map.get(pid)
                    if pi:
                        v['playlistIndex'] = pi
                self.video.video_tree.item(item, values=self._video_row(v))
            except Exception:
                pass

    def recompute_video_local_indices(self):
        try:
            pids = []
            seen = set()
            for v in list(self.current_videos or []):
                pid = v.get('playlistId') or self.video_playlist_cache.get(v.get('videoId'))
                if pid and pid not in seen:
                    seen.add(pid)
                    pids.append(pid)
            lm = {}
            i = 1
            for pid in pids:
                lm[pid] = i
                i += 1
            self.video_local_index_map = lm
        except Exception:
            self.video_local_index_map = {}
        try:
            items = self.video.video_tree.get_children()
        except Exception:
            items = []
        for i, item in enumerate(items):
            try:
                v = self.current_videos[i] if i < len(self.current_videos) else {}
                vid = v.get('videoId')
                plid = v.get('playlistId') or self.video_playlist_cache.get(vid)
                if plid:
                    li = self.video_local_index_map.get(plid)
                    if li:
                        v['playlistIndex'] = li
                self.video.video_tree.item(item, values=self._video_row(v))
            except Exception:
                pass

    def _get_playlist_info(self, pid):
        info = {'playlistId': pid, 'title': '', 'channelTitle': '', 'video_count': 'N/A'}
        try:
            if self.playlist.playlist_tree.exists(pid):
                vals = self.playlist.playlist_tree.item(pid).get('values', [])
                try:
                    info['title'] = vals[1]
                except Exception:
                    pass
                try:
                    info['channelTitle'] = vals[2]
                except Exception:
                    pass
                try:
                    info['video_count'] = vals[3]
                except Exception:
                    pass
        except Exception:
            pass
        try:
            if not info['title']:
                for p in list(getattr(self, 'collected_playlists', []) or []):
                    if p.get('playlistId') == pid:
                        info['title'] = p.get('title', '')
                        info['channelTitle'] = p.get('channelTitle', '')
                        info['video_count'] = p.get('video_count', 'N/A')
                        break
        except Exception:
            pass
        try:
            if not info['title'] or not info['channelTitle'] or info['video_count'] in (None, '', 'N/A'):
                pi = self.controller.playlist_handler.get_playlist_info(pid)
                info['title'] = info['title'] or pi.get('title','')
                info['channelTitle'] = info['channelTitle'] or pi.get('channelTitle','')
                info['video_count'] = pi.get('video_count', info.get('video_count'))
        except Exception:
            pass
        return info

    def build_videos_mode_dataset(self, videos):
        vmap = {}
        pset = set()
        try:
            store_map = getattr(self, '_store_video_playlist_map', {}) or {}
        except Exception:
            store_map = {}
        for v in list(videos or []):
            try:
                vid = v.get('videoId')
                pid = v.get('playlistId') or self.video_playlist_cache.get(vid) or store_map.get(vid)
                if vid and pid:
                    vmap[vid] = pid
                    v['playlistId'] = pid
                    pset.add(pid)
            except Exception:
                pass
        if not pset:
            try:
                for v in list(videos or []):
                    try:
                        pid = self._resolve_video_playlist(v)
                        vid = v.get('videoId')
                        if vid and pid and pid not in pset:
                            pset.add(pid)
                            vmap[vid] = pid
                            v['playlistId'] = pid
                    except Exception:
                        pass
            except Exception:
                pass
        try:
            self.playlist.playlist_tree.delete(*self.playlist.playlist_tree.get_children())
        except Exception:
            pass
        plist = []
        for pid in list(pset):
            try:
                info = self._get_playlist_info(pid)
            except Exception:
                info = {'playlistId': pid, 'title': '', 'channelTitle': '', 'video_count': 'N/A'}
            plist.append(info)
        try:
            plist.sort(key=lambda d: str(d.get('title','')).lower())
        except Exception:
            pass
        nmap = {}
        i = 1
        for p in plist:
            nmap[p.get('playlistId')] = i
            i += 1
        try:
            self.video_local_index_map = dict(nmap)
        except Exception:
            pass
        try:
            items = self.video.video_tree.get_children()
        except Exception:
            items = []
        for i, item in enumerate(items):
            try:
                v = self.current_videos[i] if i < len(self.current_videos) else {}
                vid = v.get('videoId')
                pid = v.get('playlistId') or vmap.get(vid)
                if pid:
                    li = self.video_local_index_map.get(pid)
                    if li:
                        v['playlistIndex'] = li
                self.video.video_tree.item(item, values=self._video_row(v))
            except Exception:
                pass
        try:
            self.videos_mode_playlist_dataset = [{'No': self.video_local_index_map.get(p.get('playlistId')), **p} for p in plist]
        except Exception:
            self.videos_mode_playlist_dataset = plist
        for p in plist:
            try:
                self.playlist.update_playlist(p)
            except Exception:
                pass
        try:
            self.update_status_summary(len(pset), len(videos or []))
        except Exception:
            pass

    def update_status_summary(self, playlist_count, video_count):
        try:
            mapped_count = sum(1 for v in (self.current_videos or []) if (v.get('playlistId') or self.video_playlist_cache.get(v.get('videoId'))))
            msg = f"Playlists: {playlist_count} • Videos mapped: {mapped_count}/{video_count}"
            self.status_bar.configure(text=msg)
        except Exception:
            pass

    def seed_playlists_from_store(self, videos):
        try:
            if not getattr(self.controller, 'datastore', None):
                return
            vids_ids = set([v.get('videoId') for v in (videos or []) if v.get('videoId')])
            data_last = self.controller.datastore.load_last_videos_result() or {}
            pmap = {}
            for pl in data_last.get('playlists', []) or []:
                pid = pl.get('playlistId')
                if not pid:
                    continue
                try:
                    vids = self.controller.datastore.get_playlist_videos(pid, 1000, 0) or []
                except Exception:
                    vids = []
                for vv in vids:
                    vid = vv.get('videoId')
                    if vid and vid in vids_ids:
                        pmap[vid] = pid
            if not pmap:
                return
            try:
                for v in (videos or []):
                    vid = v.get('videoId')
                    pid = pmap.get(vid)
                    if not vid or not pid:
                        continue
                    if not self.video_playlist_cache.get(vid):
                        self.video_playlist_cache[vid] = pid
                    v['playlistId'] = pid
            except Exception:
                pass
            try:
                self.recompute_video_local_indices()
            except Exception:
                pass
            try:
                self.build_videos_mode_dataset(videos)
            except Exception:
                pass
        except Exception:
            pass

    def open_playlist(self, event):
        """Open the selected playlist in YouTube."""
        selected_item = self.playlist.playlist_tree.focus()
        if not selected_item:
            return

        playlist_id = selected_item
        playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
        webbrowser.open(playlist_url)

    def open_video(self, event):
        """Open the selected video in YouTube."""
        selected_item = self.video.video_tree.selection()
        if not selected_item:
            return

        selected_index = self.video.video_tree.index(selected_item[0])
        video = self.current_videos[selected_index]
        video_url = f"https://www.youtube.com/watch?v={video['videoId']}"
        webbrowser.open(video_url)

    def save_playlist(self):
        """Save the selected playlist details to a file."""
        if not self.current_playlist_info or not self.current_videos:
            messagebox.showerror("Error", "No playlist selected or no videos found.")
            return

        playlist_title = self.current_playlist_info["title"]
        channel_title = self.current_playlist_info["channel"]

        try:
            file_path = os.path.join(
                self.controller.default_folder,
                f"{playlist_title}.txt"
            )
            
            with open(file_path, 'w', encoding='utf-8') as txtfile:
                txtfile.write(f"Playlist: {playlist_title}\n")
                txtfile.write(f"Channel: {channel_title}\n")
                txtfile.write("\nVideos:\n")
                for i, video in enumerate(self.current_videos, 1):
                    txtfile.write(f"\n{i}. {video['title']}\n")
                    txtfile.write(f"   URL: https://www.youtube.com/watch?v={video['videoId']}\n")

            messagebox.showinfo("Success", f"Playlist saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save playlist: {str(e)}")

    def export_playlist_csv(self):
        """Export the current playlist to a CSV file."""
        if not self.current_playlist_info or not self.current_videos:
            messagebox.showerror("Error", "No playlist selected or no videos found.")
            return

        try:
            file_path = os.path.join(
                self.controller.default_folder,
                f"{self.current_playlist_info['title']}.csv"
            )
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Title', 'Video ID', 'URL', 'Duration'])
                for video in self.current_videos:
                    writer.writerow([
                        video['title'],
                        video['videoId'],
                        f"https://www.youtube.com/watch?v={video['videoId']}",
                        video['duration']
                    ])

            messagebox.showinfo("Success", f"Playlist exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export playlist: {str(e)}")

    def export_playlist_txt(self):
        """Export the current playlist to a text file."""
        if not self.current_playlist_info or not self.current_videos:
            messagebox.showerror("Error", "No playlist selected or no videos found.")
            return

        try:
            file_path = os.path.join(
                self.controller.default_folder,
                f"{self.current_playlist_info['title']}_export.txt"
            )
            
            with open(file_path, 'w', encoding='utf-8') as txtfile:
                txtfile.write(f"Playlist: {self.current_playlist_info['title']}\n")
                txtfile.write(f"Channel: {self.current_playlist_info['channel']}\n")
                txtfile.write(f"Total Videos: {len(self.current_videos)}\n\n")
                
                for i, video in enumerate(self.current_videos, 1):
                    txtfile.write(f"{i}. {video['title']} ({video['duration']})\n")
                    txtfile.write(f"   https://www.youtube.com/watch?v={video['videoId']}\n\n")

            messagebox.showinfo("Success", f"Playlist exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export playlist: {str(e)}")

    def change_download_folder(self):
        """Allow the user to change the default download folder."""
        new_folder = filedialog.askdirectory()
        if new_folder:
            self.controller.update_config(self.controller.api_key, new_folder)
            messagebox.showinfo("Success", f"Download folder updated to {new_folder}")

    def open_download_folder(self):
        """Open the download folder in file explorer."""
        if not self.current_playlist_info:
            return

        folder_path = os.path.join(
            self.controller.default_folder,
            f"Playlist - {self.current_playlist_info['title']}"
        )
        
        if os.path.exists(folder_path):
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder_path])
            else:
                subprocess.run(["xdg-open", folder_path])

    def view_downloaded_videos(self):
        """Open a window to view downloaded videos."""
        if not self.current_playlist_info:
            messagebox.showerror("Error", "No playlist selected.")
            return

        playlist_folder = os.path.join(
            self.controller.default_folder,
            f"Playlist - {self.current_playlist_info['title']}"
        )

        if not os.path.exists(playlist_folder):
            messagebox.showerror("Error", "No downloaded videos found for this playlist.")
            return

        # Create video player window
        player = VideoPlayer(self, playlist_folder)
        
        # Populate video list
        videos = [f for f in os.listdir(playlist_folder) if f.endswith('.mp4')]
        for video in videos:
            player.video_listbox.insert(tk.END, video)

    def download_playlist_videos(self):
        """Download videos from the current playlist."""
        print("\nStarting download process...")  # Debug print
        
        # First check if a playlist is selected
        selected_playlist = self.playlist.get_selected_playlist()
        if not selected_playlist:
            messagebox.showerror("Error", "Please select a playlist first.")
            return
        
        # Then check if videos are loaded
        if not self.current_videos:
            # Try to load videos if not already loaded
            self.show_playlist_videos()
            if not self.current_videos:
                messagebox.showerror("Error", "No videos found in the selected playlist.")
                return

        try:
            # Create download folder
            playlist_folder = os.path.join(
                self.controller.default_folder,
                f"Playlist - {self.current_playlist_info['title']}"
            )
            os.makedirs(playlist_folder, exist_ok=True)
            print(f"Created folder: {playlist_folder}")  # Debug print

            # Show download options dialog
            print("Creating download options dialog...")  # Debug print
            try:
                download_options = DownloadOptionsDialog(self)
                print(f"Dialog result: {download_options.result}")  # Debug print
            except Exception as dialog_error:
                print(f"Error creating dialog: {str(dialog_error)}")  # Debug print
                raise

            if not download_options.result:
                print("Download cancelled by user")  # Debug print
                return

            # Start download with progress tracking
            print("Creating download manager...")  # Debug print
            download_manager = DownloadManager(
                self, 
                self.current_videos,
                playlist_folder,
                download_options.result
            )
            print("Starting download manager...")  # Debug print
            download_manager.start()
            
        except Exception as e:
            print(f"Error in download process: {str(e)}")  # Debug print
            import traceback
            traceback.print_exc()  # Print full error traceback
            messagebox.showerror("Error", f"Download failed: {str(e)}")

    # ... (to be continued with more methods)
