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
from .handlers.search_persistence_handler import SearchPersistenceHandler
from .handlers.video_ui_handler import VideoUIHandler
from .handlers.playlist_ui_handler import PlaylistUIHandler
from .handlers.action_handler import ActionHandler
from .handlers.build_handler import BuildHandler
try:
    from src.services.video_playlist_scanner import VideoPlaylistScanner
    from src.services.media_index import MediaIndex
    from src.data.json_store import JsonStore
except ModuleNotFoundError:
    from services.video_playlist_scanner import VideoPlaylistScanner
    from services.media_index import MediaIndex
    from data.json_store import JsonStore

class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._lock = threading.Lock()
        self._search_session = 0
        self.current_videos = []
        self.current_playlist_info = {}
        self.current_page_token = None
        self._initialize_components()

    def _safe_ui(self, fn):
        """Schedule a UI update safely from a background thread."""
        try:
            # Note: winfo_exists() itself is NOT thread-safe in all Tkinter versions.
            # We defer all checks to the main thread via self.after.
            def _wrapped():
                try:
                    if self.winfo_exists():
                        fn()
                except Exception:
                    pass
            self.after(0, _wrapped)
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
        self._pl_hits_cache = {}
        self.video_results_ids = set()
        self.viewing_playlist_id = None
        try:
            self.media_index = MediaIndex()
        except Exception:
            self.media_index = None
        
        self.search_persistence = SearchPersistenceHandler(self)
        self.video_ui_handler = VideoUIHandler(self)
        self.playlist_ui_handler = PlaylistUIHandler(self)
        self.action_handler = ActionHandler(self)
        self.build_handler = BuildHandler(self)
        
        try:
            self.video_scanner = VideoPlaylistScanner(self.controller.api_key)
        except Exception:
            self.video_scanner = None
        
        try:
            self._load_media_index_snapshot()
        except Exception:
            pass
        self._fmt_date = self.video_ui_handler._fmt_date
        self._video_row = self.video_ui_handler._video_row
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
        self._build_in_progress = False

    def _save_media_index_snapshot(self):
        self.search_persistence.save_media_index_snapshot()

    def _load_media_index_snapshot(self):
        self.search_persistence.load_media_index_snapshot()

    def _video_target_folder(self, v):
        return self.video_ui_handler._video_target_folder(v)

    def _find_downloaded_file(self, folder, title, video_id=None):
        return self.video_ui_handler._find_downloaded_file(folder, title, video_id)

    def _video_download_status(self, v):
        return self.video_ui_handler._video_download_status(v)

    def _count_downloaded_files(self, folder):
        return self.playlist_ui_handler._count_downloaded_files(folder)

    def _playlist_folder_by_id(self, playlist_id):
        return self.playlist_ui_handler.playlist_folder_by_id(playlist_id)

    def _playlist_download_status(self, playlist_id, expected_count):
        return self.playlist_ui_handler.playlist_download_status(playlist_id, expected_count)

    def refresh_video_statuses(self):
        self.video_ui_handler.refresh_video_statuses()

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
        self.video_ui_handler.update_video_row_by_vid(vid, playlist_id)

    def _bring_playlist_to_top(self, playlist_id):
        self.playlist_ui_handler.bring_playlist_to_top(playlist_id)

    def _set_pinned_playlist(self, playlist_id):
        self.playlist_ui_handler.set_pinned_playlist(playlist_id)

    def _cache_playlist_videos(self, playlist_id, page_token, response):
        self.action_handler.cache_playlist_videos(playlist_id, page_token, response)

    def _get_cached_playlist_page(self, playlist_id, page_token):
        return self.action_handler.get_cached_playlist_page(playlist_id, page_token)

    def assign_playlist_index(self, playlist_id):
        return self.action_handler.assign_playlist_index(playlist_id)

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
        """Reset UI and clear internal data state safely."""
        try:
            if self.video_scanner:
                self.video_scanner.stop()
        except Exception:
            pass

        with self._lock:
            self._search_session += 1
            try:
                self.playlist.playlist_tree.delete(*self.playlist.playlist_tree.get_children())
            except Exception:
                pass
            try:
                self.video.video_tree.delete(*self.video.video_tree.get_children())
            except Exception:
                pass
            
            self.current_videos = []
            self.action_handler.current_playlist_info = None
            self.prev_page_token = None
            self.current_page_token = None
            self.viewing_playlist_id = None
            self.video_results_ids = set()
            self.playlist_index_map = {}
            
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
        """Loads last search results using SearchPersistenceHandler."""
        self.search_persistence.load_and_restore_search(mode_display)

    def execute_search(self, query, mode_display):
        self.action_handler.execute_search(query, mode_display)

    def _execute_search_deprecated(self, query, mode_display):
        # We keep the old name temporarily to avoid breaking internal calls if any
        self.action_handler.execute_search(query, mode_display)

    def back_to_video_results(self):
        self.action_handler.back_to_video_results()


    def on_video_select(self, event=None):
        self.action_handler.on_video_select(event)


    def show_videos_search_page(self, page_token=None):
        self.action_handler.show_videos_search_page(page_token)

    def execute_search_stable(self, query, mode_display):
        self.action_handler.execute_search(query, mode_display)

    def _render_playlist_videos(self, total_videos=None):
        """Compatibility method for rendering videos."""
        self.video_ui_handler.render_videos(
            self.current_videos,
            getattr(self, 'video_search_ids', set()),
            getattr(self, 'video_search_query', '')
        )

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
        return self.playlist_ui_handler.map_videos_to_playlists(videos)

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

    def refresh_all_statuses(self):
        self.playlist_ui_handler.refresh_all_statuses()

    def refresh_playlist(self):
        self.playlist_ui_handler.refresh_all_statuses()

    def recompute_indices_from_tree(self):
        self.playlist_ui_handler.normalize_playlist_indices()

    def highlight_videos_for_playlist(self, playlist_id):
        self.playlist_ui_handler.highlight_videos_for_playlist(playlist_id)

    def on_videos_mode_playlist_click(self, playlist_id):
        self.playlist_ui_handler.on_videos_mode_playlist_click(playlist_id)

    def _report_playlist_hits(self, playlist_id):
        self.playlist_ui_handler._report_playlist_hits(playlist_id)



    def _update_results_ids(self):
        self.video_ui_handler.update_results_ids()

    def clear_video_playlist_highlights(self):
        self.video_ui_handler.clear_video_playlist_highlights()

    def toggle_only_hits(self, enabled: bool):
        self.video_ui_handler.toggle_only_hits(enabled)

    def on_video_header_double_click(self, column_name, q=None):
        self.video_ui_handler.on_video_header_double_click(column_name, q)

    def on_playlist_header_double_click(self, column_name, q=None):
        self.playlist_ui_handler.on_playlist_header_double_click(column_name, q)

    def sort_videos_by(self, column_name):
        self.video_ui_handler.sort_videos_by(column_name)

    def sort_playlists_by(self, column_name):
        self.playlist_ui_handler.sort_playlists_by(column_name)

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
        self.action_handler.save_playlist()

    def export_playlist_csv(self):
        self.action_handler.export_playlist_csv()

    def export_playlist_txt(self):
        self.action_handler.export_playlist_txt()

    def change_download_folder(self):
        self.action_handler.change_download_folder()

    def open_download_folder(self):
        self.action_handler.open_download_folder()

    def build_exe_windows(self):
        """Delegated to BuildHandler."""
        self.build_handler.build_exe_windows()

    def build_portable_windows(self):
        """Delegated to BuildHandler."""
        self.build_handler.build_portable_windows()

    def view_downloaded_videos(self):
        self.action_handler.view_downloaded_videos()

    def download_playlist_videos(self):
        self.action_handler.download_playlist_videos()

    def print_playlist_videos_to_terminal(self, playlist_id):
        self.action_handler.print_playlist_videos_to_terminal(playlist_id)

    def populate_videos_table_preview(self, playlist_id):
        self.video_ui_handler.populate_videos_table_preview(playlist_id)

    def _show_playlist_listing_popup(self, playlist_id, videos):
        self.video_ui_handler.show_playlist_listing_popup(playlist_id, videos)


    def download_selected_videos(self):
        self.action_handler.download_selected_videos()

    def download_single_video(self):
        self.action_handler.download_single_video()

    def download_selected_playlists(self):
        self.action_handler.download_selected_playlists()

    def _start_download_for_videos(self, videos, folder=None):
        self.action_handler._start_download_for_videos(videos, folder)

    def _enrich_video_playlist_info(self, videos):
        self.action_handler._enrich_video_playlist_info(videos)

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
    def _persist_last_videos_result(self):
        self.search_persistence.persist_last_videos_result()
