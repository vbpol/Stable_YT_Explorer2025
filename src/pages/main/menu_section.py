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

        fragments_menu = tk.Menu(download_menu, tearoff=0)
        fragments_menu.add_command(label="1", command=lambda: self.main_page.set_concurrent_fragments(1))
        fragments_menu.add_command(label="2", command=lambda: self.main_page.set_concurrent_fragments(2))
        fragments_menu.add_command(label="4", command=lambda: self.main_page.set_concurrent_fragments(4))
        fragments_menu.add_command(label="8", command=lambda: self.main_page.set_concurrent_fragments(8))
        download_menu.add_cascade(label="Concurrent Fragments", menu=fragments_menu)

        download_menu.add_checkbutton(label="Post-Processing (merge to mp4)", onvalue=1, offvalue=0, command=self.main_page.toggle_post_processing)
        menubar.add_cascade(label="Download", menu=download_menu)

        # Persistence menu
        persist_menu = tk.Menu(menubar, tearoff=0)
        self.persist_var = tk.StringVar(value=(self.controller.config.get("persistence", "") or "json").capitalize())
        persist_menu.add_radiobutton(label="JSON", variable=self.persist_var, value="Json", command=lambda: self.main_page.set_persistence_mode("json"))
        persist_menu.add_radiobutton(label="SQLite", variable=self.persist_var, value="Sqlite", command=lambda: self.main_page.set_persistence_mode("sqlite"))
        persist_menu.add_radiobutton(label="Django", variable=self.persist_var, value="Django", command=lambda: self.main_page.set_persistence_mode("django"))
        menubar.add_cascade(label="Persistence", menu=persist_menu)