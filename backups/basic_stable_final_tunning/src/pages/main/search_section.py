import tkinter as tk
from tkinter import ttk
from .base_section import BaseSection
from tkinter import LabelFrame

class SearchSection(BaseSection):
    def setup_gui(self):
        """Create the search section."""
        self.configure(text="Search")
        self.pack(fill="x", padx=10, pady=5)
        
        # Single-row search controls
        row = ttk.Frame(self)
        row.pack(fill="x", padx=10, pady=8)

        ttk.Label(row, text="Mode:").pack(side="left", padx=5)
        self.mode_var = tk.StringVar(value="Playlists")
        rb_pl = ttk.Radiobutton(row, text="Playlists", variable=self.mode_var, value="Playlists", command=lambda: self.main_page.set_search_mode(self.mode_var.get()))
        rb_vi = ttk.Radiobutton(row, text="Videos", variable=self.mode_var, value="Videos", command=lambda: self.main_page.set_search_mode(self.mode_var.get()))
        rb_pl.pack(side="left")
        rb_vi.pack(side="left", padx=(2, 10))

        ttk.Label(row, text="Enter keyword:").pack(side="left", padx=5)
        self.search_entry = tk.Entry(row, width=50)
        self.search_entry.pack(side="left", padx=5)

        tk.Button(row, text="Search", command=lambda: self.main_page.execute_search(self.search_entry.get(), self.mode_var.get())).pack(side="left", padx=10)