import tkinter as tk
from tkinter import ttk
from .base_section import BaseSection

class SearchSection(BaseSection):
    def setup_gui(self):
        self.configure(text="Search")
        self.pack(fill="x", padx=10, pady=5)
        row = ttk.Frame(self)
        row.pack(fill="x", padx=5, pady=6)
        ttk.Label(row, text="Mode:").pack(side="left", padx=(0, 6))
        self.mode_var = tk.StringVar(value="Playlists")
        ttk.Radiobutton(row, text="Playlists", variable=self.mode_var, value="Playlists", command=lambda: self.main_page.set_search_mode("Playlists")).pack(side="left")
        ttk.Radiobutton(row, text="Videos", variable=self.mode_var, value="Videos", command=lambda: self.main_page.set_search_mode("Videos")).pack(side="left", padx=(8, 12))
        ttk.Label(row, text="Enter keyword:").pack(side="left", padx=(0, 6))
        self.search_entry = tk.Entry(row, width=40)
        self.search_entry.pack(side="left")
        ttk.Button(row, text="Search", command=lambda: self.main_page.execute_search(self.search_entry.get(), self.mode_var.get())).pack(side="left", padx=(12, 0))
