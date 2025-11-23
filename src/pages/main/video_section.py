import tkinter as tk
from tkinter import ttk
from .base_section import BaseSection

class VideoSection(BaseSection):
    def setup_gui(self):
        """Create the video section with pagination."""
        self.configure(text="Videos in Playlist")
        self.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create video tree
        self._create_video_tree()
        
        # Create page controls
        self._create_page_controls()
        
        # Create action buttons
        self._create_action_buttons()

    def _create_video_tree(self):
        columns = ("Title", "Duration")
        self.video_tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        self.video_tree.heading("Title", text="Title")
        self.video_tree.heading("Duration", text="Duration")
        self.video_tree.column("Duration", width=100, anchor="center")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.video_tree.yview)
        self.video_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack components
        self.video_tree.pack(side="left", fill="both", expand=True, padx=(10, 0))
        scrollbar.pack(side="right", fill="y", padx=(0, 10))
        
        self.video_tree.bind("<Double-1>", self.main_page.open_video)

    def _create_page_controls(self):
        # Page size and total info
        info_frame = ttk.Frame(self)
        info_frame.pack(fill="x", pady=5)
        
        # Left side: page size selector
        size_frame = ttk.Frame(info_frame)
        size_frame.pack(side="left")
        
        ttk.Label(size_frame, text="Videos per page:").pack(side="left", padx=5)
        self.page_size_var = tk.StringVar(value="10")
        page_size_combo = ttk.Combobox(
            size_frame, 
            textvariable=self.page_size_var,
            values=["5", "10", "20", "50"],
            width=5,
            state="readonly"
        )
        page_size_combo.pack(side="left", padx=5)
        page_size_combo.bind('<<ComboboxSelected>>', lambda e: self.main_page.show_playlist_videos())

        # Right side: total videos
        self.total_label = ttk.Label(info_frame, text="Total videos: 0")
        self.total_label.pack(side="right", padx=10)

        # Pagination frame
        pagination_frame = ttk.Frame(self)
        pagination_frame.pack(fill="x", pady=5)
        
        self.prev_page_btn = ttk.Button(
            pagination_frame, 
            text="Previous", 
            command=lambda: self.main_page.show_playlist_videos(page_token=self.main_page.prev_page_token),
            state="disabled"
        )
        self.prev_page_btn.pack(side="left", padx=5)
        
        self.page_indicator = ttk.Label(pagination_frame, text="Page 0 of 0")
        self.page_indicator.pack(side="left", padx=10)
        
        self.next_page_btn = ttk.Button(
            pagination_frame, 
            text="Next", 
            command=lambda: self.main_page.show_playlist_videos(page_token=self.main_page.current_page_token),
            state="disabled"
        )
        self.next_page_btn.pack(side="left", padx=5)

    def _create_action_buttons(self):
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=5)
        
        ttk.Button(button_frame, text="Save Playlist", 
                  command=self.main_page.save_playlist).pack(side="left", padx=5)
        
        # Add debug print to verify button click
        self.download_btn = ttk.Button(
            button_frame, 
            text="Download Videos", 
            command=lambda: print("Download button clicked") or self.main_page.download_playlist_videos()
        )
        self.download_btn.pack(side="left", padx=5)
        
        ttk.Button(button_frame, text="View Downloaded", 
                  command=self.main_page.view_downloaded_videos).pack(side="left", padx=5) 