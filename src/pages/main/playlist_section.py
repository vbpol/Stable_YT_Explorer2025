from .base_section import BaseSection
import tkinter as tk
from tkinter import messagebox
try:
    from src.ui.table_panel import TablePanel
except ModuleNotFoundError:
    from ui.table_panel import TablePanel
import os

class PlaylistSection(BaseSection):
    def __init__(self, main_page):
        super().__init__(main_page, text="Playlists")
        self.controller = main_page.controller

    def setup_gui(self):
        """Initialize playlist section GUI components."""
        panel = TablePanel(self, columns=("No", "Title", "Channel", "Videos", "Status", "Actions"), show_page_size=False, size_label="Rows per page:")
        self._panel = panel
        self.playlist_tree = panel.tree
        try:
            self.playlist_tree.configure(selectmode='extended')
        except Exception:
            pass
        self.playlist_tree.column("No", width=50, anchor="center")
        self.playlist_tree.column("Title", width=300, anchor="w")
        self.playlist_tree.column("Channel", width=150, anchor="w")
        self.playlist_tree.column("Videos", width=70, anchor="center")
        self.playlist_tree.column("Status", width=120, anchor="center")
        self.playlist_tree.column("Actions", width=80, anchor="center")

        # Refresh is handled by mid controls in MainPage; no local button here

        # Bind events
        self.playlist_tree.bind("<Double-1>", self.on_playlist_select)
        self.playlist_tree.bind("<Button-1>", self.handle_click)
        try:
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
            self._ctx.add_separator()
            self._ctx.add_command(label="Download Selected Playlists", command=self.main_page.download_selected_playlists)
            self.playlist_tree.bind("<Button-3>", self._on_right_click)
        except Exception:
            pass

    

    def on_playlist_select(self, event):
        try:
            if getattr(self.main_page, '_preview_active', False):
                try:
                    messagebox.showinfo("Preview Active", "Use Back to Results to change playlist.")
                except Exception:
                    pass
                return "break"
        except Exception:
            pass
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
                        self.main_page.on_videos_mode_playlist_click(selected_playlist)
                    except Exception:
                        pass
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
        try:
            if getattr(self.main_page, '_preview_active', False):
                try:
                    messagebox.showinfo("Preview Active", "Use Back to Results to change playlist.")
                except Exception:
                    pass
                return "break"
        except Exception:
            pass
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
                            self.main_page.on_videos_mode_playlist_click(item)
                        except Exception:
                            pass
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
                    current = set(self.playlist_tree.selection())
                    if item not in current:
                        try:
                            self.playlist_tree.selection_add(item)
                        except Exception:
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
        """Check playlist download status via shared logic in MainPage."""
        try:
            return self.main_page._playlist_download_status(playlist_id, video_count)
        except Exception:
            try:
                # Fallback to direct computation
                playlist_values = self.playlist_tree.item(playlist_id)["values"]
                playlist_title = playlist_values[1] if playlist_values else "Unknown"
                folder = os.path.join(self.controller.default_folder, f"Playlist - {playlist_title}")
                if not os.path.exists(folder):
                    return "Not Downloaded"
                exts = ('.mp4', '.webm', '.mkv')
                files = [f for f in os.listdir(folder) if any(f.lower().endswith(e) for e in exts)]
                if not files:
                    return "Empty Folder"
                try:
                    vc = int(video_count or 0)
                except Exception:
                    vc = 0
                if vc and len(files) >= vc:
                    return "Complete"
                if vc:
                    return f"{len(files)}/{vc}"
                return str(len(files))
            except Exception:
                return "Unknown"

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
        try:
            cnt = len(self.playlist_tree.get_children())
            if hasattr(self, '_panel'):
                self._panel.update_pages(index=1, has_prev=False, has_next=False, total_items=cnt, row_count=cnt)
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
        """Refresh download status for all playlists with progress in status bar."""
        try:
            items = list(self.playlist_tree.get_children())
            total = len(items)
            done = 0
            try:
                self.main_page.status_bar.configure(text="Refreshing download statuses")
                self.main_page.set_mid_job_title('Refreshing statuses')
                self.main_page.show_mid_scan(total)
            except Exception:
                pass
            for playlist_id in items:
                try:
                    current_values = self.playlist_tree.item(playlist_id)["values"]
                except Exception:
                    current_values = []
                try:
                    vc = int(current_values[3])
                except Exception:
                    vc = 0
                try:
                    status = self.check_download_status(playlist_id, vc)
                except Exception:
                    status = "Unknown"
                try:
                    new_values = (
                        current_values[0] if len(current_values)>0 else "",
                        current_values[1] if len(current_values)>1 else "",
                        current_values[2] if len(current_values)>2 else "",
                        current_values[3] if len(current_values)>3 else "",
                        status,
                        current_values[5] if len(current_values)>5 else "❌"
                    )
                    self.playlist_tree.item(playlist_id, values=new_values)
                except Exception:
                    pass
                done += 1
                try:
                    self.main_page.update_mid_scan_progress(done, total)
                except Exception:
                    pass
            try:
                self.main_page.status_bar.configure(text="Statuses refreshed")
                self.main_page.finish_mid_scan()
            except Exception:
                pass
            try:
                from src.config_manager import ConfigManager
                ConfigManager.save_last_mode(getattr(self.main_page, 'search_mode', 'playlists'))
            except Exception:
                pass
        except Exception:
            try:
                self.main_page.status_bar.configure(text="Failed to refresh statuses")
            except Exception:
                pass
