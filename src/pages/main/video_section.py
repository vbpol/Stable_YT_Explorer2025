import tkinter as tk
from tkinter import ttk
from .base_section import BaseSection
try:
    from src.ui.table_panel import TablePanel
except ModuleNotFoundError:
    from ui.table_panel import TablePanel

class VideoSection(BaseSection):
    def setup_gui(self):
        """Create the video section with pagination."""
        self._title_videos = "Videos"
        self._title_playlist = "Videos in Playlist"
        self.configure(text=self._title_videos)
        self.pack(fill="both", expand=True, padx=10, pady=10)
        
        cols = ("Title", "Playlist", "Channel", "Duration", "Published", "Views", "Status", "Actions")
        self._panel = TablePanel(self, columns=cols, show_page_size=True, size_label="Videos per page:")
        self.video_tree = self._panel.tree
        try:
            self.video_tree.configure(selectmode='extended')
        except Exception:
            pass
        self._create_video_tree_styles()
        self._pagination = self._panel.pagination
        self.prev_page_btn = self._pagination.prev_btn
        self.next_page_btn = self._pagination.next_btn
        self.page_indicator = self._pagination.page_indicator
        self.total_label = self._pagination.total_label
        self.page_size_var = self._pagination.page_size_var
        
        # Create action buttons
        self._create_action_buttons()
        try:
            self._create_page_controls()
        except Exception:
            pass

    def _create_video_tree_styles(self):
        self.video_tree.column("Playlist", width=80, anchor="center")
        self.video_tree.column("Duration", width=100, anchor="center")
        self.video_tree.column("Published", width=120, anchor="center")
        self.video_tree.column("Views", width=90, anchor="center")
        self.video_tree.column("Status", width=120, anchor="center")
        self.video_tree.column("Actions", width=80, anchor="center")
        try:
            self.video_tree.tag_configure('pl_match', background='#d7ffd7')
        except Exception:
            pass
        try:
            self.video_tree.tag_configure('search_hit', background='#fff6bf')
        except Exception:
            pass
        self.video_tree.bind('<<TreeviewSelect>>', self.main_page.on_video_select)
        self.video_tree.bind("<Button-1>", self._on_video_click)
        self.video_tree.bind("<Double-1>", self._on_video_double)
        try:
            self._ctx = tk.Menu(self.video_tree, tearoff=0)
            self._ctx.add_command(label="Download This Video", command=lambda: self.main_page.download_single_video())
            self._ctx.add_command(label="Download Selected", command=lambda: self.main_page.download_selected_videos())
            self._ctx_idx_single = 0
            self._ctx_idx_multi = 1
            self._ctx.add_separator()
            self._ctx.add_command(label="Explore Downloaded", command=lambda: self.main_page.open_explore_downloaded_popup())
            self.video_tree.bind("<Button-3>", self._on_right_click)
        except Exception:
            pass
        self._tooltip = None
        self.video_tree.bind("<Motion>", self._on_motion)
        self.video_tree.bind("<Leave>", self._on_leave)

    def _create_page_controls(self):
        self._pagination.bind_prev(lambda: self.main_page.show_playlist_videos(page_token=self.main_page.prev_page_token))
        self._pagination.bind_next(lambda: self.main_page.show_playlist_videos(page_token=self.main_page.current_page_token))
        def _on_size(val):
            try:
                q = getattr(self.main_page, 'video_search_query', '')
            except Exception:
                q = ''
            try:
                if q:
                    self.main_page.execute_search_stable(q, 'Videos')
            except Exception:
                pass
        self._pagination.bind_page_size(lambda v: _on_size(v))

    def _create_action_buttons(self):
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=5)
        self.back_btn = ttk.Button(button_frame, text="Back to Results", command=self.main_page.back_to_video_results)
        self.back_btn.pack(side="left", padx=5)
        
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
        import os as _os
        _env = str(_os.getenv("APP_ENV", "")).strip().lower()
        if _env not in ("production", "prod", "release"):
            ttk.Button(button_frame, text="Build EXE", 
                      command=self.main_page.build_exe_windows).pack(side="left", padx=5)
        try:
            self.only_hits_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(button_frame, text="Show Only Hits", variable=self.only_hits_var, command=lambda: self.main_page.toggle_only_hits(self.only_hits_var.get())).pack(side="left", padx=8)
        except Exception:
            pass

    def update_back_button_state(self, enabled: bool):
        try:
            if enabled:
                self.back_btn["state"] = "normal"
            else:
                self.back_btn["state"] = "disabled"
        except Exception:
            pass
    def update_mode_ui(self, is_videos_mode: bool):
        try:
            self.configure(text=self._title_videos if is_videos_mode else self._title_playlist)
        except Exception:
            pass
    def show_scan(self, total: int):
        try:
            self._scan_total = max(int(total or 0), 1)
            self.main_page.show_mid_scan(self._scan_total)
        except Exception:
            pass
    def update_scan_progress(self, processed: int, total: int = None):
        try:
            self.main_page.update_mid_scan_progress(processed, total)
        except Exception:
            pass
    def finish_scan(self):
        try:
            self.main_page.finish_mid_scan()
        except Exception:
            pass

    def set_total_videos(self, count: int):
        try:
            self.total_label["text"] = f"Total: {int(count or 0)}"
        except Exception:
            pass
        try:
            self._panel.update_visibility(int(count or 0))
        except Exception:
            pass
    def _on_video_click(self, event):
        r = self.video_tree.identify_region(event.x, event.y)
        if r == 'heading':
            col = self.video_tree.identify_column(event.x)
            name_map = {"#1":"Title","#2":"Playlist","#3":"Channel","#4":"Duration","#5":"Published","#6":"Views","#7":"Status","#8":"Actions"}
            name = name_map.get(str(col))
            if name:
                self.main_page.sort_videos_by(name)
            return
        if r == 'cell':
            col = self.video_tree.identify_column(event.x)
            iid = self.video_tree.identify_row(event.y)
            if str(col) == "#8" and iid:
                try:
                    import tkinter.messagebox as messagebox
                    if messagebox.askyesno("Confirm Removal", "Remove this video from the list?"):
                        idx = self.video_tree.index(iid)
                        try:
                            if 0 <= idx < len(self.main_page.current_videos):
                                self.main_page.current_videos.pop(idx)
                        except Exception:
                            pass
                        self.video_tree.delete(iid)
                        return "break"
                except Exception:
                    pass

    def _on_video_double(self, event):
        r = self.video_tree.identify_region(event.x, event.y)
        if r == 'heading':
            col = self.video_tree.identify_column(event.x)
            name_map = {"#1":"Title","#2":"Playlist","#3":"Channel","#4":"Duration","#5":"Published","#6":"Views","#7":"Status","#8":"Actions"}
            name = name_map.get(str(col))
            if name:
                try:
                    import tkinter.simpledialog as simpledialog
                    q = simpledialog.askstring("Filter", f"Filter {name} contains:")
                    if q is not None:
                        self.main_page.on_video_header_double_click(name, q)
                except Exception:
                    pass
            return
        self.main_page.open_video(event)

    def _ensure_tooltip(self):
        if self._tooltip is None:
            self._tooltip = tk.Toplevel(self)
            self._tooltip.wm_overrideredirect(True)
            self._tooltip.withdraw()
            self._tooltip_label = ttk.Label(self._tooltip, background="#ffffe0", relief="solid", borderwidth=1)
            self._tooltip_label.pack(ipadx=4, ipady=2)

    def _show_tooltip(self, text, x, y):
        self._ensure_tooltip()
        try:
            self._tooltip_label.configure(text=text)
            self._tooltip.geometry(f"+{x+12}+{y+12}")
            self._tooltip.deiconify()
        except Exception:
            pass

    def _hide_tooltip(self):
        try:
            if self._tooltip:
                self._tooltip.withdraw()
        except Exception:
            pass

    def _on_motion(self, event):
        try:
            if self.video_tree.identify_region(event.x, event.y) == 'heading':
                self._hide_tooltip()
                return
            iid = self.video_tree.identify_row(event.y)
            if not iid:
                self._hide_tooltip()
                return
            idx = self.video_tree.index(iid)
            v = self.main_page.current_videos[idx] if idx < len(self.main_page.current_videos) else {}
            col = self.video_tree.identify_column(event.x)
            if str(col) == "#8":
                self._show_tooltip("Delete from list", event.x_root, event.y_root)
                return
            vid = v.get('videoId')
            pid = v.get('playlistId') or self.main_page.video_playlist_cache.get(vid)
            title = ''
            if pid and self.main_page.playlist.playlist_tree.exists(pid):
                try:
                    vals = self.main_page.playlist.playlist_tree.item(pid).get('values', [])
                    title = vals[1] if len(vals) > 1 else ''
                except Exception:
                    title = ''
            txt = f"{pid or ''} {title or ''}".strip()
            if txt:
                self._show_tooltip(txt, event.x_root, event.y_root)
            else:
                self._hide_tooltip()
        except Exception:
            pass

    def _on_leave(self, event):
        self._hide_tooltip()

    def _on_right_click(self, event):
        try:
            item = self.video_tree.identify_row(event.y)
            if item:
                try:
                    current = set(self.video_tree.selection())
                    if item not in current:
                        try:
                            self.video_tree.selection_add(item)
                        except Exception:
                            self.video_tree.selection_set(item)
                except Exception:
                    pass
                try:
                    sel_count = len(self.video_tree.selection())
                    if sel_count > 1:
                        self._ctx.entryconfigure(self._ctx_idx_single, state='disabled')
                        self._ctx.entryconfigure(self._ctx_idx_multi, state='normal')
                        try:
                            self._ctx.entryconfigure(self._ctx.index("Explore Downloaded"), state='normal')
                        except Exception:
                            pass
                    else:
                        self._ctx.entryconfigure(self._ctx_idx_single, state='normal')
                        self._ctx.entryconfigure(self._ctx_idx_multi, state='disabled')
                        try:
                            self._ctx.entryconfigure(self._ctx.index("Explore Downloaded"), state='disabled')
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    self._ctx.tk_popup(event.x_root, event.y_root)
                except Exception:
                    pass
        except Exception:
            pass
