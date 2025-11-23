import tkinter as tk
from .base_section import BaseSection
from src.pages.setup_page import SetupPage

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

        download_menu = tk.Menu(menubar, tearoff=0)
        quality_menu = tk.Menu(download_menu, tearoff=0)
        quality_menu.add_command(label="Best", command=lambda: self.main_page.set_preferred_quality("best"))
        quality_menu.add_command(label="720p", command=lambda: self.main_page.set_preferred_quality("best[height<=720]"))
        quality_menu.add_command(label="480p", command=lambda: self.main_page.set_preferred_quality("best[height<=480]"))
        quality_menu.add_command(label="360p", command=lambda: self.main_page.set_preferred_quality("best[height<=360]"))
        download_menu.add_cascade(label="Preferred Quality", menu=quality_menu)
        menubar.add_cascade(label="Download", menu=download_menu)