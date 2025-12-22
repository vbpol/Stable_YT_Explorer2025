import tkinter as tk
import os
from .base_section import BaseSection
try:
    from src.pages.setup_page import SetupPage
except ModuleNotFoundError:
    from pages.setup_page import SetupPage

class MenuSection(BaseSection):
    def setup_gui(self):
        menubar = tk.Menu(self.controller.root)
        self.controller.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Change Download Folder", command=self.main_page.change_download_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Settings", command=lambda: self.controller.show_frame(SetupPage))
        file_menu.add_separator()
        file_menu.add_command(label="Export Playlist (CSV)", command=self.main_page.export_playlist_csv)
        file_menu.add_command(label="Export Playlist (TXT)", command=self.main_page.export_playlist_txt)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.controller.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Sort by Name", command=lambda: self.main_page._sort_playlists("Name"))
        view_menu.add_command(label="Sort by Channel", command=lambda: self.main_page._sort_playlists("Channel"))
        view_menu.add_command(label="Sort by Videos", command=lambda: self.main_page._sort_playlists("Videos"))
        menubar.add_cascade(label="View", menu=view_menu)

        # Download menu
        download_menu = tk.Menu(menubar, tearoff=0)
        download_menu.add_command(label="Save Playlist", command=self.main_page.save_playlist)
        download_menu.add_command(label="Download Videos", command=getattr(self.main_page, 'download_playlist_videos', lambda: None))
        download_menu.add_command(label="Download Selected", command=getattr(self.main_page, 'download_selected_videos', lambda: None))
        download_menu.add_command(label="View Downloaded", command=self.main_page.view_downloaded_videos)
        menubar.add_cascade(label="Download", menu=download_menu)

        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        
        def _set_search_limit(limit):
            ConfigManager.set_max_search_results(limit)
            tk.messagebox.showinfo("Settings", f"Search result limit set to {limit}.\nPlease repeat your search to apply.")
            
        search_limit_menu = tk.Menu(settings_menu, tearoff=0)
        search_limit_menu.add_command(label="40 Results", command=lambda: _set_search_limit(40))
        search_limit_menu.add_command(label="50 Results", command=lambda: _set_search_limit(50))
        search_limit_menu.add_command(label="100 Results", command=lambda: _set_search_limit(100))
        search_limit_menu.add_command(label="200 Results", command=lambda: _set_search_limit(200))
        search_limit_menu.add_command(label="500 Results", command=lambda: _set_search_limit(500))
        
        settings_menu.add_cascade(label="Max Search Results", menu=search_limit_menu)
        menubar.add_cascade(label="Settings", menu=settings_menu)

        env = str(os.getenv("APP_ENV", "")).strip().lower()
        if env not in ("production", "prod", "release"):
            tools_menu = tk.Menu(menubar, tearoff=0)
            tools_menu.add_command(label="Build EXE (Onefile)", command=getattr(self.main_page, 'build_exe_windows', lambda: None))
            tools_menu.add_command(label="Build Portable (Folder)", command=getattr(self.main_page, 'build_portable_windows', lambda: None))
            tools_menu.add_separator()
            tools_menu.add_command(label="Restart App", command=getattr(self.main_page, 'restart_app', lambda: None))
            menubar.add_cascade(label="Tools", menu=tools_menu)
