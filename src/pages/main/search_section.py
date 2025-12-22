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
        
        # Add Exact Match Checkbox
        self.exact_match_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row, text="Exact Match", variable=self.exact_match_var).pack(side="left", padx=(8, 0))
        
        self.search_btn = tk.Button(row, text="Search", command=lambda: self.main_page.execute_search_stable(self.search_entry.get(), self.mode_var.get()))
        self.search_btn.pack(side="left", padx=(12, 0))

    def update_search_button_color(self, status):
        """
        Update search button color based on API key status.
        status: 'valid' (green), 'warning' (orange), 'invalid' (red)
        """
        color_map = {
            'valid': '#90EE90',  # Light Green
            'warning': '#FFB347', # Pastel Orange
            'invalid': '#FF6961'  # Pastel Red
        }
        bg_color = color_map.get(status, 'SystemButtonFace')
        try:
            self.search_btn.configure(bg=bg_color)
        except Exception:
            pass
