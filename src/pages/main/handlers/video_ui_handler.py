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

    def _video_row(self, video: Dict[str, Any]) -> tuple:
        """Format a video dictionary into a tuple for the TreeView."""
        try:
            status = self.main_page._video_download_status(video)
            idx = video.get('playlistIndex')
            
            # Format duration
            dur = str(video.get('duration', ''))
            if dur.startswith('PT'):
                dur = dur[2:].lower()
            
            # Format published date
            pub = str(video.get('published', ''))
            if 'T' in pub:
                pub = pub.split('T')[0]
            
            return (
                str(idx) if idx is not None else "",
                video.get('title', 'Unknown'),
                video.get('channelTitle', 'Unknown'),
                dur,
                pub,
                str(video.get('views', '0')),
                status
            )
        except Exception as e:
            logger.error(f"Error formatting video row: {e}")
            return ("", "Error", "", "", "", "", "")

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
