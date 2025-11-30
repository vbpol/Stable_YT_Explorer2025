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
            columns=("No", "Title", "Channel", "Videos", "Status", "Actions"),
            show="headings",
            selectmode="browse"
        )

        # Configure column headings
        self.playlist_tree.heading("No", text="No")
        self.playlist_tree.heading("Title", text="Title")
        self.playlist_tree.heading("Channel", text="Channel")
        self.playlist_tree.heading("Videos", text="Videos")
        self.playlist_tree.heading("Status", text="Download Status")
        self.playlist_tree.heading("Actions", text="Actions")

        # Configure column widths and alignments
        self.playlist_tree.column("No", width=50, anchor="center")
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
        try:
            import tkinter as tk
            self._ctx = tk.Menu(self.playlist_tree, tearoff=0)
            self._ctx.add_command(label="Highlight Related Videos", command=lambda: self.main_page.highlight_videos_for_playlist(getattr(self, "_rc_item", None)))
            self._ctx.add_command(label="Clear Video Highlights", command=self.main_page.clear_video_playlist_highlights)
            def _popup_show():
                pid = getattr(self, "_rc_item", None)
                if not pid:
                    return
                try:
                    cached = self.main_page._get_cached_playlist_page(pid, None)
                except Exception:
                    cached = None
                vids = []
                if cached is not None:
                    try:
                        vids = list(cached.get('videos', []) or [])
                    except Exception:
                        vids = []
                else:
                    try:
                        mr = int(self.main_page.video.page_size_var.get())
                    except Exception:
                        mr = 10
                    try:
                        resp = self.controller.playlist_handler.get_videos(pid, None, max_results=mr)
                        try:
                            self.main_page._cache_playlist_videos(pid, None, resp)
                        except Exception:
                            pass
                        vids = list(resp.get('videos', []) or [])
                    except Exception:
                        vids = []
                try:
                    self.main_page._show_playlist_listing_popup(pid, vids)
                except Exception:
                    pass
            def _print_dataset():
                pid = getattr(self, "_rc_item", None)
                if not pid:
                    return
                try:
                    self.main_page.print_playlist_videos_to_terminal(pid)
                except Exception:
                    pass
            def _populate_table():
                pid = getattr(self, "_rc_item", None)
                if not pid:
                    return
                try:
                    self.main_page.populate_videos_table_preview(pid)
                except Exception:
                    pass
            self._ctx.add_separator()
            self._ctx.add_command(label="Show Videos (Popup)", command=_popup_show)
            self._ctx.add_command(label="Print Videos Dataset", command=_print_dataset)
            self._ctx.add_command(label="Populate Videos Table", command=_populate_table)
            self.playlist_tree.bind("<Button-3>", self._on_right_click)
        except Exception:
            pass

    def on_playlist_select(self, event):
        """Handle double-click on playlist row.
        In Videos mode: consume event and only pin/print/highlight (no navigation)
        In Playlists mode: open playlist videos normally"""
        region = self.playlist_tree.identify_region(event.x, event.y)
        if region == "heading":
            col = self.playlist_tree.identify_column(event.x)
            name_map = {"#1":"No","#2":"Title","#3":"Channel","#4":"Videos","#5":"Status","#6":"Actions"}
            name = name_map.get(str(col))
            if name:
                try:
                    import tkinter.simpledialog as simpledialog
                    q = simpledialog.askstring("Filter", f"Filter {name} contains:")
                    if q is not None:
                        self.main_page.on_playlist_header_double_click(name, q)
                except Exception:
                    pass
            return
        if region == "cell":
            column = self.playlist_tree.identify_column(event.x)
            item = self.playlist_tree.identify_row(event.y)
            if str(column) != "#6":
                self.playlist_tree.selection_set(item)
                selected_playlist = self.get_selected_playlist()
                try:
                    print(f"[UI] Double-click playlist item={selected_playlist} mode={self.main_page.search_mode}")
                except Exception:
                    pass
                if self.main_page.search_mode == 'playlists':
                    self.main_page.show_playlist_videos_stable(selected_playlist)
                else:
                    try:
                        self.main_page._set_pinned_playlist(selected_playlist)
                    except Exception:
                        pass
                    try:
                        self.main_page.print_playlist_videos_to_terminal(selected_playlist)
                    except Exception:
                        pass
                    self.main_page.highlight_videos_for_playlist(selected_playlist)
                    try:
                        return "break"
                    except Exception:
                        pass

    def get_selected_playlist(self):
        """Get the currently selected playlist ID."""
        selected_items = self.playlist_tree.selection()
        if not selected_items:
            return None
        return selected_items[0]  # Return the playlist ID

    def handle_click(self, event):
        """Handle single-click in playlists table.
        In Videos mode: pin + terminal print + highlight; consume event"""
        region = self.playlist_tree.identify_region(event.x, event.y)
        if region == "heading":
            col = self.playlist_tree.identify_column(event.x)
            name_map = {"#1":"No","#2":"Title","#3":"Channel","#4":"Videos","#5":"Status","#6":"Actions"}
            name = name_map.get(str(col))
            if name:
                self.main_page.sort_playlists_by(name)
            return
        if region == "cell":
            column = self.playlist_tree.identify_column(event.x)
            item = self.playlist_tree.identify_row(event.y)
            if str(column) == "#6" and item:
                self.remove_playlist(item)
            else:
                self.playlist_tree.selection_set(item)
                try:
                    if self.main_page.search_mode == 'videos' and item:
                        try:
                            self.main_page._set_pinned_playlist(item)
                        except Exception:
                            pass
                        try:
                            self.main_page.print_playlist_videos_to_terminal(item)
                        except Exception:
                            pass
                        self.main_page.highlight_videos_for_playlist(item)
                        try:
                            return "break"
                        except Exception:
                            pass
                except Exception:
                    pass

    def _on_right_click(self, event):
        """Show context menu with popup/print/populate actions on right-click."""
        try:
            item = self.playlist_tree.identify_row(event.y)
            if item:
                self._rc_item = item
                try:
                    self.playlist_tree.selection_set(item)
                except Exception:
                    pass
                try:
                    self._ctx.tk_popup(event.x_root, event.y_root)
                except Exception:
                    pass
        except Exception:
            pass

    def remove_playlist(self, playlist_id):
        """Remove playlist from the tree."""
        if messagebox.askyesno("Confirm Removal", 
                             "Remove this playlist from the list?"):
            self.playlist_tree.delete(playlist_id)

    def check_download_status(self, playlist_id, video_count):
        """Check if all videos in the playlist are downloaded."""
        # Get the playlist title from the tree
        playlist_values = self.playlist_tree.item(playlist_id)["values"]
        playlist_title = playlist_values[1] if playlist_values else "Unknown"
        
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
            # Ensure video_count is enriched when missing
            vc = playlist_data.get("video_count")
            if vc in (None, "N/A"):
                try:
                    vc = int(self.controller.playlist_handler.get_details(playlist_id))
                    playlist_data["video_count"] = vc
                except Exception:
                    vc = "N/A"
            status = self.check_download_status(playlist_id, int(vc) if isinstance(vc, int) else 0)
        except Exception:
            status = "Unknown"
        
        try:
            pi = self.main_page.assign_playlist_index(playlist_id)
        except Exception:
            pi = ""
        values = (
            pi,
            playlist_data["title"],
            playlist_data["channelTitle"],
            playlist_data.get("video_count", "N/A"),
            status,
            "❌"
        )

        if self.playlist_tree.exists(playlist_id):
            self.playlist_tree.item(playlist_id, values=values)
        else:
            self.playlist_tree.insert("", "end", iid=playlist_id, values=values)
        try:
            self.playlist_tree.set(playlist_id, "No", str(pi or ""))
        except Exception:
            pass

    def normalize_numbers(self):
        try:
            for iid in self.playlist_tree.get_children():
                # Only show numbers for playlists that were matched in this session
                pi = self.main_page.playlist_index_map.get(iid)
                try:
                    vals = self.playlist_tree.item(iid).get('values', [])
                    new_vals = ((pi or ""),) + tuple(vals[1:]) if vals else ((pi or ""),)
                    self.playlist_tree.item(iid, values=new_vals)
                    self.playlist_tree.set(iid, "No", str(pi or ""))
                except Exception:
                    pass
        except Exception:
            pass

    def refresh_all_statuses(self):
        """Refresh download status for all playlists in the tree."""
        for playlist_id in self.playlist_tree.get_children():
            current_values = self.playlist_tree.item(playlist_id)["values"]
            try:
                vc = int(current_values[3])
            except Exception:
                vc = 0
            status = self.check_download_status(playlist_id, vc)
            
            new_values = (
                current_values[0],  # No
                current_values[1],  # Title
                current_values[2],  # Channel
                current_values[3],  # Videos count
                status,             # Updated status
                current_values[5]   # Actions
            )
            
            self.playlist_tree.item(playlist_id, values=new_values) 
