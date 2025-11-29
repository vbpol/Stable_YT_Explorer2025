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
        
        tk.Label(search_frame, text="Enter keyword to search for playlists:").pack(pady=10)
        self.search_entry = tk.Entry(search_frame, width=60)
        self.search_entry.pack(pady=5)
        
        tk.Button(search_frame, text="Search", command=self.main_page.search_playlists).pack(pady=5) 