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
        self._playlist_map = {}
        self._playlist_order = []
        self._current_page = 1
        self._filter_column = None
        self._filter_query = None

    def setup_gui(self):
        """Initialize playlist section GUI components."""
        panel = TablePanel(self, columns=("No", "Title", "Channel", "Videos", "Status", "Actions"), show_page_size=True, size_label="Rows per page:")
        self._panel = panel
        self.playlist_tree = panel.tree
        self._pagination = panel.pagination
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

        # Bind events
        self.playlist_tree.bind("<Double-1>", self.on_playlist_select)
        self.playlist_tree.bind("<Button-1>", self.handle_click)
        try:
            self._ctx = tk.Menu(self.playlist_tree, tearoff=0)
            self._ctx.add_command(label="Highlight Related Videos", command=lambda: self.main_page.highlight_videos_for_playlist(getattr(self, "_rc_item", None)))
            self._ctx.add_command(label="Clear Video Highlights", command=self.main_page.clear_video_playlist_highlights)
            def _popup_show():
                pid = getattr(self, "_rc_item", None)
                if not pid: return
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
                if not pid: return
                try:
                    self.main_page.print_playlist_videos_to_terminal(pid)
                except Exception:
                    pass
            def _populate_table():
                pid = getattr(self, "_rc_item", None)
                if not pid: return
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

        # Pagination callbacks
        self._pagination.prev_btn.configure(command=self._prev_page)
        self._pagination.next_btn.configure(command=self._next_page)
        self._pagination.page_size_var.trace("w", self._on_page_size_change)
        
        # Initial template setup
        try:
             self._pagination.set_total_template("Total playlists: {}")
        except Exception:
             pass

    def _prev_page(self):
        if self._current_page > 1:
            self._current_page -= 1
            self._refresh_table()

    def _next_page(self):
        self._current_page += 1
        self._refresh_table()

    def _on_page_size_change(self, *args):
        self._current_page = 1
        self._refresh_table()

    def _refresh_table(self):
        try:
            for item in self.playlist_tree.get_children():
                self.playlist_tree.delete(item)
            
            try:
                ps = int(self._pagination.page_size_var.get())
            except Exception:
                ps = 10
            
            # Apply filter
            filtered_order = []
            if self._filter_query and self._filter_column:
                idx_map = {"No": 0, "Title": 1, "Channel": 2, "Videos": 3, "Status": 4, "Actions": 5}
                idx = idx_map.get(self._filter_column)
                q = self._filter_query.lower()
                for pid in self._playlist_order:
                    vals = self._playlist_map.get(pid)
                    if not vals: continue
                    s = str(vals[idx]) if idx is not None and idx < len(vals) else ''
                    if q in s.lower():
                        filtered_order.append(pid)
            else:
                filtered_order = list(self._playlist_order)
            
            total = len(filtered_order)
            
            # Adjust page
            total_pages = (total + ps - 1) // max(ps, 1)
            if self._current_page > total_pages and total_pages > 0:
                self._current_page = total_pages
            if self._current_page < 1:
                self._current_page = 1
                
            start_idx = (self._current_page - 1) * ps
            end_idx = start_idx + ps
            
            page_items = filtered_order[start_idx:end_idx]
            
            for pid in page_items:
                vals = self._playlist_map.get(pid)
                if vals:
                    self.playlist_tree.insert("", "end", iid=pid, values=vals)
                    try:
                        self.playlist_tree.set(pid, "No", str(vals[0] or ""))
                    except Exception:
                        pass
            
            self._pagination.update_state(self._current_page, total)
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
        """Handle double-click on playlist row."""
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
                        self.set_filter(name, q)
                except Exception:
                    pass
            return
        if region == "cell":
            column = self.playlist_tree.identify_column(event.x)
            item = self.playlist_tree.identify_row(event.y)
            if str(column) != "#6":
                self.playlist_tree.selection_set(item)
                selected_playlist = self.get_selected_playlist()
                if self.main_page.search_mode == 'playlists':
                    self.main_page.show_playlist_videos_stable(selected_playlist)
                else:
                    try:
                        self.main_page.populate_videos_table_preview(selected_playlist)
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
        return selected_items[0]

    def handle_click(self, event):
        try:
            if getattr(self.main_page, '_preview_active', False):
                try:
                    item = self.playlist_tree.identify_row(event.y)
                except Exception:
                    item = None
                try:
                    col = self.playlist_tree.identify_column(event.x)
                except Exception:
                    col = None
                try:
                    if self.main_page.search_mode == 'videos' and item and str(col) != "#6":
                        try:
                            self.main_page.back_to_video_results()
                        except Exception:
                            pass
                        try:
                            self.playlist_tree.selection_set(item)
                        except Exception:
                            pass
                        try:
                            self.main_page.on_videos_mode_playlist_click(item)
                        except Exception:
                            pass
                        return "break"
                except Exception:
                    pass
                return "break"
        except Exception:
            pass
        """Handle single-click in playlists table."""
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
        """Show context menu."""
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
        if messagebox.askyesno("Confirm Removal", "Remove this playlist from the list?"):
            if playlist_id in self._playlist_map:
                del self._playlist_map[playlist_id]
            if playlist_id in self._playlist_order:
                self._playlist_order.remove(playlist_id)
            self._refresh_table()

    def check_download_status(self, playlist_id, video_count):
        """Check playlist download status."""
        try:
            return self.main_page._playlist_download_status(playlist_id, video_count)
        except Exception:
            try:
                playlist_values = self._playlist_map.get(playlist_id)
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
        playlist_id = playlist_data["playlistId"]
        try:
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
        
        self._playlist_map[playlist_id] = values
        if playlist_id not in self._playlist_order:
            self._playlist_order.append(playlist_id)
        
        self._refresh_table()

    def normalize_numbers(self):
        for pid in self._playlist_order:
             pi = self.main_page.playlist_index_map.get(pid)
             if pid in self._playlist_map:
                 vals = list(self._playlist_map[pid])
                 vals[0] = pi or ""
                 self._playlist_map[pid] = tuple(vals)
        self._refresh_table()

    def refresh_all_statuses(self):
        try:
            total = len(self._playlist_order)
            done = 0
            try:
                self.main_page.status_bar.configure(text="Refreshing download statuses")
                self.main_page.set_mid_job_title('Refreshing statuses')
                self.main_page.show_mid_scan(total)
            except Exception:
                pass
            
            for playlist_id in self._playlist_order:
                try:
                    current_values = self._playlist_map.get(playlist_id)
                    if not current_values:
                        continue
                except Exception:
                    continue
                
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
                    self._playlist_map[playlist_id] = new_values
                except Exception:
                    pass
                done += 1
                try:
                    self.main_page.update_mid_scan_progress(done, total)
                except Exception:
                    pass
            
            self._refresh_table()
            
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

    def clear_playlists(self):
        self._playlist_map.clear()
        self._playlist_order.clear()
        self._current_page = 1
        self._refresh_table()

    def playlist_exists(self, playlist_id):
        return playlist_id in self._playlist_map

    def get_playlist_values(self, playlist_id):
        return self._playlist_map.get(playlist_id)

    def bring_to_top(self, playlist_id):
        if playlist_id in self._playlist_order:
            self._playlist_order.remove(playlist_id)
            self._playlist_order.insert(0, playlist_id)
            self._current_page = 1
            self._refresh_table()

    def update_playlist_item(self, playlist_id, values):
        if playlist_id in self._playlist_map:
            self._playlist_map[playlist_id] = values
            self._refresh_table()
    
    def sort_playlists(self, column_name, ascending=True):
        idx_map = {"No": 0, "Title": 1, "Channel": 2, "Videos": 3, "Status": 4, "Actions": 5}
        idx = idx_map.get(column_name)
        if idx is None: return
        def _key(pid):
            vals = self._playlist_map.get(pid)
            if not vals: return ""
            v = vals[idx] if idx < len(vals) else ''
            if column_name == 'Videos' or column_name == 'No':
                try: return int(v)
                except: return -1
            return str(v).lower()
        self._playlist_order.sort(key=_key, reverse=not ascending)
        self._current_page = 1
        self._refresh_table()

    def get_focused_playlist(self):
        return self.playlist_tree.focus()

    def set_selection_mode(self, mode):
        try: self.playlist_tree.configure(selectmode=mode)
        except: pass

    def set_playlist_filter(self, ordered_ids, index_map):
        self._playlist_order = list(ordered_ids)
        for pid, idx in index_map.items():
            if pid in self._playlist_map:
                vals = list(self._playlist_map[pid])
                vals[0] = idx
                self._playlist_map[pid] = tuple(vals)
        self._current_page = 1
        self._refresh_table()

    def get_all_playlist_ids(self):
        return list(self._playlist_order)

    def set_filter(self, column_name, query):
        self._filter_column = column_name
        self._filter_query = query
        self._current_page = 1
        self._refresh_table()

    def select_playlist(self, playlist_id):
        if playlist_id in self._playlist_map:
            try: self.playlist_tree.selection_set(playlist_id)
            except: pass

    def see_playlist(self, playlist_id):
        if playlist_id in self._playlist_map:
            try: self.playlist_tree.see(playlist_id)
            except: pass
