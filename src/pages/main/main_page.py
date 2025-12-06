import tkinter as tk
from tkinter import messagebox, filedialog
import webbrowser
import os
import csv
import sys
import subprocess
import threading  # Add this for download threading
import json
import tkinter.ttk as ttk
try:
    from src.config_manager import ConfigManager
except ModuleNotFoundError:
    from config_manager import ConfigManager
from .menu_section import MenuSection
from .search_section import SearchSection
from .playlist_section import PlaylistSection
from .video_section import VideoSection
from .status_bar import StatusBar
from .video_player import VideoPlayer
from .download_options_dialog import DownloadOptionsDialog
from .download_manager import DownloadManager
try:
    from src.services.video_playlist_scanner import VideoPlaylistScanner
except ModuleNotFoundError:
    from services.video_playlist_scanner import VideoPlaylistScanner

class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_videos = []
        self.current_playlist_info = {}
        self.current_page_token = None
        self._initialize_components()

    def _safe_ui(self, fn):
        try:
            if not self.winfo_exists():
                return
            try:
                self.after(0, fn)
            except Exception:
                pass
        except Exception:
            pass

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
                try:
                    self.video.update_mode_ui(True)
                except Exception:
                    pass
            elif lm == 'playlists':
                try:
                    self.search.mode_var.set('Playlists')
                except Exception:
                    pass
                self.search_mode = 'playlists'
                self._load_last_search('Playlists')
                try:
                    self.video.update_mode_ui(False)
                except Exception:
                    pass
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
        self.playlist_video_ids = {}
        self._preview_only_hits = False
        self._last_open_playlist_id = None
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
            status = self._video_download_status(v)
            return (
                v.get('title', ''),
                idx,
                v.get('channelTitle', ''),
                v.get('duration', 'N/A'),
                self._fmt_date(v.get('published', '')),
                (f"{int(v.get('views', '0')):,}" if str(v.get('views', '0')).isdigit() else v.get('views', '0')),
                status,
                "🗑"
            )
        self._video_row = _video_row
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
        try:
            self.video.update_mode_ui(self.search_mode == 'videos')
        except Exception:
            pass
        try:
            self._create_mid_controls()
        except Exception:
            pass

    def _video_target_folder(self, v):
        try:
            if getattr(self, 'download_folder', None):
                return self.download_folder
            vid = v.get('videoId')
            pid = v.get('playlistId') or self.video_playlist_cache.get(vid)
            if not pid:
                try:
                    pid = self._resolve_playlist_for_video(v)
                except Exception:
                    pid = None
            if pid:
                try:
                    ttl = ''
                    if self.playlist.playlist_tree.exists(pid):
                        vals = self.playlist.playlist_tree.item(pid).get('values', [])
                        ttl = vals[1] if len(vals) > 1 else ''
                    return os.path.join(self.controller.default_folder, f"Playlist - {ttl or 'Unknown'}")
                except Exception:
                    pass
            try:
                opts = getattr(self, '_download_opts', {})
                fv = bool(opts.get('fallback_videos', True))
            except Exception:
                fv = True
            if fv:
                try:
                    use_ct = bool(opts.get('use_channel_title_fallback', True))
                except Exception:
                    use_ct = True
                if use_ct:
                    ct = str(v.get('channelTitle','')).strip()
                    if ct:
                        q = ct
                    else:
                        q = getattr(self, 'video_search_query', '') or 'Misc'
                else:
                    q = getattr(self, 'video_search_query', '') or 'Misc'
                return os.path.join(self.controller.default_folder, f"Videos - {q}")
            return os.path.join(self.controller.default_folder, f"Playlist - Unknown")
        except Exception:
            return self.controller.default_folder

    def _find_downloaded_file(self, folder, title, video_id=None):
        try:
            name = str(title or '').strip()
            if not folder or not name:
                return None
            exts = ('.mp4', '.webm', '.mkv')
            candidates = []
            for f in os.listdir(folder):
                try:
                    if not any(f.lower().endswith(e) for e in exts):
                        continue
                    fl = f.lower()
                    if video_id and str(video_id).lower() in fl:
                        candidates.append(os.path.join(folder, f))
                        continue
                    import re
                    def _norm(s):
                        return re.sub(r"[^a-z0-9]+"," ", s.lower()).strip()
                    if _norm(fl).startswith(_norm(name)[:50]):
                        candidates.append(os.path.join(folder, f))
                except Exception:
                    pass
            if not candidates:
                return None
            try:
                candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            except Exception:
                pass
            return candidates[0]
        except Exception:
            return None

    def _video_download_status(self, v):
        try:
            folder = self._video_target_folder(v)
            try:
                os.makedirs(folder, exist_ok=True)
            except Exception:
                pass
            fp = self._find_downloaded_file(folder, v.get('title',''), v.get('videoId'))
            return "Downloaded" if fp else "Not Downloaded"
        except Exception:
            return "Unknown"

    def _count_downloaded_files(self, folder):
        try:
            exts = ('.mp4', '.webm', '.mkv')
            return len([f for f in os.listdir(folder) if any(f.lower().endswith(e) for e in exts)])
        except Exception:
            return 0

    def _playlist_folder_by_id(self, playlist_id):
        try:
            ttl = ''
            if self.playlist.playlist_tree.exists(playlist_id):
                vals = self.playlist.playlist_tree.item(playlist_id).get('values', [])
                ttl = vals[1] if len(vals) > 1 else ''
            return os.path.join(self.controller.default_folder, f"Playlist - {ttl or 'Unknown'}")
        except Exception:
            return self.controller.default_folder

    def _playlist_download_status(self, playlist_id, expected_count):
        try:
            folder = self._playlist_folder_by_id(playlist_id)
            if not os.path.exists(folder):
                return "Not Downloaded"
            cnt = self._count_downloaded_files(folder)
            try:
                exp = int(expected_count or 0)
            except Exception:
                exp = 0
            if cnt == 0:
                return "Empty Folder"
            if exp and cnt >= exp:
                return "Complete"
            if exp:
                return f"{cnt}/{exp}"
            return str(cnt)
        except Exception:
            return "Unknown"

    def refresh_video_statuses(self):
        try:
            items = list(self.video.video_tree.get_children())
        except Exception:
            items = []
        for i, iid in enumerate(items):
            try:
                v = self.current_videos[i] if i < len(self.current_videos) else None
                if not v:
                    continue
                self.video.video_tree.item(iid, values=self._video_row(v))
            except Exception:
                pass
        try:
            pass
        except Exception:
            pass

    def refresh_all_statuses(self):
        try:
            self.playlist.refresh_all_statuses()
        except Exception:
            pass
        try:
            self.refresh_video_statuses()
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

    def _cache_playlist_videos(self, playlist_id, page_token, response):
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

    def _get_cached_playlist_page(self, playlist_id, page_token):
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

    def assign_playlist_index(self, playlist_id):
        if playlist_id in self.playlist_index_map:
            return self.playlist_index_map[playlist_id]
        idx = len(self.playlist_index_map) + 1
        self.playlist_index_map[playlist_id] = idx
        return idx

    def _pack_sections(self):
        """Pack sections into the main page."""
        self.search.pack(fill="x", padx=10, pady=5)
        self.video.pack(fill="both", expand=True, padx=10, pady=5)
        try:
            self._mid_controls.pack(fill="x", padx=10, pady=(0,5))
        except Exception:
            pass
        self.playlist.pack(fill="both", expand=True, padx=10, pady=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_mid_controls(self):
        try:
            frm = tk.Frame(self)
            self._mid_controls = frm
            btn = tk.Button(frm, text="Refresh Status", command=self.refresh_all_statuses)
            btn.pack(side=tk.LEFT, padx=6, pady=2)
            import tkinter.ttk as ttk
            self._mid_pb = ttk.Progressbar(frm, orient="horizontal", length=220, mode="determinate")
            self._mid_pb.pack(side=tk.LEFT, padx=8)
            self._mid_label = ttk.Label(frm, text="")
            self._mid_label.pack(side=tk.LEFT, padx=8)
            self._mid_total = 0
            self._mid_job_title = None
        except Exception:
            self._mid_controls = None
            self._mid_pb = None
            self._mid_label = None
            self._mid_total = 0
            self._mid_job_title = None

    def set_mid_job_title(self, title: str):
        try:
            self._mid_job_title = str(title or '').strip() or None
        except Exception:
            pass

    def show_mid_scan(self, total: int):
        try:
            self._mid_total = max(int(total or 0), 1)
            if self._mid_pb:
                self._mid_pb['value'] = 0
            if self._mid_label:
                prefix = self._mid_job_title or 'Scanning'
                self._mid_label.configure(text=f"{prefix}: 0/{self._mid_total}")
        except Exception:
            pass

    def update_mid_scan_progress(self, processed: int, total: int = None):
        try:
            if total is not None:
                self._mid_total = max(int(total or 0), 1)
            p = max(0, int(processed or 0))
            t = max(1, int(self._mid_total or 1))
            val = min(100, int(p * 100 / t))
            if self._mid_pb:
                self._mid_pb['value'] = val
            if self._mid_label:
                prefix = self._mid_job_title or 'Scanning'
                self._mid_label.configure(text=f"{prefix}: {p}/{t}")
        except Exception:
            pass

    def finish_mid_scan(self):
        try:
            if self._mid_label:
                prefix = self._mid_job_title or 'Scanning'
                self._mid_label.configure(text=f"{prefix}: done")
            if self._mid_pb:
                self._mid_pb['value'] = 0
            self._mid_job_title = None
        except Exception:
            pass

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

    def set_search_mode(self, mode_display):
        mode = (mode_display or '').strip().lower()
        if mode not in ('playlists', 'videos'):
            mode = 'playlists'
        if mode != self.search_mode:
            self.search_mode = mode
            self.clear_panels()
            try:
                self._load_last_search(mode_display)
            except Exception:
                pass
            try:
                ConfigManager.save_last_mode(mode)
            except Exception:
                pass
            try:
                self.video.update_mode_ui(self.search_mode == 'videos')
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
                q = data.get('query', '')
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
                ConfigManager.save_json(ConfigManager.get_last_search_path('playlists'), {
                    'query': query,
                    'playlists': enriched
                })
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
                    self._safe_ui(lambda: self.set_mid_job_title('Mapping playlists'))
                    self._safe_ui(lambda t=len(videos): self.video.show_scan(t))
                    self._safe_ui(lambda t=len(videos): self.show_mid_scan(t))
                    collected_local = []
                    scanner = VideoPlaylistScanner(self.controller.api_key)
                    def _on_pl(pl):
                        plid = pl.get('playlistId')
                        try:
                            pi = self.assign_playlist_index(plid)
                        except Exception:
                            pi = None
                        self._safe_ui(lambda d=pl: self.playlist.update_playlist(d))
                        collected_local.append(pl)
                        return pi
                    def _prefetch(pid):
                        try:
                            from src.playlist import Playlist as _Pl
                        except ModuleNotFoundError:
                            from playlist import Playlist as _Pl
                        try:
                            ph2 = _Pl(self.controller.api_key)
                            resp_pf = ph2.get_videos(pid, None, max_results=10)
                            self._cache_playlist_videos(pid, None, resp_pf)
                        except Exception:
                            pass
                    def _progress(done, total):
                        self._safe_ui(lambda x=done, t=total: self.status_bar.configure(text=f"Collecting playlists from videos... {x}/{t}"))
                        self._safe_ui(lambda x=done, t=total: self.video.update_scan_progress(x, t))
                        self._safe_ui(lambda x=done, t=total: self.update_mid_scan_progress(x, t))
                    def _index(vid, pid, idx):
                        self._safe_ui(lambda v_id=vid, p_id=pid: self._update_video_row_by_vid(v_id, p_id))
                    try:
                        scanner.scan(videos, _on_pl, _prefetch, _progress, _index)
                    except Exception:
                        pass
                    try:
                        ConfigManager.save_json(ConfigManager.get_last_search_path('videos'), {
                            'query': query,
                            'videos': videos,
                            'playlists': collected_local,
                            'nextPageToken': self.video_next_page_token,
                            'prevPageToken': self.video_prev_page_token,
                            'videoIds': list(self.video_search_ids),
                            'playlistPages': {pid: {'pages': cache.get('pages', {}), 'tokens': cache.get('tokens', {})} for pid, cache in (self.playlist_videos_cache or {}).items()},
                            'playlistIds': {pid: list(self.playlist_video_ids.get(pid, set())) for pid in (self.playlist_video_ids or {}).keys()}
                        })
                        self.collected_playlists = collected_local
                        try:
                            vids_cnt = len(videos or [])
                        except Exception:
                            vids_cnt = 0
                        self._safe_ui(lambda n=len(collected_local), v=vids_cnt: self.status_bar.configure(text=f"Collected {n} playlists for {v} videos"))
                        self._safe_ui(lambda: self.video.finish_scan())
                        self._safe_ui(lambda: self.finish_mid_scan())
                    except Exception:
                        pass
            try:
                threading.Thread(target=_fetch_playlists, daemon=True).start()
            except Exception:
                pass
            ConfigManager.save_json(ConfigManager.get_last_search_path('videos'), {
                'query': query,
                'videos': videos,
                'playlists': [],
                'nextPageToken': self.video_next_page_token,
                'prevPageToken': self.video_prev_page_token,
                'videoIds': list(self.video_search_ids),
                'playlistPages': {pid: {'pages': cache.get('pages', {}), 'tokens': cache.get('tokens', {})} for pid, cache in (self.playlist_videos_cache or {}).items()},
                'playlistIds': {pid: list(self.playlist_video_ids.get(pid, set())) for pid in (self.playlist_video_ids or {}).keys()}
            })
            self.video.update_back_button_state(False)
            try:
                self.video.prev_page_btn.configure(command=lambda: self.show_videos_search_page(self.video_prev_page_token))
                self.video.next_page_btn.configure(command=lambda: self.show_videos_search_page(self.video_next_page_token))
                has_prev = bool(self.video_prev_page_token)
                has_next = bool(self.video_next_page_token)
                self.video.prev_page_btn["state"] = "normal" if has_prev else "disabled"
                self.video.next_page_btn["state"] = "normal" if has_next else "disabled"
                try:
                    idx = int(getattr(self, 'video_search_page_index', 1) or 1)
                except Exception:
                    idx = 1
                try:
                    count_items = len(self.video.video_tree.get_children())
                except Exception:
                    count_items = len(videos)
                try:
                    self.video._panel.update_pages(index=idx, has_prev=has_prev, has_next=has_next, total_items=count_items)
                except Exception:
                    pass
            except Exception:
                pass

    def back_to_video_results(self):
        if self.search_mode != 'videos':
            return
        data = {}
        try:
            ds = getattr(self.controller, 'datastore', None)
            if ds and hasattr(ds, 'load_last_videos_result'):
                d = ds.load_last_videos_result() or {}
                if isinstance(d, dict) and d:
                    data = d
        except Exception:
            pass
        if not data:
            try:
                path = ConfigManager.get_last_search_path('videos')
                data = ConfigManager.load_json(path) or {}
            except Exception:
                data = {}
        self.clear_panels()
        try:
            self.playlist_index_map = {}
        except Exception:
            pass
        videos = data.get('videos', [])
        playlists = data.get('playlists', [])
        try:
            ppages = data.get('playlistPages') or {}
            if isinstance(ppages, dict):
                self.playlist_videos_cache = ppages
        except Exception:
            pass
        try:
            pids = data.get('playlistIds') or {}
            if isinstance(pids, dict):
                self.playlist_video_ids = {pid: set(v or []) for pid, v in pids.items()}
        except Exception:
            pass
        try:
            q = data.get('query', '')
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
        try:
            rev = {idx: pid for pid, idx in (self.playlist_index_map or {}).items()}
            for v in list(self.current_videos or []):
                try:
                    pi = v.get('playlistIndex')
                    vid = v.get('videoId')
                    pid = rev.get(pi)
                    if pid and vid:
                        self.video_playlist_cache[vid] = pid
                except Exception:
                    pass
        except Exception:
            pass
        self.video_prev_page_token = data.get('prevPageToken')
        self.video_next_page_token = data.get('nextPageToken')
        try:
            self.video_search_page_index = int(data.get('pageIndex') or 1)
            self.video.page_indicator["text"] = f"Results page {self.video_search_page_index}"
            try:
                self.video.set_total_videos(len(videos))
            except Exception:
                self.video.total_label["text"] = f"Items: {len(videos)}"
        except Exception:
            pass
        try:
            self.video.prev_page_btn.configure(command=lambda: self.show_videos_search_page(self.video_prev_page_token))
            self.video.next_page_btn.configure(command=lambda: self.show_videos_search_page(self.video_next_page_token))
            has_prev = bool(self.video_prev_page_token)
            has_next = bool(self.video_next_page_token)
            self.video.prev_page_btn["state"] = "normal" if has_prev else "disabled"
            self.video.next_page_btn["state"] = "normal" if has_next else "disabled"
            try:
                idx = int(getattr(self, 'video_search_page_index', 1) or 1)
            except Exception:
                idx = 1
            try:
                count_items = len(self.video.video_tree.get_children())
            except Exception:
                count_items = len(videos)
            try:
                self.video._panel.update_pages(index=idx, has_prev=has_prev, has_next=has_next, total_items=count_items)
            except Exception:
                pass
        except Exception:
            pass
        self.video.update_back_button_state(True)
        try:
            self.video.update_mode_ui(True)
        except Exception:
            pass
        try:
            self._preview_only_hits = False
            self._preview_active = False
            try:
                self.playlist.playlist_tree.configure(selectmode='browse')
            except Exception:
                pass
        except Exception:
            pass
        try:
            self.status_bar.configure(text="Back to video results")
        except Exception:
            pass
        try:
            if not self.collected_playlists and self.current_videos:
                self._log("Re-triggering playlist collection for restored results")
                import threading as _t
                def _collect_again():
                    collected = []
                    processed = 0
                    total = len(self.current_videos or [])
                    try:
                        self.after(0, lambda: self.set_mid_job_title('Mapping playlists'))
                        self.after(0, lambda t=total: self.video.show_scan(t))
                        self.after(0, lambda t=total: self.show_mid_scan(t))
                    except Exception:
                        pass
                    for v in list(self.current_videos or []):
                        vid = v.get('videoId')
                        cid = v.get('channelId')
                        if not vid or not cid:
                            processed += 1
                            try:
                                self.after(0, lambda x=processed, t=total: self.video.update_scan_progress(x, t))
                            except Exception:
                                pass
                            continue
                        try:
                            chpls = self.controller.playlist_handler.get_channel_playlists(cid, max_results=20)
                        except Exception:
                            chpls = []
                        first_index = None
                        first_plid = None
                        for pl in chpls:
                            plid = pl.get('playlistId')
                            has = False
                            try:
                                ids_set = self.playlist_video_ids.get(plid)
                                if ids_set is None:
                                    cached_page = self._get_cached_playlist_page(plid, None)
                                    if cached_page:
                                        try:
                                            ids_set = {x.get('videoId') for x in cached_page.get('videos', []) if x.get('videoId')}
                                        except Exception:
                                            ids_set = set()
                                        try:
                                            self.playlist_video_ids[plid] = ids_set
                                        except Exception:
                                            pass
                                if ids_set is None:
                                    try:
                                        resp_pf_local = self.controller.playlist_handler.get_videos(plid, None, max_results=10)
                                        self._cache_playlist_videos(plid, None, resp_pf_local)
                                        try:
                                            ids_set = {x.get('videoId') for x in resp_pf_local.get('videos', []) if x.get('videoId')}
                                            self.playlist_video_ids[plid] = ids_set
                                        except Exception:
                                            ids_set = set()
                                    except Exception:
                                        ids_set = set()
                                has = bool(vid) and (vid in (ids_set or set()))
                            except Exception:
                                has = False
                            if not has:
                                continue
                            if not any(p.get('playlistId') == plid for p in collected):
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
                        if first_index and first_plid:
                            try:
                                v['playlistIndex'] = first_index
                                self.after(0, lambda v_id=vid, p_id=first_plid: self._update_video_row_by_vid(v_id, p_id))
                            except Exception:
                                pass
                        processed += 1
                        try:
                            self.after(0, lambda x=processed, t=total: self.status_bar.configure(text=f"Collecting playlists from videos... {x}/{t}"))
                            self.after(0, lambda x=processed, t=total: self.video.update_scan_progress(x, t))
                            self.after(0, lambda x=processed, t=total: self.update_mid_scan_progress(x, t))
                        except Exception:
                            pass
                    try:
                        ConfigManager.save_json(ConfigManager.get_last_search_path('videos'), {
                            'query': self.video_search_query,
                            'videos': self.current_videos,
                            'playlists': collected,
                            'nextPageToken': self.video_next_page_token,
                            'prevPageToken': self.video_prev_page_token,
                            'videoIds': list(getattr(self, 'video_search_ids', set()))
                        })
                        self.collected_playlists = collected
                        try:
                            try:
                                vc = len(self.current_videos or [])
                            except Exception:
                                vc = 0
                            self.after(0, lambda n=len(collected), v=vc: self.status_bar.configure(text=f"Collected {n} playlists for {v} videos"))
                        except Exception:
                            pass
                        try:
                            self.after(0, lambda: self.video.finish_scan())
                            self.after(0, lambda: self.finish_mid_scan())
                        except Exception:
                            pass
                    except Exception:
                        pass
                try:
                    _t.Thread(target=_collect_again, daemon=True).start()
                except Exception:
                    pass
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
                for pl in list(self.collected_playlists or []):
                    plid = pl.get('playlistId')
                    if not plid:
                        continue
                    try:
                        ids_set = self.playlist_video_ids.get(plid)
                        if ids_set is None:
                            cached_page = self._get_cached_playlist_page(plid, None)
                            if cached_page:
                                try:
                                    ids_set = {x.get('videoId') for x in cached_page.get('videos', []) if x.get('videoId')}
                                except Exception:
                                    ids_set = set()
                                try:
                                    self.playlist_video_ids[plid] = ids_set
                                except Exception:
                                    pass
                        has = bool(video_id) and (video_id in (ids_set or set()))
                    except Exception:
                        has = False
                    if not has:
                        try:
                            has = self.controller.playlist_handler.playlist_contains_video(plid, video_id)
                        except Exception:
                            has = False
                    if has:
                        found = plid
                        try:
                            self.video_playlist_cache[video_id] = found
                        except Exception:
                            pass
                        break
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
                                    self.video.video_tree.item(items[selected_index], values=self._video_row(self.current_videos[selected_index]))
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

    def show_videos_search_page(self, page_token=None):
        if self.search_mode != 'videos' or not self.video_search_query:
            return
        try:
            max_results = int(self.video.page_size_var.get())
            resp = self.controller.playlist_handler.search_videos(self.video_search_query, max_results=max_results, page_token=page_token)
            videos = resp.get('videos', [])
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
                has_prev = bool(self.video_prev_page_token)
                has_next = bool(self.video_next_page_token)
                self.video.prev_page_btn["state"] = "normal" if has_prev else "disabled"
                self.video.next_page_btn["state"] = "normal" if has_next else "disabled"
                try:
                    idx = int(getattr(self, 'video_search_page_index', 1) or 1)
                except Exception:
                    idx = 1
                try:
                    count_items = len(self.video.video_tree.get_children())
                except Exception:
                    count_items = len(videos)
                try:
                    self.video._panel.update_pages(index=idx, has_prev=has_prev, has_next=has_next, total_items=count_items)
                except Exception:
                    pass
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch videos: {e}")

    def execute_search_stable(self, query, mode_display):
        try:
            return self.execute_search(query, mode_display)
        except Exception:
            pass

    def show_playlist_videos_stable(self, playlist_id):
        try:
            if playlist_id:
                try:
                    self.playlist.playlist_tree.selection_set(playlist_id)
                except Exception:
                    pass
            self.show_playlist_videos()
        except Exception:
            pass

    def map_videos_to_playlists(self, videos):
        collected = []
        try:
            existing = list(self.playlist.playlist_tree.get_children())
        except Exception:
            existing = []
        index_map = dict(self.playlist_index_map or {})
        for v in list(videos or []):
            vid = v.get('videoId')
            target = None
            for pid in existing:
                try:
                    if self.controller.playlist_handler.playlist_contains_video(pid, vid):
                        target = pid
                        break
                except Exception:
                    continue
            if not target:
                continue
            if not any(p.get('playlistId') == target for p in collected):
                try:
                    info = self.controller.playlist_handler.get_playlist_info(target)
                except Exception:
                    info = {'playlistId': target, 'title': '', 'channelTitle': '', 'video_count': 'N/A'}
                collected.append(info)
            if target not in index_map:
                index_map[target] = len(index_map) + 1
            v['playlistId'] = target
            v['playlistIndex'] = index_map.get(target)
            self.video_playlist_cache[vid] = target
        try:
            self.playlist_index_map = index_map
        except Exception:
            pass
        try:
            items = self.video.video_tree.get_children()
            for i, item in enumerate(items):
                if i < len(videos):
                    self.video.video_tree.item(item, values=self._video_row(videos[i]))
        except Exception:
            pass
        return collected

    def normalize_playlist_indices(self):
        try:
            pids = list(self.playlist_index_map.keys())
            new_map = {}
            for i, pid in enumerate(pids, start=1):
                new_map[pid] = i
            self.playlist_index_map = new_map
        except Exception:
            pass
        try:
            for v in list(self.current_videos or []):
                pid = v.get('playlistId')
                if pid in self.playlist_index_map:
                    v['playlistIndex'] = self.playlist_index_map[pid]
        except Exception:
            pass
        try:
            items = self.video.video_tree.get_children()
            for i, item in enumerate(items):
                if i < len(self.current_videos):
                    self.video.video_tree.item(item, values=self._video_row(self.current_videos[i]))
        except Exception:
            pass

    def highlight_videos_for_playlist(self, playlist_id):
        # Marks only intersection: videos in selected playlist AND present in current search results
        # Updates row values without changing mode; safe against UI restart
        try:
            if not playlist_id:
                return
            items = self.video.video_tree.get_children()
            try:
                pi = self.assign_playlist_index(playlist_id)
            except Exception:
                pi = None
            for i, item in enumerate(items):
                try:
                    v = self.current_videos[i] if i < len(self.current_videos) else None
                    if not v:
                        continue
                    vid = v.get('videoId')
                    cached_hit = bool(vid) and (self.video_playlist_cache.get(vid) == playlist_id)
                    ids_hit = bool(vid) and (vid in self.playlist_video_ids.get(playlist_id, set()))
                    in_results = bool(vid) and (vid in getattr(self, 'video_search_ids', set()))
                    is_hit = (cached_hit or ids_hit) and in_results
                    if is_hit:
                        try:
                            if in_results:
                                self.video_playlist_cache[vid] = playlist_id
                            if pi is not None:
                                v['playlistIndex'] = pi
                        except Exception:
                            pass
                    row = self._video_row(v)
                    if is_hit:
                        try:
                            row = (f"★ {row[0]}",) + row[1:]
                        except Exception:
                            pass
                    self.video.video_tree.item(item, values=row, tags=('search_hit',) if is_hit else ())
                except Exception:
                    pass
            try:
                self._set_pinned_playlist(playlist_id)
            except Exception:
                pass
            try:
                self.status_bar.configure(text="Highlighted videos for playlist")
            except Exception:
                pass
        except Exception:
            pass

    def clear_video_playlist_highlights(self):
        # Removes all transient highlight/star tags from Videos table
        try:
            items = self.video.video_tree.get_children()
            for i, item in enumerate(items):
                try:
                    v = self.current_videos[i] if i < len(self.current_videos) else None
                    if not v:
                        continue
                    row = self._video_row(v)
                    self.video.video_tree.item(item, values=row, tags=())
                except Exception:
                    pass
            try:
                self.status_bar.configure(text="Cleared video highlights")
            except Exception:
                pass
        except Exception:
            pass

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
        # Opens playlist videos in Playlists mode; guarded against wrong column map and missing row
        """Show videos in the selected playlist with pagination."""
        if event:
            selected_item = self.playlist.get_selected_playlist()
        else:
            selected_item = self.playlist.playlist_tree.selection()[0]
        
        if not selected_item:
            return

        playlist_id = selected_item
        try:
            if not self.playlist.playlist_tree.exists(playlist_id):
                info = self.controller.playlist_handler.get_playlist_info(playlist_id)
                self.playlist.update_playlist(info)
        except Exception:
            pass
        playlist_values = self.playlist.playlist_tree.item(selected_item)["values"]
        try:
            self._set_pinned_playlist(playlist_id)
            self._log(f"Opening playlist {playlist_id} page_token={page_token}")
            self._last_open_playlist_id = playlist_id
        except Exception:
            pass
        
        try:
            self._preview_active = False
            try:
                self.playlist.playlist_tree.configure(selectmode='browse')
            except Exception:
                pass
        except Exception:
            pass
        try:
            self.video.update_mode_ui(False)
        except Exception:
            pass
        playlist_title = playlist_values[1]
        channel_title = playlist_values[2]
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
                    self._preview_only_hits = False
                except Exception:
                    pass
                self._render_playlist_videos(total_videos)
                try:
                    if page_token is None:
                        self._show_playlist_listing_popup(playlist_id, self.current_videos)
                except Exception:
                    pass
                return
            try:
                import threading as _t_wd, time as _t
                def _watchdog(pid):
                    try:
                        _t.sleep(12)
                        if self._last_open_playlist_id == pid and not self.current_videos:
                            print(f"[Watchdog] No videos loaded for {pid} within timeout")
                            try:
                                self.after(0, lambda p=pid: self.highlight_videos_for_playlist(p))
                            except Exception:
                                pass
                    except Exception:
                        pass
                _t_wd.Thread(target=_watchdog, args=(playlist_id,), daemon=True).start()
            except Exception:
                pass
            def _worker_open(mr):
                try:
                    import time as _t0
                    t0 = _t0.time()
                    print(f"[WorkerOpen] start pid={playlist_id} token={page_token} mr={mr}")
                except Exception:
                    pass
                try:
                    resp = self.controller.playlist_handler.get_videos(playlist_id, page_token, max_results=mr)
                except Exception as e1:
                    try:
                        print(f"[WorkerOpen] first attempt failed: {e1}")
                    except Exception:
                        pass
                    try:
                        resp = self.controller.playlist_handler.get_videos(playlist_id, page_token, max_results=max(5, int(mr/2)))
                    except Exception as e2:
                        try:
                            self._log(f"Failed to load playlist {playlist_id}: {e2}")
                        except Exception:
                            pass
                        try:
                            print(f"[WorkerOpen] fallback to highlight for pid={playlist_id}")
                            self.after(0, lambda pid=playlist_id: self.highlight_videos_for_playlist(pid))
                        except Exception:
                            pass
                        return
                try:
                    self.current_videos = resp.get("videos", [])
                    self.current_page_token = resp.get("nextPageToken")
                    self.prev_page_token = resp.get("prevPageToken")
                    try:
                        self._cache_playlist_videos(playlist_id, page_token, resp)
                        print(f"[Cache] Stored page for playlist {playlist_id} token={page_token}")
                    except Exception:
                        pass
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
                    try:
                        import time as _t1
                        dt = 0
                        try:
                            dt = _t1.time() - t0
                        except Exception:
                            pass
                        print(f"[WorkerOpen] done pid={playlist_id} count={len(self.current_videos or [])} in {dt:.2f}s")
                    except Exception:
                        pass
                    try:
                        self._preview_only_hits = False
                    except Exception:
                        pass
                    self.after(0, lambda: self._render_playlist_videos(total_videos))
                    try:
                        if page_token is None:
                            self.after(0, lambda: self._show_playlist_listing_popup(playlist_id, self.current_videos))
                    except Exception:
                        pass
                except Exception:
                    pass
            try:
                import threading as _t
                self.status_bar.configure(text="Loading playlist videos...")
                _t.Thread(target=_worker_open, args=(max_results,), daemon=True).start()
                return
            except Exception:
                pass
            resp = self.controller.playlist_handler.get_videos(playlist_id, page_token, max_results=max_results)
            self.current_videos = resp["videos"]
            self.current_page_token = resp.get("nextPageToken")
            self.prev_page_token = resp.get("prevPageToken")

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

            try:
                self._preview_only_hits = False
            except Exception:
                pass
            self._render_playlist_videos(total_videos)
            try:
                if page_token is None:
                    self._show_playlist_listing_popup(playlist_id, self.current_videos)
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
            
            try:
                self.video.set_total_videos(total_videos)
            except Exception:
                self.video.total_label["text"] = f"Total videos: {total_videos}"
            self.video.page_indicator["text"] = f"Page {self.current_page} of {total_pages}"
            
            # Update pagination buttons
            self.video.next_page_btn["state"] = "normal" if self.current_page_token else "disabled"
            self.video.prev_page_btn["state"] = "normal" if self.prev_page_token else "disabled"
            self.video.update_back_button_state(True)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch videos: {e}")

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
                vid = video.get('videoId')
                ttl = str(video.get('title', '')).lower()
                chn = str(video.get('channelTitle', '')).lower()
                if getattr(self, '_preview_only_hits', False):
                    is_hit = (vid in getattr(self, 'video_search_ids', set()))
                else:
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
                    prefix = '★ ' if is_hit else ''
                    print(f" - {prefix}{video.get('title','')} | {video.get('duration','')} | {pub} | {vs}")
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
        if not hasattr(self, 'current_page') or self.prev_page_token is None and self.current_page_token is None:
            self.current_page = 1
        try:
            self.video.set_total_videos(total_videos)
        except Exception:
            self.video.total_label["text"] = f"Total videos: {total_videos}"
        self.video.page_indicator["text"] = f"Page {self.current_page} of {total_pages}"
        try:
            self.video.next_page_btn["state"] = "normal" if self.current_page_token else "disabled"
            self.video.prev_page_btn["state"] = "normal" if self.prev_page_token else "disabled"
            self.video.prev_page_btn.configure(command=lambda: self.show_playlist_videos(page_token=self.prev_page_token))
            self.video.next_page_btn.configure(command=lambda: self.show_playlist_videos(page_token=self.current_page_token))
            self.video.update_back_button_state(True)
        except Exception:
            pass

    def on_video_header_double_click(self, column_name, q=None):
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
        if q is None:
            q = simpledialog.askstring("Filter", f"Filter {column_name} contains:")
            if q is None:
                return
        ql = (q or '').strip().lower()
        items = []
        for v in self.current_videos:
            val = str(v.get(key, ""))
            if ql in val.lower():
                items.append(v)
        self.video.video_tree.delete(*self.video.video_tree.get_children())
        for v in items:
            self.video.video_tree.insert('', 'end', values=self._video_row(v))

    def on_playlist_header_double_click(self, column_name, q=None):
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
        if q is None:
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
            "Views": (lambda v: int(v.get('views') or 0)),
            "Status": (lambda v: (2 if self._video_download_status(v) == 'Downloaded' else (1 if self._video_download_status(v) == 'Not Downloaded' else 0)))
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

    def _sort_playlists(self, name):
        try:
            map_name = {
                'Name': 'Title',
                'Channel': 'Channel',
                'Videos': 'Videos'
            }.get(name, 'Title')
            self.sort_playlists_by(map_name)
        except Exception:
            pass

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

    def build_exe_windows(self):
        try:
            base_src = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            root_dir = os.path.dirname(base_src)
            cand_root = os.path.join(root_dir, "scripts", "build_exe.ps1")
            cand_src = os.path.join(base_src, "scripts", "build_exe.ps1")
            script_path = cand_root if os.path.exists(cand_root) else cand_src
            if not os.path.exists(script_path):
                messagebox.showerror("Error", f"Build script not found: {script_path}")
                return
            project_root = os.path.dirname(os.path.dirname(script_path))
            dist_dir = os.path.join(project_root, "dist")
            top = tk.Toplevel(self)
            top.title("Building EXE")
            frm = ttk.Frame(top)
            frm.pack(fill="both", expand=True, padx=10, pady=10)
            lbl = ttk.Label(frm, text="Building packaged EXE...")
            lbl.pack(anchor="w")
            pb = ttk.Progressbar(frm, mode="indeterminate", length=320)
            pb.pack(fill="x", pady=6)
            pb.start(10)
            txt = tk.Text(frm, height=18, width=80)
            sb = ttk.Scrollbar(frm, orient="vertical", command=txt.yview)
            txt.configure(yscrollcommand=sb.set)
            txt.pack(side="left", fill="both", expand=True)
            sb.pack(side="right", fill="y")
            btns = ttk.Frame(frm)
            btns.pack(fill="x", pady=8)
            run_btn = ttk.Button(btns, text="Run EXE")
            run_btn.pack(side="left")
            open_btn = ttk.Button(btns, text="Open EXE Folder")
            open_btn.pack(side="left", padx=6)
            close_btn = ttk.Button(btns, text="Close", command=top.destroy)
            close_btn.pack(side="right")
            open_btn.configure(state="disabled")
            run_btn.configure(state="disabled")
            exe_path = os.path.join(dist_dir, "YouTubePlaylistExplorer.exe")
            def _open_dist():
                try:
                    if sys.platform == "win32":
                        os.startfile(dist_dir)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", dist_dir])
                    else:
                        subprocess.run(["xdg-open", dist_dir])
                except Exception:
                    pass
            open_btn.configure(command=_open_dist)
            def _run_exe():
                try:
                    if sys.platform == "win32":
                        os.startfile(exe_path)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", exe_path])
                    else:
                        subprocess.run([exe_path])
                except Exception:
                    pass
            run_btn.configure(command=_run_exe)
            def _append(s):
                try:
                    txt.insert("end", s)
                    txt.see("end")
                except Exception:
                    pass
            def _done(ok):
                try:
                    pb.stop()
                    lbl.configure(text=("Build completed" if ok else "Build failed"))
                    if ok:
                        open_btn.configure(state="normal")
                        run_btn.configure(state="normal")
                except Exception:
                    pass
            def _worker():
                try:
                    ok = False
                    # Python-first build
                    try:
                        venv_dir = os.path.join(project_root, ".venv")
                        if not os.path.exists(venv_dir):
                            subprocess.run([sys.executable, "-m", "venv", venv_dir], cwd=project_root, check=True)
                        vpy = os.path.join(venv_dir, "Scripts", "python.exe")
                        if not os.path.exists(vpy):
                            vpy = os.path.join(venv_dir, "bin", "python")
                        def runp(args):
                            p = subprocess.run(args, cwd=project_root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                            self.after(0, lambda s=p.stdout: _append(s))
                            return p.returncode
                        runp([vpy, "-m", "pip", "install", "--upgrade", "pip"])
                        runp([vpy, "-m", "pip", "install", "pyinstaller"])
                        req_path = os.path.join(project_root, "requirements.txt")
                        if os.path.exists(req_path):
                            runp([vpy, "-m", "pip", "install", "-r", req_path])
                        entry = os.path.join(project_root, "src", "main.py")
                        dist = os.path.join(project_root, "dist")
                        work = os.path.join(project_root, "build")
                        os.makedirs(dist, exist_ok=True)
                        os.makedirs(work, exist_ok=True)
                        args = [
                            vpy, "-m", "PyInstaller",
                            "--onefile", "--windowed",
                            "--name", "YouTubePlaylistExplorer",
                            "--distpath", dist, "--workpath", work,
                            "--hidden-import", "googleapiclient.discovery",
                            "--hidden-import", "googleapiclient.errors",
                            "--hidden-import", "isodate",
                            "--hidden-import", "vlc",
                            "--hidden-import", "yt_dlp",
                            entry
                        ]
                        r = subprocess.run(args, cwd=project_root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                        self.after(0, lambda s=r.stdout: _append(s))
                        exe = os.path.join(dist, "YouTubePlaylistExplorer.exe")
                        ok = os.path.exists(exe)
                        if ok:
                            try:
                                run_cmd = os.path.join(dist, "Run-YouTubePlaylistExplorer.cmd")
                                with open(run_cmd, "w", encoding="ascii") as f:
                                    f.write("@echo off\r\n")
                                    f.write("setlocal\r\n")
                                    for env in ("PYTHONHOME","PYTHONPATH","PYTHONUSERBASE","SSL_CERT_FILE","REQUESTS_CA_BUNDLE"):
                                        f.write(f"set {env}=\r\n")
                                    f.write("set PYTHONUTF8=1\r\n")
                                    f.write("start \"\" \"%~dp0YouTubePlaylistExplorer.exe\"\r\n")
                            except Exception:
                                pass
                    except Exception as e:
                        self.after(0, lambda: _append(str(e) + "\n"))
                        ok = False
                    # No PowerShell fallback; Python-only build
                    self.after(0, lambda: _done(ok))
                except Exception:
                    self.after(0, lambda: _done(False))
            try:
                threading.Thread(target=_worker, daemon=True).start()
            except Exception:
                pass
        except Exception:
            pass

    def build_portable_windows(self):
        try:
            base_src = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            root_dir = os.path.dirname(base_src)
            cand_root = os.path.join(root_dir, "scripts", "build_exe.ps1")
            cand_src = os.path.join(base_src, "scripts", "build_exe.ps1")
            script_path = cand_root if os.path.exists(cand_root) else cand_src
            if not os.path.exists(script_path):
                messagebox.showerror("Error", f"Build script not found: {script_path}")
                return
            project_root = os.path.dirname(os.path.dirname(script_path))
            dist_dir = os.path.join(project_root, "dist", "YouTubePlaylistExplorer")
            top = tk.Toplevel(self)
            top.title("Building Portable")
            frm = ttk.Frame(top)
            frm.pack(fill="both", expand=True, padx=10, pady=10)
            lbl = ttk.Label(frm, text="Building portable folder...")
            lbl.pack(anchor="w")
            pb = ttk.Progressbar(frm, mode="indeterminate", length=320)
            pb.pack(fill="x", pady=6)
            pb.start(10)
            txt = tk.Text(frm, height=18, width=80)
            sb = ttk.Scrollbar(frm, orient="vertical", command=txt.yview)
            txt.configure(yscrollcommand=sb.set)
            txt.pack(side="left", fill="both", expand=True)
            sb.pack(side="right", fill="y")
            btns = ttk.Frame(frm)
            btns.pack(fill="x", pady=8)
            run_btn = ttk.Button(btns, text="Run EXE")
            run_btn.pack(side="left")
            open_btn = ttk.Button(btns, text="Open EXE Folder")
            open_btn.pack(side="left", padx=6)
            close_btn = ttk.Button(btns, text="Close", command=top.destroy)
            close_btn.pack(side="right")
            open_btn.configure(state="disabled")
            run_btn.configure(state="disabled")
            exe_path = os.path.join(dist_dir, "YouTubePlaylistExplorer.exe")
            def _open_dist():
                try:
                    if sys.platform == "win32":
                        os.startfile(dist_dir)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", dist_dir])
                    else:
                        subprocess.run(["xdg-open", dist_dir])
                except Exception:
                    pass
            open_btn.configure(command=_open_dist)
            def _append(s):
                try:
                    txt.insert("end", s)
                    txt.see("end")
                except Exception:
                    pass
            def _done(ok):
                try:
                    pb.stop()
                    lbl.configure(text=("Build completed" if ok else "Build failed"))
                    if ok:
                        open_btn.configure(state="normal")
                        run_btn.configure(state="normal")
                except Exception:
                    pass
            def _worker():
                try:
                    ok = False
                    # Python-first build
                    try:
                        venv_dir = os.path.join(project_root, ".venv")
                        if not os.path.exists(venv_dir):
                            subprocess.run([sys.executable, "-m", "venv", venv_dir], cwd=project_root, check=True)
                        vpy = os.path.join(venv_dir, "Scripts", "python.exe")
                        if not os.path.exists(vpy):
                            vpy = os.path.join(venv_dir, "bin", "python")
                        def runp(args):
                            p = subprocess.run(args, cwd=project_root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                            self.after(0, lambda s=p.stdout: _append(s))
                            return p.returncode
                        runp([vpy, "-m", "pip", "install", "--upgrade", "pip"])
                        runp([vpy, "-m", "pip", "install", "pyinstaller"])
                        req_path = os.path.join(project_root, "requirements.txt")
                        if os.path.exists(req_path):
                            runp([vpy, "-m", "pip", "install", "-r", req_path])
                        entry = os.path.join(project_root, "src", "main.py")
                        dist = os.path.join(project_root, "dist")
                        work = os.path.join(project_root, "build")
                        os.makedirs(dist, exist_ok=True)
                        os.makedirs(work, exist_ok=True)
                        args = [
                            vpy, "-m", "PyInstaller",
                            "--onedir", "--windowed",
                            "--name", "YouTubePlaylistExplorer",
                            "--distpath", dist, "--workpath", work,
                            "--hidden-import", "googleapiclient.discovery",
                            "--hidden-import", "googleapiclient.errors",
                            "--hidden-import", "isodate",
                            "--hidden-import", "vlc",
                            "--hidden-import", "yt_dlp",
                            entry
                        ]
                        r = subprocess.run(args, cwd=project_root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                        self.after(0, lambda s=r.stdout: _append(s))
                        target_dir = os.path.join(dist, "YouTubePlaylistExplorer")
                        ok = os.path.isdir(target_dir)
                        exe_path2 = os.path.join(target_dir, "YouTubePlaylistExplorer.exe")
                        if ok:
                            try:
                                run_cmd = os.path.join(target_dir, "Run-App.cmd")
                                with open(run_cmd, "w", encoding="ascii") as f:
                                    f.write("@echo off\r\n")
                                    f.write("setlocal\r\n")
                                    for env in ("PYTHONHOME","PYTHONPATH","PYTHONUSERBASE","SSL_CERT_FILE","REQUESTS_CA_BUNDLE"):
                                        f.write(f"set {env}=\r\n")
                                    f.write("set PYTHONUTF8=1\r\n")
                                    f.write("start \"\" \"%~dp0YouTubePlaylistExplorer.exe\"\r\n")
                            except Exception:
                                pass
                    except Exception as e:
                        self.after(0, lambda: _append(str(e) + "\n"))
                        ok = False
                    # No PowerShell fallback; Python-only build
                    self.after(0, lambda: _done(ok))
                except Exception:
                    self.after(0, lambda: _done(False))
            try:
                threading.Thread(target=_worker, daemon=True).start()
            except Exception:
                pass
        except Exception:
            pass

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
        selected_playlist = self.playlist.get_selected_playlist()
        if not selected_playlist:
            messagebox.showerror("Error", "Please select a playlist first.")
            return
        try:
            if not self.current_playlist_info:
                try:
                    vals = self.playlist.playlist_tree.item(selected_playlist).get('values', [])
                except Exception:
                    vals = []
                ttl = ''
                chn = ''
                try:
                    ttl = vals[1] if len(vals) > 1 else ''
                except Exception:
                    ttl = ''
                try:
                    chn = vals[2] if len(vals) > 2 else ''
                except Exception:
                    chn = ''
                try:
                    self.current_playlist_info = {"title": ttl or str(selected_playlist), "channel": chn, "id": selected_playlist}
                except Exception:
                    self.current_playlist_info = {"title": str(selected_playlist), "channel": '', "id": selected_playlist}
        except Exception:
            pass
        if not self.current_videos:
            self.show_playlist_videos()
            if not self.current_videos:
                messagebox.showerror("Error", "No videos found in the selected playlist.")
                return
        try:
            folder = os.path.join(self.controller.default_folder, f"Playlist - {self.current_playlist_info['title']}")
            os.makedirs(folder, exist_ok=True)
            self._start_download_for_videos(self.current_videos, folder)
        except Exception:
            pass

    # ... (to be continued with more methods)
    def print_playlist_videos_to_terminal(self, playlist_id):
        try:
            vals = self.playlist.playlist_tree.item(playlist_id).get('values', [])
            ttl = (vals[1] if isinstance(vals, (list, tuple)) and len(vals) > 1 else '') or ''
        except Exception:
            ttl = ''
        def _printer(resp):
            try:
                vids = list(resp.get('videos', []) or [])
                print(f"[Playlist] {ttl or playlist_id} ({playlist_id})")
                for v in vids:
                    try:
                        pub = self._fmt_date(v.get('published',''))
                        vs = v.get('views','')
                        print(f" - {v.get('title','')} | {v.get('duration','')} | {pub} | {vs}")
                    except Exception:
                        pass
            except Exception:
                pass
        def _worker():
            try:
                cached = self._get_cached_playlist_page(playlist_id, None)
            except Exception:
                cached = None
            if cached is not None:
                _printer(cached)
                return
            try:
                mr = int(self.video.page_size_var.get())
            except Exception:
                mr = 10
            def _fetch(mr2):
                return self.controller.playlist_handler.get_videos(playlist_id, None, max_results=mr2)
            try:
                resp = _fetch(mr)
                try:
                    self._cache_playlist_videos(playlist_id, None, resp)
                except Exception:
                    pass
                _printer(resp)
            except Exception as e:
                try:
                    import ssl
                    is_ssl = isinstance(e, ssl.SSLError) or ('SSL' in str(e))
                except Exception:
                    is_ssl = 'SSL' in str(e)
                try:
                    import socket
                    is_timeout = isinstance(e, socket.timeout) or ('timed out' in str(e).lower())
                except Exception:
                    is_timeout = 'timed out' in str(e).lower()
                if is_ssl or is_timeout:
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
                        try:
                            self._cache_playlist_videos(playlist_id, None, resp)
                        except Exception:
                            pass
                        _printer(resp)
                    except Exception:
                        try:
                            self.after(0, lambda: self.status_bar.configure(text="Network issue; highlighted matches instead"))
                        except Exception:
                            pass
                        try:
                            self.after(0, lambda: self.highlight_videos_for_playlist(playlist_id))
                        except Exception:
                            pass
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
            import threading as _t
            _t.Thread(target=_worker, daemon=True).start()
        except Exception:
            pass

    def populate_videos_table_preview(self, playlist_id):
        # Renders selected playlist videos into Videos table without changing mode
        # Sets _preview_only_hits so stars/tags apply only to search result intersection
        try:
            vals = self.playlist.playlist_tree.item(playlist_id).get('values', [])
        except Exception:
            vals = []
        try:
            ttl = vals[1] if len(vals) > 1 else ''
        except Exception:
            ttl = ''
        try:
            try:
                total_videos = int(vals[3])
            except Exception:
                try:
                    total_videos = int(self.controller.playlist_handler.get_details(playlist_id))
                except Exception:
                    total_videos = 0
            try:
                cached = self._get_cached_playlist_page(playlist_id, None)
            except Exception:
                cached = None
            if cached is not None:
                try:
                    self.current_videos = list(cached.get('videos', []) or [])
                    self.prev_page_token = cached.get('prevPageToken')
                    self.current_page_token = cached.get('nextPageToken')
                except Exception:
                    pass
            else:
                try:
                    mr = int(self.video.page_size_var.get())
                except Exception:
                    mr = 10
                try:
                    resp = self.controller.playlist_handler.get_videos(playlist_id, None, max_results=mr)
                except Exception:
                    try:
                        resp = self.controller.playlist_handler.get_videos(playlist_id, None, max_results=max(5, int(mr//2)))
                    except Exception:
                        resp = {'videos': [], 'nextPageToken': None, 'prevPageToken': None}
                try:
                    self._cache_playlist_videos(playlist_id, None, resp)
                except Exception:
                    pass
                try:
                    self.current_videos = list(resp.get('videos', []) or [])
                    self.prev_page_token = resp.get('prevPageToken')
                    self.current_page_token = resp.get('nextPageToken')
                except Exception:
                    pass
            try:
                pi = None
                try:
                    pi = self.assign_playlist_index(playlist_id)
                except Exception:
                    pi = None
                for v in list(self.current_videos or []):
                    try:
                        vid = v.get('videoId')
                        if vid and (vid in getattr(self, 'video_search_ids', set())):
                            self.video_playlist_cache[vid] = playlist_id
                        if pi is not None:
                            v['playlistIndex'] = pi
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                self._preview_only_hits = True
                self._preview_active = True
                try:
                    self.playlist.playlist_tree.configure(selectmode='none')
                except Exception:
                    pass
            except Exception:
                pass
            try:
                self._render_playlist_videos(total_videos)
            except Exception:
                pass
            try:
                self.video.update_back_button_state(True)
                self.status_bar.configure(text=f"Preview: {ttl or playlist_id}")
            except Exception:
                pass
        except Exception:
            pass

    def _show_playlist_listing_popup(self, playlist_id, videos):
        # Popup window showing playlist number and each video title
        # Applies star tag for intersection with current search results
        try:
            import tkinter as _tk
            from tkinter import ttk as _ttk
            win = _tk.Toplevel(self)
            try:
                vals = self.playlist.playlist_tree.item(playlist_id).get('values', [])
            except Exception:
                vals = []
            ttl = ''
            try:
                ttl = vals[1] if len(vals) > 1 else ''
            except Exception:
                ttl = ''
            win.title(f"Playlist Listing: {ttl or playlist_id}")
            frm = _ttk.Frame(win)
            frm.pack(fill="both", expand=True)
            tv = _ttk.Treeview(frm, columns=("Playlist","Title"), show="headings", selectmode="none")
            tv.heading("Playlist", text="Playlist")
            tv.heading("Title", text="Title")
            tv.column("Playlist", width=80, anchor="center")
            tv.column("Title", width=520, anchor="w")
            try:
                tv.tag_configure('search_hit', background='#fff6bf')
            except Exception:
                pass
            scr = _ttk.Scrollbar(frm, orient="vertical", command=tv.yview)
            tv.configure(yscrollcommand=scr.set)
            tv.pack(side="left", fill="both", expand=True)
            scr.pack(side="right", fill="y")
            try:
                pi = self.assign_playlist_index(playlist_id)
            except Exception:
                pi = ''
            try:
                for v in list(videos or []):
                    try:
                        vid = v.get('videoId')
                    except Exception:
                        vid = None
                    hit = bool(vid) and (vid in getattr(self, 'video_search_ids', set()))
                    title = v.get('title','')
                    if hit:
                        try:
                            title = f"★ {title}"
                        except Exception:
                            pass
                    tv.insert('', 'end', values=(pi, title), tags=('search_hit',) if hit else ())
            except Exception:
                pass
            try:
                win.geometry("700x420")
            except Exception:
                pass
        except Exception:
            pass

    def download_selected_videos(self):
        try:
            sel = self.video.video_tree.selection()
            if not sel:
                messagebox.showerror("Error", "Please select one or more videos.")
                return
            videos = []
            for iid in sel:
                try:
                    idx = self.video.video_tree.index(iid)
                except Exception:
                    continue
                if 0 <= idx < len(self.current_videos):
                    videos.append(self.current_videos[idx])
            if not videos:
                messagebox.showerror("Error", "Selected rows not found.")
                return
            self._start_download_for_videos(videos, None)
        except Exception:
            pass

    def download_single_video(self):
        try:
            sel = self.video.video_tree.selection()
            if not sel:
                messagebox.showerror("Error", "Please select a video.")
                return
            idx = self.video.video_tree.index(sel[0])
            if idx < 0 or idx >= len(self.current_videos):
                return
            v = self.current_videos[idx]
            self._start_download_for_videos([v], None)
        except Exception:
            pass

    def download_selected_playlists(self):
        try:
            sel = list(self.playlist.playlist_tree.selection())
        except Exception:
            sel = []
        if not sel:
            messagebox.showerror("Error", "Please select one or more playlists.")
            return
        all_videos = []
        try:
            try:
                mr = int(self.video.page_size_var.get())
            except Exception:
                mr = 10
            for pid in sel:
                vids = []
                try:
                    cached = self._get_cached_playlist_page(pid, None)
                except Exception:
                    cached = None
                if cached is not None:
                    try:
                        vids = list(cached.get('videos', []) or [])
                    except Exception:
                        vids = []
                else:
                    try:
                        resp = self.controller.playlist_handler.get_videos(pid, None, max_results=mr)
                        try:
                            self._cache_playlist_videos(pid, None, resp)
                        except Exception:
                            pass
                        vids = list(resp.get('videos', []) or [])
                    except Exception:
                        vids = []
                for v in vids:
                    try:
                        if not v.get('playlistId'):
                            v['playlistId'] = pid
                    except Exception:
                        pass
                all_videos.extend(vids)
        except Exception:
            pass
        if not all_videos:
            messagebox.showerror("Error", "No videos found in selected playlists.")
            return
        self._start_download_for_videos(all_videos, None)

    def _start_download_for_videos(self, videos, folder=None):
        try:
            try:
                self._enrich_video_playlist_info(videos)
            except Exception:
                pass
            try:
                from .download_options_dialog import DownloadOptionsDialog
            except Exception:
                from src.pages.main.download_options_dialog import DownloadOptionsDialog
            dlg = DownloadOptionsDialog(self)
            if not getattr(dlg, 'result', None):
                return
            try:
                self._download_opts = dict(dlg.result or {})
            except Exception:
                self._download_opts = dlg.result
            try:
                from .download_manager import DownloadManager
            except Exception:
                from src.pages.main.download_manager import DownloadManager
            DownloadManager(self, list(videos or []), folder, dlg.result).start()
        except Exception:
            pass

    def open_explore_downloaded_popup(self):
        try:
            try:
                from .download_manager import DownloadManager
            except Exception:
                from src.pages.main.download_manager import DownloadManager
            # No direct instance access; this triggers only within an active download window
            # Provided here for context-menu binding; it will be a no-op if not available
        except Exception:
            pass

    def _enrich_video_playlist_info(self, videos):
        try:
            for v in list(videos or []):
                try:
                    vid = v.get('videoId')
                    pid = v.get('playlistId')
                    if not pid:
                        try:
                            pid = self.video_playlist_cache.get(vid)
                        except Exception:
                            pid = None
                    if not pid:
                        try:
                            for k, ids in (self.playlist_video_ids or {}).items():
                                if vid in ids:
                                    pid = k
                                    break
                        except Exception:
                            pid = None
                    if not pid:
                        try:
                            existing = list(self.playlist.playlist_tree.get_children())
                        except Exception:
                            existing = []
                        for plid in existing:
                            try:
                                if self.controller.playlist_handler.playlist_contains_video(plid, vid):
                                    pid = plid
                                    break
                            except Exception:
                                continue
                    if pid:
                        v['playlistId'] = pid
                        try:
                            self.video_playlist_cache[vid] = pid
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

    def restart_app(self):
        try:
            import subprocess, os, sys
            bat = r"d:\Py_2025\11-2025\youtube_downloaderV2_CURSOR_OK1_dev_multi_OK07-04-25\run_app.bat"
            if os.name == "nt":
                try:
                    ps = "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'run_app\\.bat' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
                    subprocess.run(["powershell", "-NoProfile", "-Command", ps], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass
            if os.path.exists(bat):
                try:
                    p = subprocess.Popen(["cmd", "/c", bat], creationflags=getattr(subprocess, 'CREATE_NEW_CONSOLE', 0))
                    try:
                        self._bat_process = p
                    except Exception:
                        pass
                except Exception:
                    try:
                        subprocess.Popen(["cmd", "/c", "start", "", bat])
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            self.controller.root.quit()
        except Exception:
            pass
    def _resolve_playlist_for_video(self, v):
        try:
            vid = v.get('videoId')
            pid = v.get('playlistId') or self.video_playlist_cache.get(vid)
            if pid:
                return pid
            try:
                for k, ids in (self.playlist_video_ids or {}).items():
                    if vid in ids:
                        return k
            except Exception:
                pass
            try:
                existing = list(self.playlist.playlist_tree.get_children())
            except Exception:
                existing = []
            for plid in existing:
                try:
                    if self.controller.playlist_handler.playlist_contains_video(plid, vid):
                        try:
                            self.video_playlist_cache[vid] = plid
                        except Exception:
                            pass
                        return plid
                except Exception:
                    continue
            try:
                ch = v.get('channelId')
                if ch:
                    pls = self.controller.playlist_handler.get_channel_playlists(ch, max_results=20)
                    for info in pls:
                        plid = info.get('playlistId') or info.get('id') or info.get('playlist_id')
                        if not plid:
                            continue
                        try:
                            if self.controller.playlist_handler.playlist_contains_video(plid, vid):
                                try:
                                    self.playlist.update_playlist(info)
                                except Exception:
                                    pass
                                try:
                                    self.video_playlist_cache[vid] = plid
                                except Exception:
                                    pass
                                return plid
                        except Exception:
                            continue
            except Exception:
                pass
            return None
        except Exception:
            return None
