import tkinter as tk
from tkinter import messagebox, filedialog
import webbrowser
import os
import csv
import sys
import subprocess
import threading  # Add this for download threading
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
try:
    from src.services.video_playlist_scanner import VideoPlaylistScanner
    from src.services.media_index import MediaIndex
    from src.data.json_store import JsonStore
    from src.services.results_mapper import build_index_map as _rm_build_index_map, rebuild_video_playlist_cache as _rm_rebuild_cache, link_media_index as _rm_link_index
    from src.services.playlist_search import search_enriched_playlists as _ps_search
    from src.services.video_search import search_videos as _vs_search
    from src.services.playlist_matcher import PlaylistMatcher
    from src.services.download_path_manager import DownloadPathManager
    from src.pages.main.videos_mode_handler import VideosModeHandler
except ModuleNotFoundError:
    from services.video_playlist_scanner import VideoPlaylistScanner
    from services.media_index import MediaIndex
    from data.json_store import JsonStore
    from services.results_mapper import build_index_map as _rm_build_index_map, rebuild_video_playlist_cache as _rm_rebuild_cache, link_media_index as _rm_link_index
    from services.playlist_search import search_enriched_playlists as _ps_search
    from services.video_search import search_videos as _vs_search
    from services.playlist_matcher import PlaylistMatcher
    from pages.main.videos_mode_handler import VideosModeHandler

