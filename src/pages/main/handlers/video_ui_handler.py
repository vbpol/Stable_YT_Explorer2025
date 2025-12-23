import tkinter as tk
from tkinter import messagebox
from typing import Dict, Any, List, Optional, Set
from src.logger import logger

class VideoUIHandler:
    """
    Handles video-related UI logic for the MainPage.
    Responsible for rendering the video table, row formatting, highlighting,
    and previewing playlist videos.
    """

    def __init__(self, main_page):
        self.main_page = main_page
        self.video_section = main_page.video
        self.controller = main_page.controller

    def _fmt_date(self, s):
        try:
            from datetime import datetime
            dt = datetime.fromisoformat((s or '').replace('Z', '+00:00'))
            return dt.strftime('%y-%m-%d-%H')
        except Exception:
            return (s or '')[:10]

    def _video_row(self, video: Dict[str, Any]) -> tuple:
        """Format a video dictionary into a tuple for the TreeView."""
        try:
            vid = video.get('videoId')
            plid = self.main_page.video_playlist_cache.get(vid)
            idx = ''
            if plid:
                idx = self.main_page.playlist_index_map.get(plid, '')
            elif video.get('playlistIndex'):
                idx = video.get('playlistIndex')
                
            status = self._video_download_status(video)
            
            # Format views
            views = video.get('views', '0')
            try:
                if str(views).isdigit():
                    views = f"{int(views):,}"
            except Exception:
                pass
                
            return (
                video.get('title', 'Unknown'),
                str(idx) if idx else "",
                video.get('channelTitle', 'Unknown'),
                video.get('duration', 'N/A'),
                self._fmt_date(video.get('published', '')),
                views,
                status,
                "🗑"
            )
        except Exception as e:
            logger.error(f"Error formatting video row: {e}")
            return ("Error", "", "", "", "", "", "", "")

    def render_videos(self, videos: List[Dict[str, Any]], search_ids: Set[str] = None, highlight_query: str = None):
        """Render a list of videos to the video table."""
        try:
            self.video_section.video_tree.delete(*self.video_section.video_tree.get_children())
            
            if videos is None:
                videos = []
                
            search_ids = search_ids or set()
            highlight_query = (highlight_query or '').strip().lower()
            
            # Use chunked insertion to avoid freezing UI
            def _ins_chunk(s):
                try:
                    ch = 50
                    e = min(s + ch, len(videos))
                    for i in range(s, e):
                        video = videos[i]
                        try:
                            vid = video.get('videoId')
                            ttl = str(video.get('title', '')).lower()
                            chn = str(video.get('channelTitle', '')).lower()
                            
                            is_hit = False
                            if getattr(self.main_page, '_preview_only_hits', False):
                                is_hit = bool(vid) and (vid in search_ids)
                            else:
                                is_hit = (bool(vid) and (vid in search_ids)) or \
                                         (highlight_query and (highlight_query in ttl or highlight_query in chn))
                            
                            tags = ('search_hit',) if is_hit else ()
                            row = self._video_row(video)
                            
                            if is_hit:
                                try:
                                    row = (f"★ {row[0]}",) + row[1:]
                                except Exception:
                                    pass
                                    
                            self.video_section.video_tree.insert('', 'end', values=row, tags=tags)
                        except Exception:
                            self.video_section.video_tree.insert('', 'end', values=self._video_row(video))
                            
                    if e < len(videos):
                        self.main_page.after(0, lambda st=e: _ins_chunk(st))
                except Exception as e:
                    logger.error(f"Error rendering video chunk: {e}")

            _ins_chunk(0)
            
        except Exception as e:
            logger.error(f"Error rendering videos: {e}")

    def populate_videos_table_preview(self, playlist_id: str):
        """
        Renders selected playlist videos into Videos table without changing mode.
        CRITICAL: This method must NOT save state to StateManager.
        """
        try:
            # 1. Get playlist details
            try:
                vals = self.main_page.playlist.playlist_tree.item(playlist_id).get('values', [])
                ttl = vals[1] if len(vals) > 1 else ''
                total_videos = int(vals[3]) if len(vals) > 3 else 0
            except Exception:
                ttl = ''
                total_videos = 0

            # 2. Fetch videos (Cache -> API -> Fallback)
            videos = []
            cached = self.main_page._get_cached_playlist_page(playlist_id, None)
            
            if cached:
                videos = list(cached.get('videos', []) or [])
                self.main_page.prev_page_token = cached.get('prevPageToken')
                self.main_page.current_page_token = cached.get('nextPageToken')
            else:
                try:
                    mr = int(self.video_section.page_size_var.get())
                except Exception:
                    mr = 10
                    
                try:
                    resp = self.controller.playlist_handler.get_videos(playlist_id, None, max_results=mr)
                except Exception:
                    # Fallback with fewer results
                    try:
                        resp = self.controller.playlist_handler.get_videos(playlist_id, None, max_results=max(5, int(mr//2)))
                    except Exception:
                        resp = {'videos': [], 'nextPageToken': None, 'prevPageToken': None}
                
                videos = resp.get('videos', [])
                self.main_page._cache_playlist_videos(playlist_id, None, resp)

            # 3. Update MainPage state (Transient)
            self.main_page.current_videos = videos or []
            
            # 4. Map playlist indices
            try:
                pi = self.main_page.assign_playlist_index(playlist_id)
                for v in self.main_page.current_videos:
                    try:
                        vid = v.get('videoId')
                        if vid and (vid in getattr(self.main_page, 'video_search_ids', set())):
                            self.main_page.video_playlist_cache[vid] = playlist_id
                        if pi is not None:
                            v['playlistIndex'] = pi
                    except Exception:
                        pass
            except Exception:
                pass

            # 5. UI Updates
            self.main_page._preview_only_hits = True
            self.main_page._preview_active = True
            try:
                self.main_page.playlist.playlist_tree.configure(selectmode='none')
            except Exception:
                pass

            self.render_videos(
                self.main_page.current_videos, 
                getattr(self.main_page, 'video_search_ids', set()),
                getattr(self.main_page, 'video_search_query', '')
            )
            
            self.video_section.update_back_button_state(True)
            self.main_page.status_bar.configure(text=f"Preview: {ttl or playlist_id}")

        except Exception as e:
            logger.error(f"Error in populate_videos_table_preview: {e}")
            messagebox.showerror("Error", f"Failed to preview playlist: {e}")
    def _video_download_status(self, v):
        try:
            folder = self._video_target_folder(v)
            try:
                import os
                os.makedirs(folder, exist_ok=True)
            except Exception:
                pass
            fp = self._find_downloaded_file(folder, v.get('title',''), v.get('videoId'))
            return "Downloaded" if fp else "Not Downloaded"
        except Exception:
            return "Unknown"

    def _video_target_folder(self, v):
        try:
            import os
            if getattr(self.main_page, 'download_folder', None):
                return self.main_page.download_folder
            vid = v.get('videoId')
            pid = v.get('playlistId') or self.main_page.video_playlist_cache.get(vid)
            
            if pid:
                try:
                    ttl = ''
                    if self.main_page.playlist.playlist_tree.exists(pid):
                        vals = self.main_page.playlist.playlist_tree.item(pid).get('values', [])
                        ttl = vals[1] if len(vals) > 1 else ''
                    return os.path.join(self.controller.default_folder, ttl or 'Unknown Playlist')
                except Exception:
                    pass
            
            # Fallback
            ct = str(v.get('channelTitle','')).strip()
            if ct:
                return os.path.join(self.controller.default_folder, ct)
            return os.path.join(self.controller.default_folder, getattr(self.main_page, 'video_search_query', '') or 'Misc')
        except Exception:
            return self.controller.default_folder

    def _find_downloaded_file(self, folder, title, video_id):
        try:
            import os
            if not os.path.exists(folder):
                return None
            files = os.listdir(folder)
            # Try exact match with video_id in name
            if video_id:
                for f in files:
                    if video_id in f:
                        return os.path.join(folder, f)
            # Try title match
            clean_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()
            if clean_title:
                for f in files:
                    if clean_title in f:
                        return os.path.join(folder, f)
            return None
        except Exception:
            return None

    def update_video_row_by_vid(self, video_id: str, playlist_id: str):
        """Update a specific video row in the TreeView by video ID."""
        try:
            # 1. Update cache
            self.main_page.video_playlist_cache[video_id] = playlist_id
            
            # 2. Find row in tree
            items = self.video_section.video_tree.get_children()
            for item in items:
                vals = self.video_section.video_tree.item(item).get('values', [])
                # We need a way to reliably identify the video from tree values.
                # Usually we store the video object or index. 
                # MainPage used to look at current_videos.
                pass
                
            # Efficient update if we know the index
            for i, v in enumerate(list(self.main_page.current_videos or [])):
                if v.get('videoId') == video_id:
                    v['playlistId'] = playlist_id
                    pi = self.main_page.assign_playlist_index(playlist_id)
                    v['playlistIndex'] = pi
                    if i < len(items):
                        self.main_page._safe_ui(lambda it=items[i], r=self._video_row(v): 
                            self.video_section.video_tree.item(it, values=r))
        except Exception as e:
            logger.error(f"Error updating video row by vid: {e}")

    def toggle_only_hits(self, enabled: bool):
        """Toggle preview of only search hits."""
        try:
            self.main_page._preview_only_hits = bool(enabled)
            # Re-render with current state
            self.render_videos(
                self.main_page.current_videos,
                getattr(self.main_page, 'video_search_ids', set()),
                getattr(self.main_page, 'video_search_query', '')
            )
        except Exception as e:
            logger.error(f"Error in toggle_only_hits: {e}")

    def update_results_ids(self):
        """Update the set of video IDs currently being displayed."""
        try:
            mp = self.main_page
            mp.video_results_ids = {v.get('videoId') for v in list(mp.current_videos or []) if v.get('videoId')}
            self._invalidate_hits_cache()
        except Exception as e:
            logger.error(f"Error updating results IDs: {e}")
            self.main_page.video_results_ids = set()

    def _invalidate_hits_cache(self):
        try:
            self.main_page._pl_hits_cache = {}
        except Exception:
            pass

    def clear_video_playlist_highlights(self):
        """Removes all transient highlight/star tags from Videos table."""
        try:
            items = self.video_section.video_tree.get_children()
            videos = list(self.main_page.current_videos or [])
            for i, item in enumerate(items):
                try:
                    v = videos[i] if i < len(videos) else None
                    if not v:
                        continue
                    row = self._video_row(v)
                    self.video_section.video_tree.item(item, values=row, tags=())
                except Exception:
                    pass
            self.main_page.status_bar.configure(text="Cleared video highlights")
        except Exception as e:
            logger.error(f"Error clearing highlights: {e}")
    def show_playlist_listing_popup(self, playlist_id: str, videos: List[Dict[str, Any]]):
        """Popup window showing playlist number and each video title."""
        try:
            import tkinter as tk
            from tkinter import ttk
            
            mp = self.main_page
            win = tk.Toplevel(mp)
            
            # 1. Get playlist title
            try:
                vals = mp.playlist.playlist_tree.item(playlist_id).get('values', [])
                ttl = vals[1] if len(vals) > 1 else ''
            except Exception:
                ttl = ''
                
            win.title(f"Playlist Listing: {ttl or playlist_id}")
            
            frm = ttk.Frame(win)
            frm.pack(fill="both", expand=True)
            
            tv = ttk.Treeview(frm, columns=("Playlist","Title"), show="headings", selectmode="none")
            tv.heading("Playlist", text="Playlist")
            tv.heading("Title", text="Title")
            tv.column("Playlist", width=80, anchor="center")
            tv.column("Title", width=520, anchor="w")
            
            try:
                tv.tag_configure('search_hit', background='#fff6bf')
            except Exception: pass
            
            scr = ttk.Scrollbar(frm, orient="vertical", command=tv.yview)
            tv.configure(yscrollcommand=scr.set)
            
            tv.pack(side="left", fill="both", expand=True)
            scr.pack(side="right", fill="y")
            
            # 2. Assign index
            try:
                pi = mp.assign_playlist_index(playlist_id)
            except Exception:
                pi = ''
            
            # 3. Insert items
            search_ids = getattr(mp, 'video_search_ids', set())
            for v in list(videos or []):
                vid = v.get('videoId')
                hit = bool(vid) and (vid in search_ids)
                title = v.get('title','')
                if hit:
                    title = f"★ {title}"
                tv.insert('', 'end', values=(pi, title), tags=('search_hit',) if hit else ())
                
            win.geometry("700x420")
        except Exception as e:
            logger.error(f"Error showing playlist listing popup: {e}")

    def refresh_video_statuses(self):
        """Refresh download status for all videos currently in the table."""
        try:
            mp = self.main_page
            items = list(self.video_section.video_tree.get_children())
            for i, iid in enumerate(items):
                try:
                    v = mp.current_videos[i] if i < len(mp.current_videos) else None
                    if not v:
                        continue
                    self.video_section.video_tree.item(iid, values=self._video_row(v))
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Error refreshing video statuses: {e}")

    def sort_videos_by(self, column_name: str):
        """Sort the current videos list and update the tree."""
        try:
            col_map = {
                "Title": (lambda v: str(v.get('title', '')).lower()),
                "Playlist": (lambda v: int(v.get('playlistIndex') or 0)),
                "Channel": (lambda v: str(v.get('channelTitle', '')).lower()),
                "Duration": (lambda v: str(v.get('duration', ''))),
                "Published": (lambda v: v.get('published', '')),
                "Views": (lambda v: int(v.get('views') or 0)),
                "Status": (lambda v: (2 if self._video_download_status(v) == 'Downloaded' else (1 if self._video_download_status(v) == 'Not Downloaded' else 0)))
            }
            keyfunc = col_map.get(column_name)
            if not keyfunc:
                return
            
            asc = self.main_page.video_sort_state.get(column_name, False)
            try:
                self.main_page.current_videos.sort(key=keyfunc, reverse=not asc)
            except Exception:
                try:
                    self.main_page.current_videos.sort(key=lambda v: str(keyfunc(v)), reverse=not asc)
                except Exception:
                    return
            
            self.main_page.video_sort_state[column_name] = not asc
            self.render_videos(
                self.main_page.current_videos,
                getattr(self.main_page, 'video_search_ids', set()),
                getattr(self.main_page, 'video_search_query', '')
            )
        except Exception as e:
            logger.error(f"Error sorting videos by {column_name}: {e}")

    def on_video_header_double_click(self, column_name: str, q=None):
        """Filter videos by a specific column."""
        try:
            import tkinter.simpledialog as simpledialog
            col_map = {
                "Title": "title",
                "Channel": "channelTitle",
                "Duration": "duration",
                "Published": "published",
                "Views": "views"
            }
            key = col_map.get(column_name)
            if not key:
                return
            
            if q is None:
                q = simpledialog.askstring("Filter", f"Filter {column_name} contains:")
            if q is None:
                return
                
            ql = (q or '').strip().lower()
            filtered = []
            for v in self.main_page.current_videos:
                val = str(v.get(key, ""))
                if ql in val.lower():
                    filtered.append(v)
            
            self.render_videos(
                filtered,
                getattr(self.main_page, 'video_search_ids', set()),
                getattr(self.main_page, 'video_search_query', '')
            )
        except Exception as e:
            logger.error(f"Error filtering videos by {column_name}: {e}")
