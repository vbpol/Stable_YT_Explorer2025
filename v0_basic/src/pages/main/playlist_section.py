from .base_section import BaseSection
import tkinter as tk
from tkinter import ttk, messagebox
import os

class PlaylistSection(BaseSection):
    def __init__(self, main_page):
        super().__init__(main_page, text="Playlists")
        self.controller = main_page.controller

    def setup_gui(self):
        """Initialize playlist section GUI components."""
        # Create treeview with scrollbar
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(fill="both", expand=True)

        # Create and configure the treeview
        self.playlist_tree = ttk.Treeview(
            self.tree_frame,
            columns=("Title", "Channel", "Videos", "Status", "Actions"),
            show="headings",
            selectmode="browse"
        )

        # Configure column headings
        self.playlist_tree.heading("Title", text="Title")
        self.playlist_tree.heading("Channel", text="Channel")
        self.playlist_tree.heading("Videos", text="Videos")
        self.playlist_tree.heading("Status", text="Download Status")
        self.playlist_tree.heading("Actions", text="Actions")

        # Configure column widths and alignments
        self.playlist_tree.column("Title", width=300, anchor="w")
        self.playlist_tree.column("Channel", width=150, anchor="w")
        self.playlist_tree.column("Videos", width=70, anchor="center")
        self.playlist_tree.column("Status", width=120, anchor="center")
        self.playlist_tree.column("Actions", width=80, anchor="center")

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.playlist_tree.yview)
        self.playlist_tree.configure(yscrollcommand=scrollbar.set)

        # Pack components
        self.playlist_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Add refresh button
        self.refresh_btn = ttk.Button(
            self, 
            text="Refresh Status", 
            command=self.refresh_all_statuses
        )
        self.refresh_btn.pack(pady=5)

        # Bind events
        self.playlist_tree.bind("<Double-1>", self.on_playlist_select)
        self.playlist_tree.bind("<Button-1>", self.handle_click)

    def on_playlist_select(self, event):
        """Handle playlist selection."""
        region = self.playlist_tree.identify_region(event.x, event.y)
        print(f"Click region: {region}")  # Debug print
        
        if region == "cell":
            column = self.playlist_tree.identify_column(event.x)
            item = self.playlist_tree.identify_row(event.y)
            print(f"Clicked column: {column}, item: {item}")  # Debug print
            
            if str(column) != "#5":  # If not clicking the Actions column
                # Select the item first
                self.playlist_tree.selection_set(item)
                selected_playlist = self.get_selected_playlist()
                print(f"Selected playlist ID: {selected_playlist}")  # Debug print
                
                # Get the playlist details from the tree
                playlist_info = self.playlist_tree.item(selected_playlist)
                print(f"Playlist info: {playlist_info}")  # Debug print
                
                # Then show videos
                self.main_page.show_playlist_videos(selected_playlist)

    def get_selected_playlist(self):
        """Get the currently selected playlist ID."""
        selected_items = self.playlist_tree.selection()
        if not selected_items:
            return None
        return selected_items[0]  # Return the playlist ID

    def handle_click(self, event):
        """Handle clicks on the playlist tree."""
        region = self.playlist_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.playlist_tree.identify_column(event.x)
            item = self.playlist_tree.identify_row(event.y)
            
            if str(column) == "#5" and item:  # Actions column
                self.remove_playlist(item)
            else:
                # Select the row when clicking anywhere except the remove button
                self.playlist_tree.selection_set(item)

    def remove_playlist(self, playlist_id):
        """Remove playlist from the tree."""
        if messagebox.askyesno("Confirm Removal", 
                             "Remove this playlist from the list?"):
            self.playlist_tree.delete(playlist_id)

    def check_download_status(self, playlist_id, video_count):
        """Check if all videos in the playlist are downloaded."""
        # Get the playlist title from the tree
        playlist_values = self.playlist_tree.item(playlist_id)["values"]
        playlist_title = playlist_values[0] if playlist_values else "Unknown"
        
        playlist_folder = os.path.join(
            self.controller.default_folder,
            f"Playlist - {playlist_title}"  # Match the folder name format used in download
        )

        if not os.path.exists(playlist_folder):
            return "Not Downloaded"

        video_files = [
            f for f in os.listdir(playlist_folder) 
            if f.lower().endswith(('.mp4', '.webm', '.mkv'))
        ]
        
        if len(video_files) == 0:
            return "Empty Folder"
        elif len(video_files) < video_count:
            return f"{len(video_files)}/{video_count}"
        else:
            return "Complete"

    def update_playlist(self, playlist_data):
        """Update or add a playlist to the tree."""
        playlist_id = playlist_data["playlistId"]
        
        # Use a default status of "Unknown" if we can't get details
        try:
            status = self.check_download_status(
                playlist_id, 
                playlist_data.get("video_count", 0)
            )
        except Exception:
            status = "Unknown"
        
        values = (
            playlist_data["title"],
            playlist_data["channelTitle"],
            playlist_data.get("video_count", "N/A"),  # Use N/A if count not available
            status,
            "❌"
        )

        if self.playlist_tree.exists(playlist_id):
            self.playlist_tree.item(playlist_id, values=values)
        else:
            self.playlist_tree.insert("", "end", iid=playlist_id, values=values)

    def refresh_all_statuses(self):
        """Refresh download status for all playlists in the tree."""
        for playlist_id in self.playlist_tree.get_children():
            current_values = self.playlist_tree.item(playlist_id)["values"]
            status = self.check_download_status(playlist_id, int(current_values[2]))
            
            new_values = (
                current_values[0],  # Title
                current_values[1],  # Channel
                current_values[2],  # Videos count
                status,            # Updated status
                current_values[4]  # Actions
            )
            
            self.playlist_tree.item(playlist_id, values=new_values) 