class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_videos = []
        self.current_playlist_info = {}
        self.current_page_token = None
        self.playlist_matcher = PlaylistMatcher()
        self.videos_mode_handler = VideosModeHandler(self)
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

    def _show_search_results_dialog(self, total_count, query):
        try:
            import tkinter as _tk
            from tkinter import ttk as _ttk
            win = _tk.Toplevel(self)
            win.title("Search Results")
            try:
                win.geometry("400x150")
            except Exception:
                pass
            
            # YouTube API often returns estimated counts (e.g. 1,000,000) for large result sets.
            # We clarify this to the user to avoid confusion when actual fetch count is lower.
            if total_count >= 1000:
                msg = f"Found approx. {total_count:,} videos for keyword '{query}'\n(API Estimate)"
            else:
                msg = f"Found {total_count} videos for keyword '{query}'"
            
            _ttk.Label(win, text=msg, font=("Arial", 10, "bold")).pack(pady=20, padx=20)
            
            btn_frame = _ttk.Frame(win)
            btn_frame.pack(fill="x", pady=10)
            
            _ttk.Button(btn_frame, text="Fetch More & Export (Max 2000)", command=self._export_current_videos_csv).pack(side="left", expand=True, padx=5)
            _ttk.Button(btn_frame, text="OK", command=win.destroy).pack(side="left", expand=True, padx=5)
        except Exception:
            pass

    def _export_current_videos_csv(self):
        try:
            is_search = (self.search_mode == 'videos')
            total = int(getattr(self, 'video_total_results', 0) or 0)
            current_count = len(self.current_videos)
            
            videos_to_export = list(self.current_videos)
            
            # If we have a huge total (API estimate) but only few loaded, try to fetch more
            if is_search and total > current_count:
                # Automatically fetch more results if available, up to a limit
                max_fetch = 2000
                fetched = current_count
                next_token = getattr(self, 'video_next_page_token', None)
                query = getattr(self, 'video_search_query', '')
                
                prog_win = tk.Toplevel(self)
                prog_win.title("Fetching Videos...")
                try:
                    prog_win.geometry("300x100")
                    x = self.winfo_rootx() + self.winfo_width()//2 - 150
                    y = self.winfo_rooty() + self.winfo_height()//2 - 50
                    prog_win.geometry(f"+{x}+{y}")
                except Exception:
                    pass
                
                lbl = ttk.Label(prog_win, text="Fetching more videos from API...")
                lbl.pack(pady=20)
                prog = ttk.Progressbar(prog_win, mode='indeterminate')
                prog.pack(fill='x', padx=20)
                prog.start()
                
                try:
                    while next_token and fetched < max_fetch:
                        lbl.configure(text=f"Fetched {fetched} / {min(total, max_fetch)}...")
                        prog_win.update()
                        
                        try:
                            resp = self.controller.playlist_handler.search_videos(query, max_results=50, page_token=next_token)
                            new_vids = resp.get('videos', [])
                            if not new_vids:
                                break
                            videos_to_export.extend(new_vids)
                            fetched += len(new_vids)
                            next_token = resp.get('nextPageToken')
                        except Exception:
                            break
                finally:
                    prog_win.destroy()
            
            if not videos_to_export:
                messagebox.showerror("Error", "No videos to export.")
                return
            
            path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
                title="Export Search Results"
            )
            if not path:
                return
            
            try:
                with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Video ID", "Title", "Channel", "Duration", "Published", "Views", "Playlist ID"])
                    for v in videos_to_export:
                        try:
                            writer.writerow([
                                v.get('videoId', ''),
                                v.get('title', ''),
                                v.get('channelTitle', ''),
                                v.get('duration', ''),
                                v.get('published', ''),
                                v.get('views', ''),
                                v.get('playlistId', '')
                            ])
                        except Exception:
                            pass
                msg = f"Exported {len(videos_to_export)} videos to {os.path.basename(path)}"
                if len(videos_to_export) < total and len(videos_to_export) < 2000:
                     msg += "\n\nNote: The 'Total' count (e.g. 1M) is an API estimate.\nThe YouTube API limits accessible results to a few hundred."
                messagebox.showinfo("Success", msg)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to write file: {e}")
        except Exception:
            pass

    def check_api_status_on_startup(self):
        def _check():
            try:
                self.controller.ensure_playlist_handler()
                if self.controller.playlist_handler:
                    try:
                        # Basic validation (costs 1 unit)
                        self.controller.playlist_handler.validate_key()
                        self._safe_ui(lambda: self.search.update_search_button_color('valid'))
                    except Exception as e:
                        if 'quota' in str(e).lower():
                             self._safe_ui(lambda: self.search.update_search_button_color('warning'))
                        else:
                             self._safe_ui(lambda: self.search.update_search_button_color('invalid'))
                else:
                    self._safe_ui(lambda: self.search.update_search_button_color('invalid'))
            except Exception:
                self._safe_ui(lambda: self.search.update_search_button_color('invalid'))
        
        import threading
        threading.Thread(target=_check, daemon=True).start()

    def _initialize_components(self):
        """Initialize and pack GUI components."""
        self._create_sections()
        self._pack_sections()
        try:
            self.check_api_status_on_startup()
        except Exception:
            pass
        try:
            lm = (ConfigManager.load_last_mode() or '').strip().lower()
            if lm == 'videos':
                try:
                    self.search.mode_var.set('Videos')
                except Exception:
                    pass
                self.search_mode = 'videos'
                self._load_last_search('Videos')
                self._update_results_ids()
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
        self._preview_only_hits = False
        self._last_open_playlist_id = None
        self._pl_hits_cache = {}
        self.video_results_ids = set()
        try:
            self.media_index = MediaIndex()
        except Exception:
            self.media_index = None
        try:
            self._load_media_index_snapshot()
        except Exception:
            pass
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
            plid = None
            if self.media_index:
                plid = self.media_index.get_video_playlist(vid)
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

    def on_pagination_toggle(self, enabled):
        try:
            # Show/Hide pagination bar
            self.video._panel.pagination.set_visible(enabled)
            
            # Refresh current view
            if self.search_mode == 'videos':
                # If pagination is OFF, reset to page 1 but show ALL
                if not enabled:
                    self.video_search_page_index = 1
                self.videos_mode_handler.show_videos_search_page(direction='reset')
        except Exception:
            pass

    def _save_media_index_snapshot(self):
        try:
            if not self.media_index:
                return
            d = self.media_index.to_dict()
            JsonStore().save_media_index_snapshot(d.get('videos', {}), d.get('playlists', {}))
        except Exception:
            pass

    def _load_media_index_snapshot(self):
        try:
            snap = JsonStore().load_media_index_snapshot() or {}
            if not self.media_index:
                self.media_index = MediaIndex()
            self.media_index.load_from_dict(snap)
        except Exception:
            pass

    def _video_target_folder(self, v):
        try:
            # Construct comprehensive video info for the manager
            video_info = v.copy()
            
            # Enrich with playlist title from tree if possible
            pid = v.get('playlistId')
            if not pid and self.media_index:
                pid = self.media_index.get_video_playlist(v.get('videoId'))
            if not pid:
                try:
                    pid = self._resolve_playlist_for_video(v)
                except Exception:
                    pass
            
            if pid:
                video_info['playlistId'] = pid
                if self.playlist.playlist_exists(pid):
                    vals = self.playlist.get_playlist_values(pid) or []
                    if len(vals) > 1:
                        video_info['playlist_title'] = vals[1]
            
            # Prepare download options
            opts = getattr(self, '_download_opts', {})
            # Add search query to opts for fallback naming
            opts['query'] = getattr(self, 'video_search_query', '') or 'Misc'
            
            return DownloadPathManager.get_video_target_folder(video_info, opts)
        except Exception:
            return DownloadPathManager.get_default_download_folder()

    def _find_downloaded_file(self, folder, title, video_id=None):
        try:
            name = str(title or '').strip()
            if not folder or not name:
                return None
            exts = ('.mp4', '.webm', '.mkv')
            candidates = []
            if not os.path.exists(folder):
                return None
                
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
            if self.playlist.playlist_exists(playlist_id):
                vals = self.playlist.get_playlist_values(playlist_id) or []
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
            if self.media_index:
                self.media_index.link_video_to_playlist(playlist_id, vid)
            pi = self.assign_playlist_index(playlist_id)
            self.current_videos[idx]['playlistIndex'] = pi
            items = self.video.video_tree.get_children()
            if idx < len(items):
                row = self._video_row(self.current_videos[idx])
                try:
                    itm = items[idx]
                    meta = self.video.video_tree.item(itm)
                    tags = tuple(meta.get('tags') or ())
                    if 'search_hit' in tags:
                        try:
                            row = (f"★ {row[0]}",) + row[1:]
                        except Exception:
                            pass
                        self.video.video_tree.item(itm, values=row, tags=('search_hit',))
                        return
                except Exception:
                    pass
                self.video.video_tree.item(items[idx], values=row)
        except Exception:
            pass

    def _bring_playlist_to_top(self, playlist_id):
        try:
            self.playlist.bring_to_top(playlist_id)
        except Exception:
            pass

    def _set_pinned_playlist(self, playlist_id):
        try:
            if self.pinned_playlist_id and self.playlist.playlist_exists(self.pinned_playlist_id):
                vals = list(self.playlist.get_playlist_values(self.pinned_playlist_id) or [])
                if len(vals) >= 5 and isinstance(vals[4], str):
                    vals[4] = vals[4].replace(' • Pinned', '')
                    self.playlist.update_playlist_item(self.pinned_playlist_id, tuple(vals))
            self.pinned_playlist_id = playlist_id
            if self.playlist.playlist_exists(playlist_id):
                vals = list(self.playlist.get_playlist_values(playlist_id) or [])
                if len(vals) >= 5 and isinstance(vals[4], str) and ' • Pinned' not in vals[4]:
                    vals[4] = f"{vals[4]} • Pinned"
                    self.playlist.update_playlist_item(playlist_id, tuple(vals))
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
                if self.media_index:
                    self.media_index.bulk_link_playlist_videos(playlist_id, list(ids))
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
            self.playlist.clear_playlists()
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
        try:
            self.media_index = MediaIndex()
        except Exception:
            self.media_index = None

    def set_search_mode(self, mode_display):
        mode = (mode_display or '').strip().lower()
        if mode not in ('playlists', 'videos'):
            mode = 'playlists'
        if mode != self.search_mode:
            self.search_mode = mode
            self.clear_panels()
            try:
                if mode == 'videos':
                    try:
                        self.status_bar.configure(text="Mode: Videos — reloading last search results")
                    except Exception:
                        pass
                    try:
                        self.video._panel.pagination.set_visible(False)
                    except Exception:
                        pass
                    try:
                        self._preview_active = False
                    except Exception:
                        pass
                    try:
                        self.playlist.playlist_tree.configure(selectmode='browse')
                    except Exception:
                        pass
                else:
                    try:
                        self.status_bar.configure(text="Mode: Playlists — ready")
                    except Exception:
                        pass
            except Exception:
                pass
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
        import threading
        mode = (mode_display or '').strip().lower()
        if mode not in ('playlists', 'videos'):
            mode = 'playlists'

        try:
            self._last_load_token = int(getattr(self, '_last_load_token', 0)) + 1
        except Exception:
            self._last_load_token = 1
        token = self._last_load_token

        try:
            self._last_load_in_progress = True
        except Exception:
            pass

        def _load_thread():
            try:
                if getattr(self, '_last_load_token', 0) != token:
                    return
                
                self._safe_ui(lambda: self.status_bar.configure(text=f"Loading {mode} history..."))

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
                        self.after(0, lambda: self.search.search_entry.delete(0, 'end'))
                        if q:
                            self.after(0, lambda qq=q: self.search.search_entry.insert(0, qq))
                    except Exception:
                        pass
                    try:
                        # Clear and insert in chunks to keep UI responsive
                        self.after(0, lambda: self.playlist.clear_playlists())
                        def _ins_pl_chunk_playlists(s=0):
                            try:
                                ch = 30
                                e = min(s + ch, len(data_list))
                                for i in range(s, e):
                                    if getattr(self, '_last_load_token', 0) != token:
                                        return
                                    self.playlist.update_playlist(data_list[i])
                                if e < len(data_list):
                                    if getattr(self, '_last_load_token', 0) != token:
                                        return
                                    self.after(10, lambda st=e: _ins_pl_chunk_playlists(st))
                                else:
                                    self._safe_ui(lambda: self.status_bar.configure(text=f"Mode: Playlists — history loaded ({len(data_list)} items)"))
                            except Exception:
                                pass
                        self.after(0, _ins_pl_chunk_playlists)
                    except Exception:
                        pass
                    try:
                        self.after(0, lambda: self.video.update_back_button_state(False))
                    except Exception:
                        pass
                else:
                    try:
                        # Load data in background thread
                        data = self.videos_mode_handler.load_last_search_data()
                        
                        if getattr(self, '_last_load_token', 0) != token:
                            return
                            
                        # Schedule UI update on main thread
                        self._safe_ui(lambda: self.status_bar.configure(text="Rendering video history..."))
                        self.after(0, lambda: self.videos_mode_handler.populate_from_last_search(data))
                        
                        # Status update will be visible after rendering starts
                        self._safe_ui(lambda: self.status_bar.configure(text="Mode: Videos — history loaded"))
                    except Exception:
                        pass
            except Exception:
                pass
            finally:
                try:
                    if getattr(self, '_last_load_token', 0) == token:
                        self.after(0, lambda: setattr(self, '_last_load_in_progress', False))
                except Exception:
                    pass

        try:
            threading.Thread(target=_load_thread, daemon=True).start()
        except Exception:
            # Fallback to synchronous if threading fails
            try:
                _load_thread()
            except Exception:
                pass

    def execute_search(self, query, mode_display):
        query = (query or '').strip()
        if not query:
            messagebox.showerror("Error", "Please enter a keyword.")
            return
            
        try:
            if getattr(self.search, 'exact_match_var', None) and self.search.exact_match_var.get():
                if not (query.startswith('"') and query.endswith('"')):
                    query = f'"{query}"'
        except Exception:
            pass
            
        try:
            self.controller.ensure_playlist_handler()
        except Exception:
            pass
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
                enriched = _ps_search(self.controller.playlist_handler, query)
                self.playlist.playlist_tree.delete(*self.playlist.playlist_tree.get_children())
                def _ins_chunk(s):
                    try:
                        ch = 30
                        e = min(s + ch, len(enriched))
                        for i in range(s, e):
                            self.playlist.update_playlist(enriched[i])
                        if e < len(enriched):
                            self.after(0, lambda st=e: _ins_chunk(st))
                    except Exception:
                        pass
                _ins_chunk(0)
                ConfigManager.save_json(ConfigManager.get_last_search_path('playlists'), {
                    'query': query,
                    'playlists': enriched
                })
                self.video.update_back_button_state(False)
            except Exception as e:
                try:
                    self.status_bar.configure(text="API quota/error — loading last saved playlists")
                except Exception:
                    pass
                try:
                    path = ConfigManager.get_last_search_path('playlists')
                    raw = ConfigManager.load_json(path)
                except Exception:
                    raw = None
                enriched = []
                q_cached = ''
                try:
                    if isinstance(raw, dict):
                        enriched = raw.get('playlists', [])
                        q_cached = raw.get('query', '')
                    else:
                        enriched = raw or []
                except Exception:
                    enriched = []
                try:
                    self.playlist.playlist_tree.delete(*self.playlist.playlist_tree.get_children())
                    def _ins_chunk_cached(s):
                        try:
                            ch = 30
                            e = min(s + ch, len(enriched))
                            for i in range(s, e):
                                self.playlist.update_playlist(enriched[i])
                            if e < len(enriched):
                                self.after(0, lambda st=e: _ins_chunk_cached(st))
                        except Exception:
                            pass
                    _ins_chunk_cached(0)
                    self.video.update_back_button_state(False)
                except Exception:
                    pass
        else:
            self.video_search_query = query
            try:
                self.status_bar.configure(text="Searching videos...")
            except Exception:
                pass
            try:
                self.video._panel.pagination.set_visible(False)
            except Exception:
                pass
            
            try:
                # Use configured limit (e.g. 40, 100) from Settings
                target_limit = ConfigManager.get_max_search_results()
            except Exception:
                target_limit = 40

            all_videos = []
            next_token = None
            total_found = 0
            
            try:
                # Fetch first page
                # We use 50 (API max) to be efficient, even if limit is 40
                resp = _vs_search(self.controller.playlist_handler, query, max_results=50)
                
                vids = resp.get('videos', [])
                all_videos.extend(vids)
                next_token = resp.get('nextPageToken')
                total_found = resp.get('totalResults')
                
                # Fetch more if needed to reach target_limit
                while len(all_videos) < target_limit and next_token:
                    # Safety break
                    if len(all_videos) >= 2000:
                        break
                        
                    try:
                        resp = _vs_search(self.controller.playlist_handler, query, max_results=50, page_token=next_token)
                        new_vids = resp.get('videos', [])
                        if not new_vids:
                            break
                        all_videos.extend(new_vids)
                        next_token = resp.get('nextPageToken')
                    except Exception:
                        break
                        
            except Exception as e:
                try:
                    self.status_bar.configure(text="API quota/error — loading last saved results")
                except Exception:
                    pass
                try:
                    path = ConfigManager.get_last_search_path('videos')
                    data = ConfigManager.load_json(path) or {}
                    videos = data.get('videos', [])
                    self.current_videos = videos
                    self.video_next_page_token = data.get('nextPageToken')
                    self.video_prev_page_token = data.get('prevPageToken')
                    self.video_total_results = data.get('totalResults')
                    self.video_search_ids = set([v.get('videoId') for v in videos if v.get('videoId')])
                    self.video_search_page_index = 1
                    self.video.page_indicator["text"] = f"Results page {self.video_search_page_index}"
                    self.video.video_tree.delete(*self.video.video_tree.get_children())
                    def _ins_chunk_vs(s):
                        try:
                            ch = 50
                            e = min(s + ch, len(videos))
                            vs = getattr(self, 'video_search_ids', set())
                            for i in range(s, e):
                                v = videos[i]
                                try:
                                    vid = v.get('videoId')
                                    tags = ('search_hit',) if vid in vs else ()
                                    self.video.video_tree.insert('', 'end', values=self._video_row(v), tags=tags)
                                except Exception:
                                    self.video.video_tree.insert('', 'end', values=self._video_row(v))
                            if e < len(videos):
                                self.after(0, lambda st=e: _ins_chunk_vs(st))
                        except Exception:
                            pass
                    _ins_chunk_vs(0)
                    return
                except Exception:
                    messagebox.showerror("Error", f"Failed to fetch videos: {e}")
                    return

            # Trim to exact limit
            all_videos = all_videos[:target_limit]
            
            self.current_videos = all_videos
            self.video_next_page_token = next_token
            self.video_prev_page_token = None # Search always starts at beginning
            self.video_total_results = total_found
            
            # Update total count to reflect REAL fetched count if less than API total
            # This is less confusing for the user
            if len(all_videos) > 0 and len(all_videos) < (int(total_found or 0)):
                 # Keep the API total in a separate var if needed, but for UI use loaded count?
                 # No, user wants to see "Found 781" if 781 exists.
                 # But we only loaded 40.
                 pass

            try:
                # Show popup with total count as requested
                total_val = int(self.video_total_results or 0)
                # Show custom dialog to allow CSV export
                self.after(100, lambda t=total_val, q=query: self._show_search_results_dialog(t, q))
            except Exception:
                pass
            
            # Initial render of first page (local)
            try:
                self.video_search_page_index = 1
                self.videos_mode_handler.show_videos_search_page(direction='reset')
            except Exception:
                pass

            try:
                self.video_search_ids = set([v.get('videoId') for v in self.current_videos if v.get('videoId')])
            except Exception:
                self.video_search_ids = set()

            try:
                self._update_results_ids()
            except Exception:
                pass
            
            try:
                if self.media_index:
                    self.media_index.add_videos(self.current_videos)
            except Exception:
                pass

            def _fetch_playlists():
                    # Reset numbering for fresh scan
                    self.playlist_index_map = {}
                    self._safe_ui(lambda: self.playlist.clear_playlists())
                    
                    self._safe_ui(lambda: self.set_mid_job_title('Mapping playlists'))
                    # ... existing logic ...
                    
                    # OPTIMIZATION: Scan only currently loaded videos (target_limit)
                    # This prevents scanning 2000 videos if user only requested 40.
                    # If user clicks "Fetch More", we should ideally scan those too, but for now this fixes the "slowness"
                    videos = self.current_videos 
                    
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
                        try:
                            if self.media_index:
                                self.media_index.add_playlists([pl])
                        except Exception:
                            pass
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
                            try:
                                if self.media_index:
                                    self.media_index.bulk_link_playlist_videos(pid, [x.get('videoId') for x in (resp_pf.get('videos', []) or []) if x.get('videoId')])
                            except Exception:
                                pass
                        except Exception:
                            pass
                    def _progress(done, total):
                        self._safe_ui(lambda x=done, t=total: self.status_bar.configure(text=f"Collecting playlists from videos... {x}/{t}"))
                        self._safe_ui(lambda x=done, t=total: self.video.update_scan_progress(x, t))
                        self._safe_ui(lambda x=done, t=total: self.update_mid_scan_progress(x, t))
                    def _index(vid, pid, idx):
                        self._safe_ui(lambda v_id=vid, p_id=pid: self._update_video_row_by_vid(v_id, p_id))
                        try:
                            if self.media_index:
                                self.media_index.link_video_to_playlist(pid, vid, idx)
                        except Exception:
                            pass
                    try:
                        scanner.scan(videos, _on_pl, _prefetch, _progress, _index)
                    except Exception:
                        pass
                    try:
                        idx_map = _rm_build_index_map(videos, collected_local, getattr(self, 'playlist_index_map', {}))
                        self.playlist_index_map = dict(idx_map or {})
                        try:
                            cache_map = _rm_rebuild_cache(videos, idx_map)
                            for vid, pid in (cache_map or {}).items():
                                if self.media_index:
                                    self.media_index.link_video_to_playlist(pid, vid)
                        except Exception:
                            pass
                        try:
                            for item in self.playlist.playlist_tree.get_children():
                                vals = self.playlist.playlist_tree.item(item).get('values', [])
                                pi = self.playlist_index_map.get(item)
                                if pi is not None:
                                    new_vals = ((pi or ""),) + tuple(vals[1:]) if vals else ((pi or ""),)
                                    self.playlist.playlist_tree.item(item, values=new_vals)
                                    try:
                                        self.playlist.playlist_tree.set(item, 'No', str(pi))
                                    except Exception:
                                        pass
                            try:
                                self.playlist.normalize_numbers()
                            except Exception:
                                pass
                        except Exception:
                            pass
                    except Exception:
                        pass
                    try:
                        pids_map = {}
                        if self.media_index:
                            for pid, pm in self.media_index.playlists.items():
                                if pm.video_ids:
                                    pids_map[pid] = list(pm.video_ids)
                    except Exception:
                        pids_map = {}
                    try:
                        # Update playlistIndex on videos and sort
                        if self.media_index:
                            for v in videos:
                                vid = v.get('videoId')
                                if vid:
                                    pid = self.media_index.get_video_playlist(vid)
                                    if pid:
                                        idx = self.playlist_index_map.get(pid)
                                        if idx:
                                            v['playlistIndex'] = idx
                        
                        # Sort videos by playlistIndex (ascending)
                        videos.sort(key=lambda v: int(v.get('playlistIndex') or 999999))
                        
                        # Refresh UI with sorted videos
                        self._safe_ui(lambda: self.videos_mode_handler.populate_video_table(videos, clear=True, apply_marks=True))

                        # Assign sequence numbers to videos if missing
                        for i, v in enumerate(videos):
                            if 'sequence_number' not in v:
                                v['sequence_number'] = i + 1

                        if getattr(self.controller, 'datastore', None):
                             self.controller.datastore.save_last_videos_result(
                                query=query,
                                videos=videos,
                                playlists=collected_local,
                                next_token=self.video_next_page_token,
                                prev_token=self.video_prev_page_token,
                                video_ids=list(self.video_search_ids)
                             )
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
                            'playlistIds': pids_map
                        })
                        try:
                            self._save_media_index_snapshot()
                        except Exception:
                            pass
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
            try:
                pids_map = {}
                if self.media_index:
                    for pid, pm in self.media_index.playlists.items():
                        if pm.video_ids:
                            pids_map[pid] = list(pm.video_ids)
            except Exception:
                pids_map = {}
            ConfigManager.save_json(ConfigManager.get_last_search_path('videos'), {
                'query': query,
                'videos': videos,
                'playlists': [],
                'nextPageToken': self.video_next_page_token,
                'prevPageToken': self.video_prev_page_token,
                'videoIds': list(self.video_search_ids),
                'playlistPages': {pid: {'pages': cache.get('pages', {}), 'tokens': cache.get('tokens', {})} for pid, cache in (self.playlist_videos_cache or {}).items()},
                'playlistIds': pids_map
            })
            try:
                self._save_media_index_snapshot()
            except Exception:
                pass
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
                    ps = int(self.video.page_size_var.get())
                except Exception:
                    ps = 10
                try:
                    est_total = ps * idx + (ps if has_next else 0)
                except Exception:
                    est_total = len(videos)
                try:
                    self.video._panel.update_pages(index=idx, has_prev=has_prev, has_next=has_next, total_items=est_total)
                except Exception:
                    pass
            except Exception:
                pass

    def _load_last_results_data(self):
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
        return data

    def _restore_search_state(self, data):
        self.clear_panels()
        try:
            self.playlist_index_map = {}
        except Exception:
            pass
        videos = data.get('videos', [])
        playlists = data.get('playlists', [])
        
        try:
            if self.media_index:
                self.media_index.add_videos(videos)
                self.media_index.add_playlists(playlists)
        except Exception:
            pass
        try:
            ppages = data.get('playlistPages') or {}
            if isinstance(ppages, dict):
                self.playlist_videos_cache = ppages
        except Exception:
            pass
        try:
            pids = data.get('playlistIds') or {}
            if isinstance(pids, dict):
                try:
                    if self.media_index:
                        for pid, vids in pids.items():
                            self.media_index.bulk_link_playlist_videos(pid, vids or [])
                except Exception:
                    pass
        except Exception:
            pass
            
        try:
            if self.media_index:
                if not (data.get('playlistIds') or {}):
                    self._link_missing_playlists_from_ds(playlists)
        except Exception:
            pass

        try:
            q = data.get('query', '')
            self.search.search_entry.delete(0, 'end')
            if q:
                self.search.search_entry.insert(0, q)
            self.video_search_query = q or getattr(self, 'video_search_query', '')
        except Exception:
            pass
        try:
            ids = data.get('videoIds') or []
            self.video_search_ids = set([i for i in ids if i])
        except Exception:
            self.video_search_ids = set()
            
        try:
            idx_map = _rm_build_index_map(videos, playlists, getattr(self, 'playlist_index_map', {}))
            self.playlist_index_map = dict(idx_map or {})
            try:
                cache = _rm_rebuild_cache(videos, idx_map)
                for vid, pid in (cache or {}).items():
                    if self.media_index:
                        self.media_index.link_video_to_playlist(pid, vid)
            except Exception:
                pass
        except Exception:
            pass
            
        return videos, playlists

    def _link_missing_playlists_from_ds(self, playlists):
        try:
            for pl in (playlists or []):
                plid = pl.get('playlistId') or pl.get('id') or pl.get('playlist_id')
                if not plid:
                    continue
                try:
                    ds = getattr(self.controller, 'datastore', None)
                    vids_ds = []
                    if ds and hasattr(ds, 'get_playlist_videos'):
                        vids_ds = [x.get('videoId') for x in (ds.get_playlist_videos(plid, 50, 0) or []) if x.get('videoId')]
                    if vids_ds:
                        self.media_index.bulk_link_playlist_videos(plid, vids_ds)
                except Exception:
                    pass
        except Exception:
            pass

    def _async_recollect_playlists(self):
        import threading as _t
        def _collect_task():
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
                if not vid:
                    processed += 1
                    try:
                        self.after(0, lambda x=processed, t=total: self.video.update_scan_progress(x, t))
                    except Exception:
                        pass
                    continue
                title = (v.get('title') or '').strip()
                channel = (v.get('channelTitle') or '').strip()
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
                first_index = None
                first_plid = None
                for q in queries:
                    pls = []
                    try:
                        pls = self.controller.playlist_handler.search_playlists(q, max_results=5)
                    except Exception:
                        pls = []
                    for pl in pls:
                        plid = pl.get('playlistId')
                        has = False
                        try:
                            has = self.controller.playlist_handler.playlist_contains_video(plid, vid)
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
                        break
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
                    self.after(0, lambda x=processed, t=total: self.status_bar.configure(text=f"Collecting playlists from videos... {x}/{t}"))
                    self.after(0, lambda x=processed, t=total: self.video.update_scan_progress(x, t))
                    self.after(0, lambda x=processed, t=total: self.update_mid_scan_progress(x, t))
                except Exception:
                    pass
            try:
                ConfigManager.save_json(ConfigManager.get_last_search_path('videos'), {
                    'query': getattr(self, 'video_search_query', ''),
                    'videos': self.current_videos,
                    'playlists': collected,
                    'nextPageToken': getattr(self, 'video_next_page_token', None),
                    'prevPageToken': getattr(self, 'video_prev_page_token', None),
                    'pageIndex': getattr(self, 'video_search_page_index', 1),
                    'videoIds': list(getattr(self, 'video_search_ids', set()) or []),
                    'pinnedPlaylistId': getattr(self, 'pinned_playlist_id', None),
                    'totalResults': getattr(self, 'video_total_results', None)
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
                
        _t.Thread(target=_collect_task, daemon=True).start()

    def back_to_video_results(self):
        self.videos_mode_handler.back_to_video_results()

    def on_video_select(self, event=None):
        if self.search_mode != 'videos':
            return
        try:
            self.controller.ensure_playlist_handler()
        except Exception:
            pass
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
        if self.media_index:
            plid = self.media_index.get_video_playlist(vid)
            if plid:
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
                        ids_set = None
                        if self.media_index:
                            ids_set = self.media_index.get_playlist_video_ids(plid)
                        
                        if not ids_set:
                            cached_page = self._get_cached_playlist_page(plid, None)
                            if cached_page:
                                try:
                                    ids_set = {x.get('videoId') for x in cached_page.get('videos', []) if x.get('videoId')}
                                except Exception:
                                    ids_set = set()
                                try:
                                    if self.media_index:
                                        self.media_index.bulk_link_playlist_videos(plid, list(ids_set))
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
                            if self.media_index:
                                self.media_index.link_video_to_playlist(found, video_id)
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

    def show_videos_search_page(self, page_token=None, direction=None):
        self.videos_mode_handler.show_videos_search_page(page_token, direction)

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
            children = list(self.playlist.playlist_tree.get_children())
        except Exception:
            children = []
        try:
            result_ids = {v.get('videoId') for v in list(videos or []) if v.get('videoId')}
        except Exception:
            result_ids = set()
        hits_by_playlist = {}
        for pid in children:
            ids = set()
            try:
                if self.media_index:
                    ids = set(list(self.media_index.get_playlist_video_ids(pid) or []))
            except Exception:
                pass
            inter = ids.intersection(result_ids)
            if inter:
                hits_by_playlist[pid] = inter
        index_map = dict(self.playlist_index_map or {})
        for pid in hits_by_playlist.keys():
            try:
                if pid not in index_map:
                    index_map[pid] = len(index_map) + 1
            except Exception:
                pass
            try:
                info = self.controller.playlist_handler.get_playlist_info(pid)
            except Exception:
                info = {'playlistId': pid, 'title': '', 'channelTitle': '', 'video_count': 'N/A'}
            collected.append(info)
        vid_to_pid = {}
        for pid, vids in hits_by_playlist.items():
            for vid in vids:
                vid_to_pid[vid] = pid
        for v in list(videos or []):
            try:
                vid = v.get('videoId')
                pid = vid_to_pid.get(vid)
                if not pid:
                    continue
                v['playlistId'] = pid
                v['playlistIndex'] = index_map.get(pid)
                if self.media_index:
                    self.media_index.link_video_to_playlist(pid, vid)
            except Exception:
                pass
        try:
            self.playlist_index_map = index_map
        except Exception:
            pass
        try:
            ordered = sorted(index_map.keys(), key=lambda k: index_map[k])
            self.playlist.set_playlist_filter(ordered, index_map)
        except Exception:
            pass
        try:
            items = self.video.video_tree.get_children()
            for i, item in enumerate(items):
                if i < len(videos):
                    self.video.video_tree.item(item, values=self._video_row(videos[i]))
        except Exception:
            pass
        try:
            self.collected_playlists = collected
        except Exception:
            pass
        try:
            self._persist_last_videos_result()
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

    def recompute_indices_from_tree(self):
        try:
            children = list(self.playlist.playlist_tree.get_children())
        except Exception:
            children = []
        try:
            new_map = {}
            n = 1
            for pid in children:
                new_map[pid] = n
                n += 1
            self.playlist_index_map = new_map
        except Exception:
            pass
        try:
            self.playlist.normalize_numbers()
        except Exception:
            pass
        try:
            for v in list(self.current_videos or []):
                pid = v.get('playlistId')
                if pid in self.playlist_index_map:
                    v['playlistIndex'] = self.playlist_index_map[pid]
            items = self.video.video_tree.get_children()
            for i, item in enumerate(items):
                if i < len(self.current_videos):
                    self.video.video_tree.item(item, values=self._video_row(self.current_videos[i]))
        except Exception:
            pass

    def highlight_videos_for_playlist(self, playlist_id):
        self.videos_mode_handler.highlight_videos_for_playlist(playlist_id)

    def on_videos_mode_playlist_click(self, playlist_id):
        self.videos_mode_handler.on_videos_mode_playlist_click(playlist_id)

    def _report_playlist_hits(self, playlist_id):
        self.videos_mode_handler._report_playlist_hits(playlist_id)

    def _invalidate_hits_cache(self):
        self.videos_mode_handler._invalidate_hits_cache()

    def _update_results_ids(self):
        self.videos_mode_handler._update_results_ids()

    def clear_video_playlist_highlights(self):
        self.videos_mode_handler.clear_video_playlist_highlights()

    # Core functionality methods
    def search_playlists(self):
        """Search for playlists based on the keyword."""
        query = self.search.search_entry.get()
        if not query:
            messagebox.showerror("Error", "Please enter a keyword.")
            return

        try:
            # Clear existing items
            self.playlist.clear_playlists()

            # Search for playlists
            playlists = self.controller.playlist_handler.search_playlists(query)
            
            # Update each playlist with video count and status
            for playlist in playlists:
                try:
                    video_count = self.controller.playlist_handler.get_details(
                        playlist["playlistId"]
                    )
                    playlist["video_count"] = video_count
                except Exception:
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
            if not self.playlist.playlist_exists(playlist_id):
                info = self.controller.playlist_handler.get_playlist_info(playlist_id)
                self.playlist.update_playlist(info)
        except Exception:
            pass
        playlist_values = self.playlist.get_playlist_values(selected_item)
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
            next_before = getattr(self, 'current_page_token', None)
            prev_before = getattr(self, 'prev_page_token', None)
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
                    self._update_results_ids()
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
                            if self.media_index:
                                self.media_index.link_video_to_playlist(playlist_id, vid)
                except Exception:
                    pass
                try:
                    self._preview_only_hits = False
                except Exception:
                    pass
                try:
                    total_pages = (total_videos + max_results - 1) // max_results
                    if page_token is None:
                        self.current_page = 1
                    elif page_token == next_before:
                        self.current_page = min(int(getattr(self, 'current_page', 1) or 1) + 1, total_pages)
                    elif page_token == prev_before:
                        self.current_page = max(1, int(getattr(self, 'current_page', 1) or 1) - 1)
                except Exception:
                    pass
                self._render_playlist_videos(total_videos)
                try:
                    has_prev = bool(self.prev_page_token)
                    has_next = bool(self.current_page_token)
                    self.video._panel.update_pages(index=int(getattr(self, 'current_page', 1) or 1), has_prev=has_prev, has_next=has_next, total_items=total_videos)
                except Exception:
                    pass
                try:
                    if page_token is None:
                        self._show_playlist_listing_popup(playlist_id, self.current_videos)
                except Exception:
                    pass
                try:
                    self._persist_playlist_caches_only()
                except Exception:
                    pass
                return
            try:
                import threading as _t_wd
                import time as _t
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
                            if self.media_index:
                                self.media_index.link_video_to_playlist(playlist_id, vid)
                except Exception:
                    pass
                try:
                    self._update_results_ids()
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
                    try:
                        self.after(0, lambda: self._persist_playlist_caches_only())
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
                        if self.media_index:
                            self.media_index.link_video_to_playlist(playlist_id, vid)
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

            total_pages = (total_videos + max_results - 1) // max_results
            try:
                if not hasattr(self, 'current_page') or page_token is None:
                    self.current_page = 1
                elif page_token == next_before:
                    self.current_page = min(int(getattr(self, 'current_page', 1) or 1) + 1, total_pages)
                elif page_token == prev_before:
                    self.current_page = max(1, int(getattr(self, 'current_page', 1) or 1) - 1)
            except Exception:
                pass
            try:
                self.video.update_back_button_state(True)
            except Exception:
                pass

        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch videos: {e}")

    def _render_playlist_videos(self, total_videos):
        try:
            self.video.video_tree.delete(*self.video.video_tree.get_children())
        except Exception:
            pass
        hit_count = 0
        ql = (self.video_search_query or '').strip().lower()
        vids_set = set(getattr(self, 'video_search_ids', set()))
        def _ins_chunk(s):
            nonlocal hit_count
            try:
                ch = 50
                e = min(s + ch, len(self.current_videos or []))
                for i in range(s, e):
                    video = self.current_videos[i]
                    try:
                        vid = video.get('videoId')
                        ttl = str(video.get('title', '')).lower()
                        chn = str(video.get('channelTitle', '')).lower()
                        if getattr(self, '_preview_only_hits', False):
                            is_hit = bool(vid) and (vid in vids_set)
                        else:
                            is_hit = (bool(vid) and (vid in vids_set)) or (ql and (ql in ttl or ql in chn))
                        tags = ('search_hit',) if is_hit else ()
                        row = self._video_row(video)
                        if is_hit:
                            hit_count += 1
                            try:
                                row = (f"★ {row[0]}",) + row[1:]
                            except Exception:
                                pass
                        self.video.video_tree.insert('', 'end', values=row, tags=tags)
                    except Exception:
                        try:
                            self.video.video_tree.insert('', 'end', values=self._video_row(video))
                        except Exception:
                            pass
                if e < len(self.current_videos or []):
                    self.after(0, lambda st=e: _ins_chunk(st))
            except Exception:
                pass
        _ins_chunk(0)
        try:
            self.status_bar.configure(text=f"Highlighted {hit_count} matched videos in playlist")
        except Exception:
            pass
        
        # Calculate pages
        try:
            max_results = int(self.video.page_size_var.get())
        except Exception:
            max_results = 10
        total_pages = (total_videos + max_results - 1) // max_results
        
        if not hasattr(self, 'current_page') or (self.prev_page_token is None and self.current_page_token is None):
            self.current_page = 1

        # Update Pagination Bar
        try:
            has_prev = bool(self.prev_page_token)
            has_next = bool(self.current_page_token)
            
            # If we are not in API mode (no tokens), fall back to index-based logic
            if not has_prev and not has_next and total_pages > 1:
                # Local pagination? current_videos usually has ALL videos if no tokens?
                # If total_videos > len(current_videos), then we are in API mode but maybe first page?
                # If tokens are None but total > len, it implies we might be on page 1 of many, or just have all.
                # But show_playlist_videos usually sets tokens.
                pass

            self.video.update_pagination(self.current_page, total_videos, has_prev=has_prev, has_next=has_next)
            self.video.update_back_button_state(True)
        except Exception:
            pass

    def toggle_only_hits(self, enabled: bool):
        try:
            self._preview_only_hits = bool(enabled)
        except Exception:
            pass
        try:
            tv = max(int(self.video.total_label["text"].split(':')[-1].strip()), len(self.current_videos or []))
        except Exception:
            tv = len(self.current_videos or [])
        self._render_playlist_videos(tv)

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
        try:
            asc = self.playlist_sort_state.get(column_name, False)
            self.playlist.sort_playlists(column_name, not asc)
            self.playlist_sort_state[column_name] = not asc
        except Exception:
            pass

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
        selected_item = self.playlist.get_focused_playlist()
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
            # Open EXE folder via OS-specific handler; path not needed here
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
                    exe_path_local = os.path.join(dist_dir, "YouTubePlaylistExplorer.exe")
                    if sys.platform == "win32":
                        os.startfile(exe_path_local)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", exe_path_local])
                    else:
                        subprocess.run([exe_path_local])
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
                ok = False
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
                    err_msg = str(e)
                    self.after(0, lambda s=err_msg: _append(s + "\n"))
                    ok = False
                finally:
                    self.after(0, lambda: _done(ok))
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
                    except Exception as exc:
                        err_msg = str(exc)
                        self.after(0, lambda s=err_msg: _append(s + "\n"))
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
        try:
            mr_main = int(self.video.page_size_var.get())
        except Exception:
            mr_main = 10
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
        def _worker(mr):
            try:
                cached = self._get_cached_playlist_page(playlist_id, None)
            except Exception:
                cached = None
            if cached is not None:
                _printer(cached)
                return
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
                        import time
                        time.sleep(0.3)
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
            _t.Thread(target=lambda: _worker(mr_main), daemon=True).start()
        except Exception:
            pass

    def populate_videos_table_preview(self, playlist_id):
        self.videos_mode_handler.populate_videos_table_preview(playlist_id)

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
            pass
        except Exception:
            pass

    def _enrich_video_playlist_info(self, videos):
        try:
            for v in list(videos or []):
                try:
                    vid = v.get('videoId')
                    pid = v.get('playlistId')
                    if not pid and self.media_index:
                        pid = self.media_index.get_video_playlist(vid)
                    
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
                        if self.media_index:
                            self.media_index.link_video_to_playlist(pid, vid)
                except Exception:
                    pass
        except Exception:
            pass

    def restart_app(self):
        try:
            import subprocess
            import os
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
            pid = v.get('playlistId')
            if not pid and self.media_index:
                pid = self.media_index.get_video_playlist(vid)
            if pid:
                return pid
            
            try:
                existing = list(self.playlist.playlist_tree.get_children())
            except Exception:
                existing = []
            for plid in existing:
                try:
                    if self.controller.playlist_handler.playlist_contains_video(plid, vid):
                        try:
                            if self.media_index:
                                self.media_index.link_video_to_playlist(plid, vid)
                        except Exception:
                            pass
                        return plid
                except Exception:
                    continue
            try:
                title = (v.get('title') or '').strip()
                channel = (v.get('channelTitle') or '').strip()
                queries = []
                if title:
                    queries.append(title)
                if channel and title:
                    queries.append(f"{channel} {title}")
                if channel and not title:
                    queries.append(channel)
                for q in queries:
                    pls = []
                    try:
                        pls = self.controller.playlist_handler.search_playlists(q, max_results=5)
                    except Exception:
                        pls = []
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
                                    if self.media_index:
                                        self.media_index.link_video_to_playlist(plid, vid)
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
    def _persist_last_videos_result(self):
        try:
            from src.config_manager import ConfigManager
        except ModuleNotFoundError:
            from config_manager import ConfigManager
        try:
            vids = list(self.current_videos or [])
        except Exception:
            vids = []
        try:
            pls = list(self.collected_playlists or [])
        except Exception:
            pls = []
        try:
            nxt = getattr(self, 'video_next_page_token', None)
            prv = getattr(self, 'video_prev_page_token', None)
        except Exception:
            nxt, prv = None, None
        try:
            v_ids = list(getattr(self, 'video_search_ids', set()) or [])
        except Exception:
            v_ids = []
        try:
            pages = {pid: {'pages': cache.get('pages', {}), 'tokens': cache.get('tokens', {})} for pid, cache in (self.playlist_videos_cache or {}).items()}
        except Exception:
            pages = {}
        try:
            pids_map = {}
            if self.media_index:
                for pid, pm in self.media_index.playlists.items():
                    if pm.video_ids:
                        pids_map[pid] = list(pm.video_ids)
        except Exception:
            pids_map = {}
        try:
            ConfigManager.save_json(ConfigManager.get_last_search_path('videos'), {
                'query': getattr(self, 'video_search_query', ''),
                'videos': vids,
                'playlists': pls,
                'nextPageToken': nxt,
                'prevPageToken': prv,
                'videoIds': v_ids,
                'playlistPages': pages,
                'playlistIds': pids_map
            })
        except Exception:
            pass

    def _persist_playlist_caches_only(self):
        try:
            from src.config_manager import ConfigManager
        except ModuleNotFoundError:
            from config_manager import ConfigManager
        try:
            path = ConfigManager.get_last_search_path('videos')
            data = ConfigManager.load_json(path) or {}
        except Exception:
            data = {}
        try:
            pages = {pid: {'pages': cache.get('pages', {}), 'tokens': cache.get('tokens', {})} for pid, cache in (self.playlist_videos_cache or {}).items()}
        except Exception:
            pages = {}
        try:
            pids_map = {}
            if self.media_index:
                for pid, pm in self.media_index.playlists.items():
                    if pm.video_ids:
                        pids_map[pid] = list(pm.video_ids)
        except Exception:
            pids_map = {}
        try:
            data['playlistPages'] = pages
            data['playlistIds'] = pids_map
            # Do not overwrite 'videos' list here; preserve original search results for Back to Results
            ConfigManager.save_json(path, data)
        except Exception:
            pass
