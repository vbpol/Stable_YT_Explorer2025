import tkinter as tk
from tkinter import ttk
from .base_section import BaseSection
from tkinter import LabelFrame

class SearchSection(BaseSection):
    def setup_gui(self):
        """Create the search section."""
        self.configure(text="Search")
        self.pack(fill="x", padx=10, pady=5)
        
        # Create search entry and button
        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", padx=5, pady=5)
        
        tk.Label(search_frame, text="Enter keyword:").pack(pady=10)
        self.search_entry = tk.Entry(search_frame, width=60)
        self.search_entry.pack(pady=5)
        
        mode_frame = ttk.Frame(search_frame)
        mode_frame.pack(fill="x", pady=5)
        ttk.Label(mode_frame, text="Mode:").pack(side="left", padx=5)
        self.mode_var = tk.StringVar(value="Playlists")
        mode_combo = ttk.Combobox(
            mode_frame,
            textvariable=self.mode_var,
            values=["Playlists", "Videos"],
            width=12,
            state="readonly"
        )
        mode_combo.pack(side="left")
        mode_combo.bind('<<ComboboxSelected>>', lambda e: self.main_page.set_search_mode(self.mode_var.get()))

        tk.Button(search_frame, text="Search", command=lambda: self.main_page.execute_search(self.search_entry.get(), self.mode_var.get())).pack(pady=5)