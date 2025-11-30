import tkinter as tk
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
