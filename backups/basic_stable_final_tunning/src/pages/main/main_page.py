import tkinter as tk
from tkinter import messagebox, filedialog
import webbrowser
import os
import csv
import sys
import subprocess
import threading  # Add this for download threading
import json
from src.config_manager import ConfigManager
from .menu_section import MenuSection
from .search_section import SearchSection
from .playlist_section import PlaylistSection
from .video_section import VideoSection
from .status_bar import StatusBar
from .video_player import VideoPlayer
from .download_options_dialog import DownloadOptionsDialog
from .download_manager import DownloadManager

class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_videos = []
        self.current_playlist_info = {}
        self.current_page_token = None
        self._initialize_components()

    def _initialize_components(self):
        """Initialize and pack GUI components."""
        self._create_sections()
        self._pack_sections()
        try:
            lm = (ConfigManager.load_last_mode() or '').strip().lower()
            if lm == 'videos':
                try:
                    self.search.mode_var.set('Videos')
                except Exception:
                    pass
                self.search_mode = 'videos'
                self._load_last_search('Videos')
            elif lm == 'playlists':
                try:
                    self.search.mode_var.set('Playlists')
                except Exception:
                    pass
                self.search_mode = 'playlists'
                self._load_last_search('Playlists')
            else:
                md = getattr(self.search, 'mode_var', None)
                self._load_last_search(md.get() if md is not None else 'Playlists')
        except Exception:
            pass

    def _create_sections(self):
        """Create sections for the main page."""
        self.menu = MenuSection(self)
        self.search = SearchSection(self)
        self.playlist = PlaylistSection(self)
        self.video = VideoSection(self)
        self.status_bar = StatusBar(self)
        self.search_mode = 'playlists'
        self.current_videos = []
        self.current_playlist_info = None
        self.prev_page_token = None
        self.current_page_token = None
        self.video_playlist_cache = {}
        self.collected_playlists = []
        self.video_search_query = ''
        self.video_next_page_token = None
        self.video_prev_page_token = None
        self.video_sort_state = {}
        self.playlist_sort_state = {}
        self.download_concurrent_fragments = 4
        self.post_processing_enabled = True
        self.pinned_playlist_id = None
        self._highlighting_video_id = None
        self.playlist_index_map = {}
        self._last_selected_video_idx = None
        self.playlist_videos_cache = {}
        self._last_open_playlist_id = None
        self._pf_queue = []
        self._pf_workers = 0
        self._pf_max_workers = 2
        self._pf_failed = set()
        self.playlist_videos_cache = {}
        self._last_open_playlist_id = None
        self._highlight_busy = False
        self._pending_highlight = None
        self._playlist_open_busy = False
        self._pending_open = None
        self.playlist_video_ids = {}
        def _log(msg):
            try:
                print(f"[MainPage] {msg}")
            except Exception:
                pass
            try:
                self.status_bar.configure(text=str(msg))
            except Exception:
                pass
        self._log = _log
        def _fmt_date(s):
            try:
                from datetime import datetime
                dt = datetime.fromisoformat((s or '').replace('Z', '+00:00'))
                return dt.strftime('%y-%m-%d-%H')
            except Exception:
                return (s or '')[:10]
        self._fmt_date = _fmt_date
        def _video_row(v):
            vid = v.get('videoId')
            plid = self.video_playlist_cache.get(vid)
            idx = ''
            if plid:
                idx = self.playlist_index_map.get(plid, '')
            elif v.get('playlistIndex'):
                idx = v.get('playlistIndex')
            title = v.get('title', '')
            try:
                pinned = getattr(self, 'pinned_playlist_id', None)
                if pinned:
                    pinned_idx = self.playlist_index_map.get(pinned)
                    belongs = (plid == pinned) or (pinned_idx is not None and v.get('playlistIndex') == pinned_idx)
                    prefix = ''
                    if belongs and not str(title).startswith('★ '):
                        prefix += '★ '
                    try:
                        ordv = int(v.get('videoOrder') or 0)
                        if ordv > 0:
                            prefix += f"{ordv}. "
                    except Exception:
                        pass
                    if prefix:
                        title = f"{prefix}{title}"
            except Exception:
                pass
            return (
                title,
                idx,
                v.get('channelTitle', ''),
                v.get('duration', 'N/A'),
                self._fmt_date(v.get('published', '')),
                (f"{int(v.get('views', '0')):,}" if str(v.get('views', '0')).isdigit() else v.get('views', '0'))
            )
        self._video_row = _video_row
        def _cache_playlist_videos(playlist_id, page_token, response):
            try:
                cache = self.playlist_videos_cache.setdefault(playlist_id, {'pages': {}, 'tokens': {}})
                key = page_token or '__first__'
                cache['pages'][key] = list(response.get('videos', []))
                cache['tokens'][key] = (response.get('prevPageToken'), response.get('nextPageToken'))
                try:
                    ids = {v.get('videoId') for v in response.get('videos', []) if v.get('videoId')}
                except Exception:
                    ids = set()
                try:
                    cur = self.playlist_video_ids.setdefault(playlist_id, set())
                    for i in ids:
                        cur.add(i)
                except Exception:
                    pass
            except Exception:
                pass
        self._cache_playlist_videos = _cache_playlist_videos
        def _get_cached_playlist_page(playlist_id, page_token):
            try:
                cache = self.playlist_videos_cache.get(playlist_id)
                if not cache:
                    return None
                key = page_token or '__first__'
                vids = cache.get('pages', {}).get(key)
                toks = cache.get('tokens', {}).get(key, (None, None))
                if vids is None:
                    return None
                return {'videos': vids, 'prevPageToken': toks[0], 'nextPageToken': toks[1]}
            except Exception:
                return None
        self._get_cached_playlist_page = _get_cached_playlist_page
        def _enqueue_prefetch(pid):
            try:
                if pid in self._pf_failed:
                    return
                self._pf_queue.append(pid)
                if self._pf_workers < self._pf_max_workers:
                    _start_prefetch_worker()
            except Exception:
                pass
        self._enqueue_prefetch = _enqueue_prefetch
        def _start_prefetch_worker():
            try:
                import threading as _t, time as _tm
                def _worker():
                    try:
                        self._pf_workers += 1
                        while self._pf_queue:
                            try:
                                pid = self._pf_queue.pop(0)
                            except Exception:
                                pid = None
                            if not pid:
                                continue
                            try:
                                resp_pf = self.controller.playlist_handler.get_videos(pid, None, max_results=10)
                                self._cache_playlist_videos(pid, None, resp_pf)
                                print(f"[Prefetch] Cached first page for playlist {pid}")
                            except Exception as e_pf:
                                print(f"[Prefetch] Failed for {pid}: {e_pf}")
                                try:
                                    self._pf_failed.add(pid)
                                except Exception:
                                    pass
                            try:
                                _tm.sleep(0.2)
                            except Exception:
                                pass
                    finally:
                        try:
                            self._pf_workers -= 1
                        except Exception:
                            pass
                _t.Thread(target=_worker, daemon=True).start()
            except Exception:
                pass

    def _update_video_row_by_vid(self, vid, playlist_id):
        try:
            idx = None
            for i, v in enumerate(self.current_videos):
                if v.get('videoId') == vid:
                    idx = i
                    break
            if idx is None:
                return
            self.video_playlist_cache[vid] = playlist_id
            pi = self.assign_playlist_index(playlist_id)
            self.current_videos[idx]['playlistIndex'] = pi
            items = self.video.video_tree.get_children()
            if idx < len(items):
                self.video.video_tree.item(items[idx], values=self._video_row(self.current_videos[idx]))
        except Exception:
            pass

    def _bring_playlist_to_top(self, playlist_id):
        try:
            self.playlist.playlist_tree.move(playlist_id, '', 0)
            self.playlist.playlist_tree.see(playlist_id)
        except Exception:
            pass

    def _set_pinned_playlist(self, playlist_id):
        try:
            if self.pinned_playlist_id and self.playlist.playlist_tree.exists(self.pinned_playlist_id):
                vals = self.playlist.playlist_tree.item(self.pinned_playlist_id).get('values', [])
                if len(vals) >= 5 and isinstance(vals[4], str):
                    vals = (vals[0], vals[1], vals[2], vals[3], vals[4].replace(' • Pinned', ''), vals[5] if len(vals) > 5 else "❌")
                    self.playlist.playlist_tree.item(self.pinned_playlist_id, values=vals)
            self.pinned_playlist_id = playlist_id
            if self.playlist.playlist_tree.exists(playlist_id):
                vals = self.playlist.playlist_tree.item(playlist_id).get('values', [])
                if len(vals) >= 5 and isinstance(vals[4], str) and ' • Pinned' not in vals[4]:
                    vals = (vals[0], vals[1], vals[2], vals[3], f"{vals[4]} • Pinned", vals[5] if len(vals) > 5 else "❌")
                    self.playlist.playlist_tree.item(playlist_id, values=vals)
            self._bring_playlist_to_top(playlist_id)
        except Exception:
            pass

    def assign_playlist_index(self, playlist_id):
        # Indexing guard: assign deterministic, incremental indices per view/search.
        # Map is reset in clear_panels to reinit numbering for correctness.
        if playlist_id in self.playlist_index_map:
            return self.playlist_index_map[playlist_id]
        idx = len(self.playlist_index_map) + 1
        self.playlist_index_map[playlist_id] = idx
        return idx

    def _pack_sections(self):
        """Pack sections into the main page."""
        self.search.pack(fill="x", padx=10, pady=5)
        self.playlist.pack(fill="both", expand=True, padx=10, pady=5)
        self.video.pack(fill="both", expand=True, padx=10, pady=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def clear_panels(self):
        try:
            self.playlist.playlist_tree.delete(*self.playlist.playlist_tree.get_children())
        except Exception:
            pass
        try:
            self.video.video_tree.delete(*self.video.video_tree.get_children())
        except Exception:
            pass
        self.current_videos = []
        self.current_playlist_info = None
        self.prev_page_token = None
        self.current_page_token = None
        # Reset numbering for each new view/search as required
        try:
            self.playlist_index_map = {}
            self.pinned_playlist_id = None
        except Exception:
            pass

    def set_search_mode(self, mode_display):
        mode = (mode_display or '').strip().lower()
        if mode not in ('playlists', 'videos'):
            mode = 'playlists'
        if mode != self.search_mode:
            self.search_mode = mode
            try:
                ConfigManager.save_last_mode(mode)
            except Exception:
                pass
            self.clear_panels()
            try:
                self._load_last_search(mode_display)
            except Exception:
                pass

    def _load_last_search(self, mode_display):
        mode = (mode_display or '').strip().lower()
        if mode not in ('playlists', 'videos'):
            mode = 'playlists'
        try:
            if mode == 'playlists':
                path = ConfigManager.get_last_search_path('playlists')
                raw = ConfigManager.load_json(path)
                data_list = []
                q = ''
                try:
                    if isinstance(raw, dict):
                        data_list = raw.get('playlists', [])
                        q = raw.get('query', '')
                    else:
                        data_list = raw or []
                except Exception:
                    data_list = raw or []
                if not q:
                    # Fallback to persisted last query
                    try:
                        q = (ConfigManager.load_last_query().get('query') or '').strip()
                    except Exception:
                        q = ''
                try:
                    self.search.search_entry.delete(0, 'end')
                    if q:
                        self.search.search_entry.insert(0, q)
                except Exception:
                    pass
                for pl in data_list:
                    self.playlist.update_playlist(pl)
                try:
                    self.video.update_back_button_state(False)
                except Exception:
                    pass
            else:
                path = ConfigManager.get_last_search_path('videos')
                data = ConfigManager.load_json(path) or {}
                videos = data.get('videos', [])
                playlists = data.get('playlists', [])
                q = (data.get('query') or '').strip()
                if not q:
                    try:
                        q = (ConfigManager.load_last_query().get('query') or '').strip()
                    except Exception:
                        q = ''
                try:
                    self.video_prev_page_token = data.get('prevPageToken')
                    self.video_next_page_token = data.get('nextPageToken')
                except Exception:
                    pass
                try:
                    ids = data.get('videoIds') or []
                    self.video_search_ids = set([i for i in ids if i])
                except Exception:
                    self.video_search_ids = set()
                try:
                    self.search.search_entry.delete(0, 'end')
                    if q:
                        self.search.search_entry.insert(0, q)
                    self.video_search_query = q or self.video_search_query
                except Exception:
                    pass
                for v in videos:
                    self.video.video_tree.insert('', 'end', values=self._video_row(v))
                for pl in playlists:
                    self.playlist.update_playlist(pl)
                self.current_videos = videos
                self.collected_playlists = playlists
                try:
                    pages = (data.get('playlistPages') or {})
                    for pid, pinfo in pages.items():
                        try:
                            self.playlist_videos_cache.setdefault(pid, {'pages': {}, 'tokens': {}})
                            pages_map = self.playlist_videos_cache[pid]['pages']
                            tokens_map = self.playlist_videos_cache[pid]['tokens']
                            for key, entry in (pinfo.get('pages') or {}).items():
                                pages_map[key] = list(entry or [])
                            for key, toks in (pinfo.get('tokens') or {}).items():
                                tokens_map[key] = (toks[0] if len(toks)>0 else None, toks[1] if len(toks)>1 else None)
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    self.video.update_back_button_state(False)
                except Exception:
                    pass
                try:
                    self.video.prev_page_btn.configure(command=lambda: self.show_videos_search_page(self.video_prev_page_token))
                    self.video.next_page_btn.configure(command=lambda: self.show_videos_search_page(self.video_next_page_token))
                    self.video.prev_page_btn["state"] = "normal" if self.video_prev_page_token else "disabled"
                    self.video.next_page_btn["state"] = "normal" if self.video_next_page_token else "disabled"
                except Exception:
                    pass
        except Exception:
            pass

    def execute_search(self, query, mode_display):
        query = (query or '').strip()
        if not query:
            messagebox.showerror("Error", "Please enter a keyword.")
            return
        mode = (mode_display or '').strip().lower()
        if mode not in ('playlists', 'videos'):
            mode = 'playlists'
        self.search_mode = mode
        self.clear_panels()
        try:
            self.playlist_index_map = {}
            self.pinned_playlist_id = None
        except Exception:
            pass
        if mode == 'playlists':
            try:
                playlists = self.controller.playlist_handler.search_playlists(query)
                enriched = []
                for playlist in playlists:
                    try:
                        video_count = self.controller.playlist_handler.get_details(playlist["playlistId"])
                        playlist["video_count"] = video_count
                    except Exception:
                        playlist["video_count"] = "N/A"
                    self.playlist.update_playlist(playlist)
                    enriched.append(playlist)
                # Save query alongside results and persist last query
                ConfigManager.save_json(ConfigManager.get_last_search_path('playlists'), {
                    'query': query,
                    'playlists': enriched
                })
                try:
                    ConfigManager.save_last_query(query, 'playlists')
                except Exception:
                    pass
                try:
                    ConfigManager.save_last_mode('playlists')
                except Exception:
                    pass
                self.video.update_back_button_state(False)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to fetch playlists: {e}")
        else:
            self.video_search_query = query
            try:
                max_results = int(self.video.page_size_var.get())
            except Exception:
                max_results = 10
            try:
                resp = self.controller.playlist_handler.search_videos(query, max_results=max_results)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to fetch videos: {e}")
                return
            videos = resp.get('videos', [])
            self.current_videos = videos
            self.video_next_page_token = resp.get('nextPageToken')
            self.video_prev_page_token = resp.get('prevPageToken')
            try:
                self.video_search_ids = set([v.get('videoId') for v in videos if v.get('videoId')])
            except Exception:
                self.video_search_ids = set()
            self.video.video_tree.delete(*self.video.video_tree.get_children())
            for v in videos:
                try:
                    vid = v.get('videoId')
                    tags = ('search_hit',) if vid in getattr(self, 'video_search_ids', set()) else ()
                    self.video.video_tree.insert('', 'end', values=self._video_row(v), tags=tags)
                except Exception:
                    self.video.video_tree.insert('', 'end', values=self._video_row(v))

            def _fetch_playlists():
                    collected = []
                    processed = 0
                    total = len(videos)
                    cache_pl_by_channel = {}
                    for v in videos:
                        vid = v.get('videoId')
                        cid = v.get('channelId')
                        if not vid or not cid:
                            processed += 1
                            continue
                        try:
                            if cid in cache_pl_by_channel:
                                chpls = cache_pl_by_channel[cid]
                            else:
                                chpls = self.controller.playlist_handler.get_channel_playlists(cid, max_results=20)
                                cache_pl_by_channel[cid] = chpls
                        except Exception:
                            chpls = []
                        first_index = None
                        first_plid = None
                        try:
                            seen_ids = {p['playlistId'] for p in collected}
                        except Exception:
                            seen_ids = set()
                        for pl in chpls:
                            plid = pl.get('playlistId')
                            try:
                                has = self.controller.playlist_handler.playlist_contains_video(plid, vid)
                            except Exception:
                                has = False
                            if not has:
                                continue
                            if plid not in seen_ids:
                                collected.append(pl)
                                try:
                                    pi = self.assign_playlist_index(plid)
                                except Exception:
                                    pi = None
                                if first_index is None:
                                    first_index = pi
                                    first_plid = plid
                                try:
                                    self.after(0, lambda d=pl: self.playlist.update_playlist(d))
                                except Exception:
                                    pass
                                try:
                                    self._enqueue_prefetch(plid)
                                except Exception:
                                    pass
                            # Found membership; no need to check other playlists for this video
                            try:
                                if first_plid:
                                    break
                            except Exception:
                                pass
                        if first_index and first_plid:
                            try:
                                v['playlistIndex'] = first_index
                                self.after(0, lambda v_id=vid, p_id=first_plid: self._update_video_row_by_vid(v_id, p_id))
                            except Exception:
                                pass
                        processed += 1
                        try:
                            self.after(0, lambda x=processed, t=total: (self.status_bar.configure(text=f"Collecting playlists from videos... {x}/{t}"), self.status_bar.set_progress_ratio(x, t)))
                        except Exception:
                            pass
                    try:
                        # Save query and collected playlists
                        ConfigManager.save_json(ConfigManager.get_last_search_path('videos'), {
                            'query': query,
                            'videos': videos,
                            'playlists': collected,
                            'nextPageToken': self.video_next_page_token,
                            'prevPageToken': self.video_prev_page_token,
                            'videoIds': list(self.video_search_ids),
                            'playlistPages': {pid: {'pages': cache.get('pages', {}), 'tokens': cache.get('tokens', {})} for pid, cache in (self.playlist_videos_cache or {}).items()}
                        })
                        self.collected_playlists = collected
                        try:
                            self.after(0, lambda n=len(collected): (self.status_bar.reset_progress(), self.status_bar.configure(text=f"Collected {n} playlists")))
                        except Exception:
                            pass
                    except Exception:
                        pass
            try:
                threading.Thread(target=_fetch_playlists, daemon=True).start()
            except Exception:
                pass
            # Save initial page results and persist query
            ConfigManager.save_json(ConfigManager.get_last_search_path('videos'), {
                'query': query,
                'videos': videos,
                'playlists': [],
                'nextPageToken': self.video_next_page_token,
                'prevPageToken': self.video_prev_page_token,
                'videoIds': list(self.video_search_ids)
            })
            try:
                ConfigManager.save_last_query(query, 'videos')
            except Exception:
                pass
            try:
                ConfigManager.save_last_mode('videos')
            except Exception:
                pass
            self.video.update_back_button_state(False)
            try:
                self.video.prev_page_btn.configure(command=lambda: self.show_videos_search_page(self.video_prev_page_token))
                self.video.next_page_btn.configure(command=lambda: self.show_videos_search_page(self.video_next_page_token))
                self.video.prev_page_btn["state"] = "normal" if self.video_prev_page_token else "disabled"
                self.video.next_page_btn["state"] = "normal" if self.video_next_page_token else "disabled"
            except Exception:
                pass

    def back_to_video_results(self):
        if self.search_mode != 'videos':
            return
        path = ConfigManager.get_last_search_path('videos')
        data = ConfigManager.load_json(path) or {}
        self.clear_panels()
        videos = data.get('videos', [])
        playlists = data.get('playlists', [])
        try:
            q = (data.get('query') or '').strip()
            if not q:
                q = (ConfigManager.load_last_query().get('query') or '').strip()
            self.search.search_entry.delete(0, 'end')
            if q:
                self.search.search_entry.insert(0, q)
            self.video_search_query = q or self.video_search_query
        except Exception:
            pass
        try:
            ids = data.get('videoIds') or []
            self.video_search_ids = set([i for i in ids if i])
        except Exception:
            self.video_search_ids = set()
        for v in videos:
            try:
                vid = v.get('videoId')
                tags = ('search_hit',) if vid in getattr(self, 'video_search_ids', set()) else ()
                self.video.video_tree.insert('', 'end', values=self._video_row(v), tags=tags)
            except Exception:
                self.video.video_tree.insert('', 'end', values=self._video_row(v))
        for pl in playlists:
            self.playlist.update_playlist(pl)
        self.current_videos = videos
        self.collected_playlists = playlists
        self.video_prev_page_token = data.get('prevPageToken')
        self.video_next_page_token = data.get('nextPageToken')
        try:
            self.video_search_page_index = int(data.get('pageIndex') or 1)
            self.video.page_indicator["text"] = f"Results page {self.video_search_page_index}"
            self.video.total_label["text"] = f"Items: {len(videos)}"
        except Exception:
            pass
        try:
            self.video.prev_page_btn.configure(command=lambda: self.show_videos_search_page(self.video_prev_page_token))
            self.video.next_page_btn.configure(command=lambda: self.show_videos_search_page(self.video_next_page_token))
            self.video.prev_page_btn["state"] = "normal" if self.video_prev_page_token else "disabled"
            self.video.next_page_btn["state"] = "normal" if self.video_next_page_token else "disabled"
        except Exception:
            pass
        self.video.update_back_button_state(True)
        try:
            self.status_bar.configure(text="Back to video results")
        except Exception:
            pass
        try:
            if not self.collected_playlists and self.current_videos:
                self._log("Re-triggering playlist collection for restored results")
                import threading
                def _collect_again():
                    try:
                        vids = list(self.current_videos)
                        collected = []
                        processed = 0
                        total = len(vids)
                        cache_pl_by_channel = {}
                        for v in vids:
                            vid = v.get('videoId')
                            cid = v.get('channelId')
                            if not vid or not cid:
                                processed += 1
                                continue
                            try:
                                if cid in cache_pl_by_channel:
                                    chpls = cache_pl_by_channel[cid]
                                else:
                                    chpls = self.controller.playlist_handler.get_channel_playlists(cid, max_results=20)
                                    cache_pl_by_channel[cid] = chpls
                            except Exception:
                                chpls = []
                            first_index = None
                            first_plid = None
                            seen_ids = {p.get('playlistId') for p in collected if p.get('playlistId')}
                            for pl in chpls:
                                plid = pl.get('playlistId')
                                try:
                                    has = self.controller.playlist_handler.playlist_contains_video(plid, vid)
                                except Exception:
                                    has = False
                                if not has:
                                    continue
                                if plid not in seen_ids:
                                    collected.append(pl)
                                    try:
                                        pi = self.assign_playlist_index(plid)
                                    except Exception:
                                        pi = None
                                    if first_index is None:
                                        first_index = pi
                                        first_plid = plid
                                    try:
                                        self.after(0, lambda d=pl: self.playlist.update_playlist(d))
                                    except Exception:
                                        pass
                                if first_plid:
                                    break
                            if first_index and first_plid:
                                try:
                                    v['playlistIndex'] = first_index
                                    self.after(0, lambda v_id=vid, p_id=first_plid: self._update_video_row_by_vid(v_id, p_id))
                                except Exception:
                                    pass
                            processed += 1
                            try:
                                self.after(0, lambda x=processed, t=total: self.status_bar.set_progress_ratio(x, t))
                            except Exception:
                                pass
                        self.collected_playlists = collected
                        try:
                            self.after(0, lambda: self.status_bar.reset_progress())
                        except Exception:
                            pass
                    except Exception as e:
                        try:
                            import traceback; traceback.print_exc()
                        except Exception:
                            pass
                threading.Thread(target=_collect_again, daemon=True).start()
        except Exception:
            pass

    def on_video_select(self, event=None):
        if self.search_mode != 'videos':
            return
        sel = self.video.video_tree.selection()
        if not sel:
            return
        idx = self.video.video_tree.index(sel[0])
        self._last_selected_video_idx = idx
        if idx < 0 or idx >= len(self.current_videos):
            return
        video = self.current_videos[idx]
        vid = video.get('videoId')
        if not vid:
            return
        if vid in self.video_playlist_cache:
            plid = self.video_playlist_cache[vid]
            try:
                self._set_pinned_playlist(plid)
                self.playlist.playlist_tree.selection_set(plid)
                self.playlist.playlist_tree.see(plid)
                pi = self.assign_playlist_index(plid)
                self.current_videos[idx]['playlistIndex'] = pi
                try:
                    self.video.video_tree.item(sel[0], values=self._video_row(self.current_videos[idx]))
                except Exception:
                    pass
            except Exception:
                pass
            return
        if self._highlighting_video_id == vid:
            return
        self._highlighting_video_id = vid
        try:
            self.status_bar.configure(text="Finding playlist for selected video...")
        except Exception:
            pass
        def _worker(video_id, selected_index):
            found = None
            try:
                # Prefer already collected playlists for quick check
                for pl in list(self.collected_playlists or []):
                    plid = pl.get('playlistId')
                    try:
                        if self.controller.playlist_handler.playlist_contains_video(plid, video_id):
                            found = plid
                            self.video_playlist_cache[video_id] = found
                            break
                    except Exception:
                        pass
            except Exception:
                pass
            def _update():
                try:
                    if found:
                        self._set_pinned_playlist(found)
                        self.playlist.playlist_tree.selection_set(found)
                        self.playlist.playlist_tree.see(found)
                        pi = self.assign_playlist_index(found)
                        try:
                            if selected_index is not None and 0 <= selected_index < len(self.current_videos):
                                self.current_videos[selected_index]['playlistIndex'] = pi
                                # Update the currently selected video row
                                items = self.video.video_tree.get_children()
                                if selected_index < len(items):
                                    self.video.video_tree.item(items[selected_index], values=self._video_row(self.current_videos[selected_index]), tags=('video_hit',))
                        except Exception:
                            pass
                        self.status_bar.configure(text="Playlist highlighted")
                    else:
                        self.status_bar.configure(text="Playlist not found (checked first page only)")
                except Exception:
                    pass
                self._highlighting_video_id = None
            try:
                self.after(0, _update)
            except Exception:
                self._highlighting_video_id = None
        import threading as _t
        try:
            _t.Thread(target=_worker, args=(vid, self._last_selected_video_idx), daemon=True).start()
        except Exception:
            self._highlighting_video_id = None

    def highlight_videos_for_playlist(self, playlist_id):
        """Highlight already listed search videos that belong to the selected playlist.
        Preserves current search results and updates the 'Playlist' column and row tags."""
        try:
            if self._highlight_busy:
                self._pending_highlight = playlist_id
                try:
                    self.status_bar.configure(text="Scanning in progress; queued next playlist")
                except Exception:
                    pass
                return
        except Exception:
            pass
        try:
            pi = self.assign_playlist_index(playlist_id)
        except Exception:
            pi = None
        def _worker(plid):
            try:
                self._highlight_busy = True
            except Exception:
                pass
            matched = 0
            done = 0
            try:
                total = len(list(self.current_videos or []))
            except Exception:
                total = 0
            try:
                for i, v in enumerate(list(self.current_videos or [])):
                    vid = v.get('videoId')
                    if not vid:
                        done += 1
                        try:
                            self.after(0, lambda x=done, t=total: self.status_bar.set_progress_ratio(x, t))
                        except Exception:
                            pass
                        continue
                    try:
                        ids_set = self.playlist_video_ids.get(plid)
                    except Exception:
                        ids_set = None
                    if ids_set is not None:
                        has = (vid in ids_set)
                    else:
                        try:
                            has = self.controller.playlist_handler.playlist_contains_video(plid, vid)
                        except Exception:
                            has = False
                    if not has:
                        done += 1
                        try:
                            self.after(0, lambda x=done, t=total: self.status_bar.set_progress_ratio(x, t))
                        except Exception:
                            pass
                        continue
                    try:
                        self.video_playlist_cache[vid] = plid
                    except Exception:
                        pass
                    try:
                        if pi is not None:
                            v['playlistIndex'] = pi
                    except Exception:
                        pass
                    matched += 1
                    done += 1
                    def _update_row(idx=i):
                        try:
                            items = self.video.video_tree.get_children()
                            if idx < len(items):
                                row = self._video_row(self.current_videos[idx])
                                try:
                                    title = row[0]
                                    if not str(title).startswith('★ '):
                                        row = (f"★ {title}",) + row[1:]
                                except Exception:
                                    pass
                                tags = ('playlist_hit',)
                                self.video.video_tree.item(items[idx], values=row, tags=tags)
                        except Exception:
                            pass
                    try:
                        self.after(0, _update_row)
                    except Exception:
                        pass
                    try:
                        self.after(0, lambda x=done, t=total: self.status_bar.set_progress_ratio(x, t))
                    except Exception:
                        pass
            except Exception:
                pass
            def _done():
                try:
                    try:
                        self.status_bar.reset_progress()
                    except Exception:
                        pass
                    if matched:
                        self.status_bar.configure(text=f"Highlighted {matched} matched videos for selected playlist")
                    else:
                        self.status_bar.configure(text="No matching videos found for selected playlist")
                    try:
                        self._set_pinned_playlist(plid)
                    except Exception:
                        pass
                    try:
                        self._highlight_busy = False
                    except Exception:
                        pass
                    try:
                        nxt = self._pending_highlight
                        self._pending_highlight = None
                        if nxt:
                            self.highlight_videos_for_playlist(nxt)
                    except Exception:
                        pass
                except Exception:
                    pass
            try:
                self.after(0, _done)
            except Exception:
                pass
        try:
            import threading as _t
            _t.Thread(target=_worker, args=(playlist_id,), daemon=True).start()
        except Exception:
            pass

    def show_videos_search_page(self, page_token=None):
        if self.search_mode != 'videos' or not self.video_search_query:
            return
        try:
            max_results = int(self.video.page_size_var.get())
            resp = self.controller.playlist_handler.search_videos(self.video_search_query, max_results=max_results, page_token=page_token)
            videos = resp.get('videos', [])
            try:
                for i, v in enumerate(videos, 1):
                    v['videoOrder'] = i
            except Exception:
                pass
            self.current_videos = videos
            self.video_next_page_token = resp.get('nextPageToken')
            self.video_prev_page_token = resp.get('prevPageToken')
            self.video.video_tree.delete(*self.video.video_tree.get_children())
            for v in videos:
                try:
                    vid = v.get('videoId')
                    tags = ('search_hit',) if vid in getattr(self, 'video_search_ids', set()) else ()
                    self.video.video_tree.insert('', 'end', values=self._video_row(v), tags=tags)
                except Exception:
                    self.video.video_tree.insert('', 'end', values=self._video_row(v))
            try:
                self.video.prev_page_btn["state"] = "normal" if self.video_prev_page_token else "disabled"
                self.video.next_page_btn["state"] = "normal" if self.video_next_page_token else "disabled"
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch videos: {e}")

    # Core functionality methods
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
        if event:
            selected_item = self.playlist.get_selected_playlist()
        else:
            selected_item = self.playlist.playlist_tree.selection()[0]
        
        if not selected_item:
            return

        playlist_id = selected_item
        try:
            if self._playlist_open_busy:
                self._pending_open = (playlist_id, page_token)
                try:
                    self.status_bar.configure(text="Opening previous playlist... please wait")
                except Exception:
                    pass
                return
        except Exception:
            pass
        playlist_values = self.playlist.playlist_tree.item(selected_item)["values"]
        try:
            self._set_pinned_playlist(playlist_id)
            self._log(f"Opening playlist {playlist_id} page_token={page_token}")
            self._last_open_playlist_id = playlist_id
        except Exception:
            pass
            
        playlist_title = playlist_values[0]
        channel_title = playlist_values[1]
        try:
            total_videos = int(playlist_values[2])
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
            max_results = int(self.video.page_size_var.get())
            try:
                cached = self._get_cached_playlist_page(playlist_id, page_token)
            except Exception:
                cached = None
            if cached is not None:
                try:
                    print(f"[Cache] Using cached page for playlist {playlist_id}")
                except Exception:
                    pass
                try:
                    self.current_videos = list(cached.get('videos', []))
                    self.prev_page_token = cached.get('prevPageToken')
                    self.current_page_token = cached.get('nextPageToken')
                except Exception:
                    pass
                try:
                    pi_local = None
                    try:
                        pi_local = self.assign_playlist_index(playlist_id)
                    except Exception:
                        pass
                    for v in list(self.current_videos or []):
                        if pi_local is not None:
                            v['playlistIndex'] = pi_local
                        vid = v.get('videoId')
                        if vid:
                            self.video_playlist_cache[vid] = playlist_id
                except Exception:
                    pass
                try:
                    self._render_playlist_videos(total_videos)
                except Exception:
                    pass
                return
            def _finish_open_fail():
                try:
                    self._playlist_open_busy = False
                    nxt = self._pending_open
                    self._pending_open = None
                    if nxt:
                        pid, tok = nxt
                        try:
                            self.playlist.playlist_tree.selection_set(pid)
                        except Exception:
                            pass
                        self.show_playlist_videos(page_token=tok)
                except Exception:
                    pass
            def _worker_open(mr):
                def _fetch(mr2):
                    return self.controller.playlist_handler.get_videos(
                        playlist_id,
                        page_token,
                        max_results=mr2
                    )
                try:
                    resp = _fetch(mr)
                except Exception as e:
                    try:
                        import ssl
                        is_ssl = isinstance(e, ssl.SSLError) or ('SSL' in str(e))
                    except Exception:
                        is_ssl = 'SSL' in str(e)
                    if is_ssl:
                        try:
                            import time; time.sleep(0.3)
                        except Exception:
                            pass
                        try:
                            mr2 = max(5, int(mr // 2) or 10)
                        except Exception:
                            mr2 = 10
                        try:
                            resp = _fetch(mr2)
                        except Exception:
                            try:
                                self.after(0, lambda: self.status_bar.configure(text="Network issue; highlighted matches instead"))
                            except Exception:
                                pass
                            try:
                                self.after(0, lambda: self.highlight_videos_for_playlist(playlist_id))
                            except Exception:
                                pass
                            try:
                                self.after(0, _finish_open_fail)
                            except Exception:
                                pass
                            return
                    else:
                        try:
                            self.after(0, lambda: self.status_bar.configure(text="Network issue; highlighted matches instead"))
                        except Exception:
                            pass
                        try:
                            self.after(0, lambda: self.highlight_videos_for_playlist(playlist_id))
                        except Exception:
                            pass
                        try:
                            self.after(0, _finish_open_fail)
                        except Exception:
                            pass
                        return
                def _apply():
                    try:
                        self.current_videos = resp["videos"]
                        self.current_page_token = resp.get("nextPageToken")
                        self.prev_page_token = resp.get("prevPageToken")
                        try:
                            self._cache_playlist_videos(playlist_id, page_token, resp)
                            print(f"[Cache] Stored page for playlist {playlist_id} token={page_token}")
                        except Exception:
                            pass
                        try:
                            self.video.prev_page_btn.configure(command=lambda: self.show_playlist_videos(page_token=self.prev_page_token))
                            self.video.next_page_btn.configure(command=lambda: self.show_playlist_videos(page_token=self.current_page_token))
                        except Exception:
                            pass
                        try:
                            self._render_playlist_videos(total_videos)
                        except Exception:
                            pass
                        try:
                            self.video.next_page_btn["state"] = "normal" if self.current_page_token else "disabled"
                            self.video.prev_page_btn["state"] = "normal" if self.prev_page_token else "disabled"
                            self.video.update_back_button_state(True)
                        except Exception:
                            pass
                        try:
                            self._playlist_open_busy = False
                            nxt = self._pending_open
                            self._pending_open = None
                            if nxt:
                                pid, tok = nxt
                                try:
                                    self.playlist.playlist_tree.selection_set(pid)
                                except Exception:
                                    pass
                                self.show_playlist_videos(page_token=tok)
                        except Exception:
                            pass
                    except Exception:
                        pass
                try:
                    self.after(0, _apply)
                except Exception:
                    pass
            try:
                import threading
                self.status_bar.configure(text="Loading playlist videos...")
                self._log(f"Spawn worker for playlist {playlist_id}")
                try:
                    self._playlist_open_busy = True
                except Exception:
                    pass
                threading.Thread(target=_worker_open, args=(max_results,), daemon=True).start()
                return
            except Exception as e:
                self._log(f"Failed to spawn worker: {e}")
        
            response = self.controller.playlist_handler.get_videos(
                playlist_id,
                page_token,
                max_results=max_results
            )
            self.current_videos = response["videos"]
            self.current_page_token = response.get("nextPageToken")
            self.prev_page_token = response.get("prevPageToken")

            # Assign selected playlist number to all videos shown
            try:
                pi = self.assign_playlist_index(playlist_id)
            except Exception:
                pi = None
            try:
                for v in self.current_videos:
                    if pi is not None:
                        v['playlistIndex'] = pi
                    vid = v.get('videoId')
                    if vid:
                        self.video_playlist_cache[vid] = playlist_id
            except Exception:
                pass
            try:
                self.video.prev_page_btn.configure(command=lambda: self.show_playlist_videos(page_token=self.prev_page_token))
                self.video.next_page_btn.configure(command=lambda: self.show_playlist_videos(page_token=self.current_page_token))
            except Exception:
                pass

            self._render_playlist_videos(total_videos)

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
            self.video.update_back_button_state(True)

        except Exception as e:
            try:
                self.status_bar.configure(text="Network issue; highlighted matches instead")
            except Exception:
                pass
            try:
                self.highlight_videos_for_playlist(playlist_id)
            except Exception:
                pass

    def _render_playlist_videos(self, total_videos):
        try:
            self.video.video_tree.delete(*self.video.video_tree.get_children())
        except Exception:
            pass
        hit_count = 0
        ql = (self.video_search_query or '').strip().lower()
        try:
            print(f"[Playlist] {self.current_playlist_info.get('title','')} ({self.current_playlist_info.get('id','')})")
        except Exception:
            pass
        for video in list(self.current_videos or []):
            try:
                video['videoOrder'] = int(hit_count + 1)
            except Exception:
                pass
            try:
                vid = video.get('videoId')
                ttl = str(video.get('title', '')).lower()
                chn = str(video.get('channelTitle', '')).lower()
                # Highlight guard: match either previously found video ids or fuzzy title/channel hits by last query
                is_hit = (vid in getattr(self, 'video_search_ids', set())) or (ql and (ql in ttl or ql in chn))
                tags = ('search_hit',) if is_hit else ()
                row = self._video_row(video)
                if is_hit:
                    hit_count += 1
                    try:
                        row = (f"★ {row[0]}",) + row[1:]
                    except Exception:
                        pass
                self.video.video_tree.insert("", "end", values=row, tags=tags)
                try:
                    pub = self._fmt_date(video.get('published',''))
                    vs = video.get('views','')
                    print(f" - {video.get('title','')} | {video.get('duration','')} | {pub} | {vs}")
                except Exception:
                    pass
            except Exception:
                try:
                    self.video.video_tree.insert("", "end", values=self._video_row(video))
                except Exception:
                    pass
        try:
            self.status_bar.configure(text=f"Highlighted {hit_count} matched videos in playlist")
        except Exception:
            pass
        try:
            max_results = int(self.video.page_size_var.get())
        except Exception:
            max_results = 10
        total_pages = (total_videos + max_results - 1) // max_results
        if not hasattr(self, 'current_page') or (self.prev_page_token is None and self.current_page_token is None):
            self.current_page = 1
        try:
            self.video.total_label["text"] = f"Total videos: {total_videos}"
            self.video.page_indicator["text"] = f"Page {self.current_page} of {total_pages}"
            self.video.next_page_btn["state"] = "normal" if self.current_page_token else "disabled"
            self.video.prev_page_btn["state"] = "normal" if self.prev_page_token else "disabled"
            self.video.prev_page_btn.configure(command=lambda: self.show_playlist_videos(page_token=self.prev_page_token))
            self.video.next_page_btn.configure(command=lambda: self.show_playlist_videos(page_token=self.current_page_token))
            self.video.update_back_button_state(True)
        except Exception:
            pass

    def on_video_header_double_click(self, column_name):
        try:
            import tkinter.simpledialog as simpledialog
        except Exception:
            return
        col_map = {
            "Title": "title",
            "Channel": "channelTitle",
            "Duration": "duration",
            "Published": "published",
            "Views": "views"
        }
        key = col_map.get(column_name)
        if not key:
            return
        q = simpledialog.askstring("Filter", f"Filter {column_name} contains:")
        if q is None:
            return
        ql = q.strip().lower()
        items = []
        for v in self.current_videos:
            val = str(v.get(key, ""))
            if ql in val.lower():
                items.append(v)
        self.video.video_tree.delete(*self.video.video_tree.get_children())
        for v in items:
            self.video.video_tree.insert('', 'end', values=self._video_row(v))

    def on_playlist_header_double_click(self, column_name):
        try:
            import tkinter.simpledialog as simpledialog
        except Exception:
            return
        idx_map = {
            "No": 0,
            "Title": 1,
            "Channel": 2,
            "Videos": 3,
            "Status": 4,
            "Actions": 5
        }
        idx = idx_map.get(column_name)
        if idx is None:
            return
        q = simpledialog.askstring("Filter", f"Filter {column_name} contains:")
        if q is None:
            return
        ql = (q or '').strip().lower()
        for item in self.playlist.playlist_tree.get_children():
            vals = self.playlist.playlist_tree.item(item).get('values', [])
            s = str(vals[idx]) if idx < len(vals) else ''
            if ql and ql not in s.lower():
                self.playlist.playlist_tree.detach(item)
            else:
                try:
                    self.playlist.playlist_tree.reattach(item, '', 'end')
                except Exception:
                    pass

    def sort_videos_by(self, column_name):
        col_map = {
            "Title": (lambda v: str(v.get('title', '')).lower()),
            "Playlist": (lambda v: int(v.get('playlistIndex') or 0)),
            "Channel": (lambda v: str(v.get('channelTitle', '')).lower()),
            "Duration": (lambda v: str(v.get('duration', ''))),
            "Published": (lambda v: v.get('published', '')),
            "Views": (lambda v: int(v.get('views') or 0))
        }
        keyfunc = col_map.get(column_name)
        if not keyfunc:
            return
        asc = self.video_sort_state.get(column_name, False)
        try:
            self.current_videos.sort(key=keyfunc, reverse=not asc)
        except Exception:
            try:
                self.current_videos.sort(key=lambda v: str(keyfunc(v)))
            except Exception:
                return
        self.video_sort_state[column_name] = not asc
        self.video.video_tree.delete(*self.video.video_tree.get_children())
        for v in self.current_videos:
            self.video.video_tree.insert('', 'end', values=self._video_row(v))

    def sort_playlists_by(self, column_name):
        idx_map = {"No": 0, "Title": 1, "Channel": 2, "Videos": 3, "Status": 4, "Actions": 5}
        idx = idx_map.get(column_name)
        if idx is None:
            return
        asc = self.playlist_sort_state.get(column_name, False)
        rows = []
        for item in self.playlist.playlist_tree.get_children(''):
            vals = self.playlist.playlist_tree.item(item).get('values', [])
            rows.append((item, vals))
        def _key(row):
            v = row[1][idx] if idx < len(row[1]) else ''
            if column_name == 'Videos':
                try:
                    return int(v)
                except Exception:
                    return -1
            if column_name == 'No':
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

    def set_concurrent_fragments(self, n):
        try:
            self.download_concurrent_fragments = int(n)
            self.status_bar.configure(text=f"Concurrent fragments: {n}")
        except Exception:
            self.download_concurrent_fragments = 1

    def toggle_post_processing(self):
        self.post_processing_enabled = not self.post_processing_enabled
        try:
            state = 'ON' if self.post_processing_enabled else 'OFF'
            self.status_bar.configure(text=f"Post-processing: {state}")
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

    def set_preferred_quality(self, value: str):
        try:
            ConfigManager.set_preferred_quality(value)
            try:
                self.status_bar.configure(text=f"Preferred quality set: {value}")
            except Exception:
                pass
        except Exception:
            pass

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
