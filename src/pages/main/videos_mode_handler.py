import threading
from tkinter import messagebox
from src.services.video_playlist_scanner import VideoPlaylistScanner
from src.services.results_mapper import build_index_map as _rm_build_index_map, rebuild_video_playlist_cache as _rm_rebuild_cache
from src.config_manager import ConfigManager

class VideosModeHandler:
    def __init__(self, main_page):
        self.parent = main_page
        self._videos_mode_click_busy = False
        self._pl_hits_cache = {}

    def highlight_videos_for_playlist(self, playlist_id):
        # Marks only intersection: videos in selected playlist AND present in current search results
        # Updates row values without changing mode; safe against UI restart
        try:
            if not playlist_id:
                return
            items = self.parent.video.video_tree.get_children()
            try:
                pi = self.parent.playlist_index_map.get(playlist_id)
                if pi is None:
                    try:
                        vals = self.parent.playlist.playlist_tree.item(playlist_id).get('values', [])
                        if vals:
                            n = vals[0]
                            try:
                                pi = int(str(n)) if n not in (None, "") else None
                            except Exception:
                                pi = None
                    except Exception:
                        pi = None
            except Exception:
                pi = None
            
            try:
                vids = set(self.parent.video_results_ids or set())
            except Exception:
                vids = set()

            # Use centralized PlaylistMatcher service
            try:
                def _fallback_fetch(pid, vid):
                    try:
                        return self.parent.controller.playlist_handler.playlist_contains_video(pid, vid)
                    except Exception:
                        return False

                hits = self.parent.playlist_matcher.get_intersection(
                    playlist_id=playlist_id,
                    current_video_ids=vids,
                    media_index=self.parent.media_index,
                    known_playlist_video_ids=getattr(self.parent, 'playlist_video_ids', {}), # Handle legacy attr if needed
                    fetch_fallback=_fallback_fetch,
                    current_videos_list=self.parent.current_videos
                )
            except Exception:
                hits = set()
        except Exception:
            pass
        try:
            for i, item in enumerate(items):
                try:
                    v = self.parent.current_videos[i] if i < len(self.parent.current_videos) else None
                    if not v:
                        continue
                    vid = v.get('videoId')
                    is_hit = bool(vid) and (vid in hits)
                    if is_hit:
                        try:
                            if self.parent.media_index:
                                self.parent.media_index.link_video_to_playlist(playlist_id, vid)
                            if pi is not None:
                                v['playlistIndex'] = pi
                        except Exception:
                            pass
                    row = self.parent._video_row(v)
                    if is_hit:
                        try:
                            row = (f"★ {row[0]}",) + row[1:]
                        except Exception:
                            pass
                    self.parent.video.video_tree.item(item, values=row, tags=('search_hit',) if is_hit else ())
                except Exception:
                    pass
        except Exception:
            pass
        try:
            self.parent._set_pinned_playlist(playlist_id)
        except Exception:
            pass
        try:
            self.parent.status_bar.configure(text="Highlighted videos for playlist")
        except Exception:
            pass
        try:
            self.parent._persist_playlist_caches_only()
        except Exception:
            pass
        try:
            vals = self.parent.playlist.playlist_tree.item(playlist_id).get('values', [])
            if vals:
                new_vals = (
                    vals[0] if len(vals)>0 else "",
                    vals[1] if len(vals)>1 else "",
                    vals[2] if len(vals)>2 else "",
                    vals[3] if len(vals)>3 else "",
                    f"Intersecting: {len(hits)}",
                    vals[5] if len(vals)>5 else "❌",
                )
                self.parent.playlist.playlist_tree.item(playlist_id, values=new_vals)
        except Exception:
            pass

    def on_videos_mode_playlist_click(self, playlist_id):
        try:
            if not playlist_id:
                return
            busy = bool(self._videos_mode_click_busy)
            if busy:
                try:
                    self.parent.status_bar.configure(text="Busy… please wait")
                except Exception:
                    pass
                return
            try:
                self._videos_mode_click_busy = True
            except Exception:
                pass
            try:
                self.parent._set_pinned_playlist(playlist_id)
            except Exception:
                pass
            try:
                self.parent.status_bar.configure(text="Loading playlist context…")
            except Exception:
                pass
            try:
                # Run highlight on UI thread
                self.parent.after(0, lambda pid=playlist_id: self.parent._safe_ui(lambda: self.highlight_videos_for_playlist(pid)))
            except Exception:
                try:
                    self.highlight_videos_for_playlist(playlist_id)
                except Exception:
                    pass
            try:
                # Defer printing so highlight appears quickly
                self.parent.after(50, lambda pid=playlist_id: self.parent.print_playlist_videos_to_terminal(pid))
            except Exception:
                pass
            try:
                self.parent.after(80, lambda pid=playlist_id: self._report_playlist_hits(pid))
            except Exception:
                pass
        except Exception:
            pass
        finally:
            try:
                self._videos_mode_click_busy = False
            except Exception:
                pass

    def _report_playlist_hits(self, playlist_id):
        try:
            vids = set(self.parent.video_results_ids or set())
        except Exception:
            vids = set()
        hits = 0
        try:
            # Use cached intersection from PlaylistMatcher
            # Since we likely just called highlight_videos_for_playlist, this should be fast
            res = self.parent.playlist_matcher.get_intersection(
                playlist_id=playlist_id,
                current_video_ids=vids,
                media_index=self.parent.media_index,
                known_playlist_video_ids=getattr(self.parent, 'playlist_video_ids', {}),
                fetch_fallback=None, # No fallback needed for reporting, should be already cached/loaded
                current_videos_list=self.parent.current_videos
            )
            hits = len(res)
        except Exception:
            hits = 0
        try:
            if hits <= 0:
                self.parent.status_bar.configure(text="No videos from this playlist in current results")
        except Exception:
            pass

    def _invalidate_hits_cache(self):
        try:
            if hasattr(self.parent, 'playlist_matcher'):
                self.parent.playlist_matcher.invalidate_cache()
            # Also clear local dict if it still exists (legacy safety)
            self._pl_hits_cache = {}
        except Exception:
            pass

    def _update_results_ids(self):
        try:
            self.parent.video_results_ids = {v.get('videoId') for v in list(self.parent.current_videos or []) if v.get('videoId')}
            self._invalidate_hits_cache()
        except Exception:
            self.parent.video_results_ids = set()

    def clear_video_playlist_highlights(self):
        # Removes all transient highlight/star tags from Videos table
        try:
            items = self.parent.video.video_tree.get_children()
            for i, item in enumerate(items):
                try:
                    v = self.parent.current_videos[i] if i < len(self.parent.current_videos) else None
                    if not v:
                        continue
                    row = self.parent._video_row(v)
                    self.parent.video.video_tree.item(item, values=row, tags=())
                except Exception:
                    pass
            try:
                self.parent.status_bar.configure(text="Cleared video highlights")
            except Exception:
                pass
        except Exception:
            pass

    def populate_videos_table_preview(self, playlist_id):
        # Renders selected playlist videos into Videos table without changing mode
        # Sets _preview_only_hits so stars/tags apply only to search result intersection
        try:
            vals = self.parent.playlist.playlist_tree.item(playlist_id).get('values', [])
        except Exception:
            vals = []
        try:
            ttl = vals[1] if len(vals) > 1 else ''
        except Exception:
            ttl = ''
        try:
            try:
                total_videos = int(vals[3])
            except Exception:
                try:
                    total_videos = int(self.parent.controller.playlist_handler.get_details(playlist_id))
                except Exception:
                    total_videos = 0
            try:
                cached = self.parent._get_cached_playlist_page(playlist_id, None)
            except Exception:
                cached = None
            if cached is not None:
                try:
                    self.parent.current_videos = list(cached.get('videos', []) or [])
                    self.parent.prev_page_token = cached.get('prevPageToken')
                    self.parent.current_page_token = cached.get('nextPageToken')
                except Exception:
                    pass
            else:
                try:
                    mr = int(self.parent.video.page_size_var.get())
                except Exception:
                    mr = 10
                try:
                    resp = self.parent.controller.playlist_handler.get_videos(playlist_id, None, max_results=mr)
                except Exception:
                    try:
                        resp = self.parent.controller.playlist_handler.get_videos(playlist_id, None, max_results=max(5, int(mr//2)))
                    except Exception:
                        resp = {'videos': [], 'nextPageToken': None, 'prevPageToken': None}
                try:
                    self.parent._cache_playlist_videos(playlist_id, None, resp)
                except Exception:
                    pass
                try:
                    self.parent.current_videos = list(resp.get('videos', []) or [])
                    self.parent.prev_page_token = resp.get('prevPageToken')
                    self.parent.current_page_token = resp.get('nextPageToken')
                except Exception:
                    pass
            try:
                pi = None
                try:
                    pi = self.parent.assign_playlist_index(playlist_id)
                except Exception:
                    pi = None
                for v in list(self.parent.current_videos or []):
                    try:
                        vid = v.get('videoId')
                        if vid and (vid in getattr(self.parent, 'video_search_ids', set())):
                            if self.parent.media_index:
                                self.parent.media_index.link_video_to_playlist(playlist_id, vid)
                        if pi is not None:
                            v['playlistIndex'] = pi
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                self.parent._preview_only_hits = True
                self.parent._preview_active = True
                try:
                    self.parent.playlist.playlist_tree.configure(selectmode='none')
                except Exception:
                    pass
            except Exception:
                pass
            try:
                self.parent._render_playlist_videos(total_videos)
            except Exception:
                pass
        except Exception:
            pass
        try:
            self.parent.video.update_back_button_state(True)
            self.parent.status_bar.configure(text=f"Preview: {ttl or playlist_id}")
        except Exception:
            pass
        try:
            self.parent._persist_playlist_caches_only()
        except Exception:
            pass

    def back_to_video_results(self):
        if self.parent.search_mode != 'videos':
            return
            
        data = self.parent._load_last_results_data()
        videos, playlists = self.parent._restore_search_state(data)
        
        # Restore UI State inline using shared populate method
        try:
            # Restore search entry
            q = data.get('query', '')
            try:
                self.parent.search.search_entry.delete(0, 'end')
                if q:
                    self.parent.search.search_entry.insert(0, q)
                self.parent.video_search_query = q
            except Exception:
                pass

            # Restore videos table
            self.parent.current_videos = videos
            # Update search IDs based on restored videos
            try:
                ids = data.get('videoIds') or []
                self.parent.video_search_ids = set([i for i in ids if i]) if ids else set([v.get('videoId') for v in videos if v.get('videoId')])
            except Exception:
                self.parent.video_search_ids = set()

            self._enrich_videos_with_metadata(videos)
            self.populate_video_table(videos, clear=True, apply_marks=True)
            
            # Restore playlists table
            self.parent.collected_playlists = playlists
            try:
                self.parent.playlist.playlist_tree.delete(*self.parent.playlist.playlist_tree.get_children())
                def _ins_pl_chunk(s=0):
                    try:
                        ch = 30
                        e = min(s + ch, len(playlists))
                        for i in range(s, e):
                            self.parent.playlist.update_playlist(playlists[i])
                        if e < len(playlists):
                            self.parent.after(10, lambda st=e: _ins_pl_chunk(st))
                    except Exception:
                        pass
                self.parent.after(0, _ins_pl_chunk)
            except Exception:
                pass
            
            # Restore pagination
            try:
                self.parent.video_next_page_token = data.get('nextPageToken')
                self.parent.video_prev_page_token = data.get('prevPageToken')
                self.parent.video_search_page_index = data.get('pageIndex', 1)
                
                self._update_pagination_state()
            except Exception:
                pass

            # Restore UI flags
            try:
                self.parent._preview_only_hits = False
                self.parent._preview_active = False
                try:
                    self.parent.playlist.playlist_tree.configure(selectmode='browse')
                except Exception:
                    pass
                self.parent.video.update_back_button_state(False)
                self.parent.status_bar.configure(text="Back to video results")
            except Exception:
                pass
                
        except Exception:
            pass
        
        try:
            if not self.parent.collected_playlists and self.parent.current_videos:
                self.parent._log("Re-triggering playlist collection for restored results")
                self.parent._async_recollect_playlists()
        except Exception:
            pass

    def _enrich_videos_with_metadata(self, videos):
        """
        Enriches the video list with playlistIndex metadata and links to MediaIndex.
        This ensures the 'Playlist' column in the video table is populated.
        """
        try:
            # Rebuild playlist index map from current collected playlists
            playlists = getattr(self.parent, 'collected_playlists', []) or []
            if not playlists:
                return

            # Rebuild index map if needed or ensure it's up to date
            # We use the existing map if available, or build new one
            index_map = getattr(self.parent, 'playlist_index_map', {})
            if not index_map:
                try:
                    # Build a simple map from collected playlists
                    # Format: {playlist_id: index}
                    # We assume collected_playlists are already in order or have indices
                    # But wait, main_page uses assign_playlist_index which is incremental.
                    # Let's try to recover indices from the UI tree if possible, or collected list.
                    
                    # Better approach: Use results_mapper logic if available, or simple iteration
                    index_map = {}
                    for i, pl in enumerate(playlists):
                         pid = pl.get('playlistId')
                         if pid:
                             # Try to get existing index from tree item if possible
                             try:
                                 item_vals = self.parent.playlist.playlist_tree.item(pid).get('values', [])
                                 if item_vals:
                                     idx = int(item_vals[0])
                                     index_map[pid] = idx
                                     continue
                             except Exception:
                                 pass
                             # Fallback to simple enumeration if not in tree
                             index_map[pid] = i + 1
                    self.parent.playlist_index_map = index_map
                except Exception:
                    pass

            # Now enrich videos
            # We need to know which video belongs to which playlist.
            # This requires checking MediaIndex or checking playlist contents.
            # If we don't have this info locally, we can't easily populate it without API calls.
            # However, MediaIndex should have been linked during search or load.
            
            if self.parent.media_index:
                # Add new videos to MediaIndex so they can be queried
                self.parent.media_index.add_videos(videos)
                
                # Check for intersections
                # For each video, check if it is in any of the collected playlists
                # This uses the MediaIndex cache
                
                # Reverse index map for lookup
                # actually we need to find which playlist contains the video
                
                for v in videos:
                    vid = v.get('videoId')
                    if not vid:
                        continue
                        
                    # Check if this video is in any known playlist
                    # We iterate over known playlists in the map
                    found_pid = None
                    for pid, idx in index_map.items():
                        # Check if linked in MediaIndex
                        # MediaIndex.is_video_in_playlist might be expensive if not cached
                        # But MediaIndex is optimized for this.
                        try:
                            if self.parent.media_index.is_video_in_playlist(pid, vid):
                                found_pid = pid
                                v['playlistIndex'] = idx
                                break
                        except Exception:
                            pass
                    
                    # If found, ensure link is reinforced
                    if found_pid:
                        try:
                            self.parent.media_index.link_video_to_playlist(found_pid, vid)
                        except Exception:
                            pass

        except Exception:
            pass

    def populate_video_table(self, videos, clear=True, apply_marks=True):
        try:
            if clear:
                self.parent.video.video_tree.delete(*self.parent.video.video_tree.get_children())
        except Exception:
            pass

        try:
            vs = getattr(self.parent, 'video_search_ids', set())
            preview_only = getattr(self.parent, '_preview_only_hits', False)
            ql = (getattr(self.parent, 'video_search_query', '') or '').strip().lower()

            def _ins_chunk(s=0):
                try:
                    ch = 50
                    e = min(s + ch, len(videos))
                    for i in range(s, e):
                        v = videos[i]
                        try:
                            vid = v.get('videoId')
                            tags = []
                            if apply_marks:
                                if preview_only:
                                    is_hit = bool(vid) and (vid in vs)
                                else:
                                    # Standard search mode logic
                                    # "Search hit" tag is generic for result presence
                                    is_hit = bool(vid) and (vid in vs)
                                
                                if is_hit:
                                    tags.append('search_hit')
                            
                            # Check for transient highlight (Star)
                            # The highlight_videos_for_playlist logic modifies the row value directly (adding ★)
                            # But if we are repopulating, we might lose it if we don't re-apply.
                            # We should rely on the caller to re-trigger highlight_videos_for_playlist
                            # OR we can check if there's a pinned playlist and current video intersects.
                            
                            row = self.parent._video_row(v)
                            
                            # Inline highlight check if pinned playlist exists
                            # This fixes "lost marks on pagination"
                            pinned = getattr(self.parent, 'pinned_playlist_id', None)
                            if pinned and not preview_only and apply_marks:
                                # Check intersection
                                try:
                                    # Use cached intersection logic if possible or quick check
                                    # But highlight_videos_for_playlist is the robust way.
                                    # We can just apply the star if we know it intersects
                                    if self.parent.media_index and self.parent.media_index.is_video_in_playlist(pinned, vid):
                                        row = (f"★ {row[0]}",) + row[1:]
                                        tags.append('search_hit')
                                except Exception:
                                    pass

                            self.parent.video.video_tree.insert('', 'end', values=row, tags=tuple(tags))
                        except Exception:
                            self.parent.video.video_tree.insert('', 'end', values=self.parent._video_row(v))
                    if e < len(videos):
                        self.parent.after(0, lambda st=e: _ins_chunk(st))
                except Exception:
                    pass
            _ins_chunk(0)
        except Exception:
            pass

    def load_last_search(self):
        try:
            self.parent.video._panel.pagination.set_visible(False)
        except Exception:
            pass
        path = ConfigManager.get_last_search_path('videos')
        data = ConfigManager.load_json(path) or {}
        videos = data.get('videos', [])
        playlists = data.get('playlists', [])
        q = data.get('query', '')
        video_prev = data.get('prevPageToken')
        video_next = data.get('nextPageToken')
        ids = data.get('videoIds') or []
        video_ids = set([i for i in ids if i])
        pinned_pl_id = data.get('pinnedPlaylistId')
        total_results = data.get('totalResults')
        
        # Load cached playlist mappings
        try:
            pl_ids_map = data.get('playlistIds') or {}
            if self.parent.media_index:
                for k, v in pl_ids_map.items():
                    try:
                        self.parent.media_index.bulk_link_playlist_videos(k, list(v or []))
                    except Exception:
                        pass
        except Exception:
            pass

        try:
            self.parent.playlist_videos_cache = data.get('playlistPages') or {}
        except Exception:
            self.parent.playlist_videos_cache = {}

        try:
            self.parent.search.search_entry.delete(0, 'end')
            if q:
                self.parent.search.search_entry.insert(0, q)
            self.parent.video_search_query = q or getattr(self.parent, 'video_search_query', '')
        except Exception:
            pass

        try:
            self.parent.video_prev_page_token = video_prev
            self.parent.video_next_page_token = video_next
            self.parent.video_search_ids = video_ids
            self.parent.video_total_results = total_results
        except Exception:
            pass

        try:
            # Populate videos and playlists
            self.parent.current_videos = videos
            self.parent.collected_playlists = playlists
            
            # Enrich videos with playlist metadata BEFORE populating
            self._enrich_videos_with_metadata(videos)
            
            # Use new populate method
            self.populate_video_table(videos, clear=True, apply_marks=True)
            
            self.parent.playlist.playlist_tree.delete(*self.parent.playlist.playlist_tree.get_children())
            def _ins_pl_chunk(s=0):
                try:
                    ch = 30
                    e = min(s + ch, len(playlists))
                    for i in range(s, e):
                        self.parent.playlist.update_playlist(playlists[i])
                    if e < len(playlists):
                        self.parent.after(10, lambda st=e: _ins_pl_chunk(st))
                except Exception:
                    pass
            self.parent.after(0, _ins_pl_chunk)
        except Exception:
            pass

        try:
            self.parent.video.update_back_button_state(False)
        except Exception:
            pass
        try:
            self.parent.video.prev_page_btn.configure(command=lambda: self.show_videos_search_page(getattr(self.parent, 'video_prev_page_token', None), direction='prev'))
            self.parent.video.next_page_btn.configure(command=lambda: self.show_videos_search_page(getattr(self.parent, 'video_next_page_token', None), direction='next'))
            
            self._update_pagination_state()
        except Exception:
            pass

        if pinned_pl_id:
            try:
                # Defer to ensure UI is ready
                self.parent.after(500, lambda: self.on_videos_mode_playlist_click(pinned_pl_id))
            except Exception:
                pass

    def _update_pagination_state(self):
        try:
            has_prev = bool(getattr(self.parent, 'video_prev_page_token', None))
            has_next = bool(getattr(self.parent, 'video_next_page_token', None))
            self.parent.video.prev_page_btn["state"] = "normal" if has_prev else "disabled"
            self.parent.video.next_page_btn["state"] = "normal" if has_next else "disabled"
            
            try:
                idx = int(getattr(self.parent, 'video_search_page_index', 1) or 1)
            except Exception:
                idx = 1
            try:
                ps = int(self.parent.video.page_size_var.get())
            except Exception:
                ps = 10
            
            try:
                total_res = getattr(self.parent, 'video_total_results', None)
                if total_res is not None:
                    est_total = int(total_res)
                else:
                    est_total = ps * idx + (ps if has_next else 0)
            except Exception:
                est_total = len(self.parent.current_videos or [])

            try:
                self.parent.video._panel.update_pages(index=idx, has_prev=has_prev, has_next=has_next, total_items=est_total)
            except Exception:
                pass
        except Exception:
            pass

    def show_videos_search_page(self, page_token=None, direction=None):
        if self.parent.search_mode != 'videos' or not self.parent.video_search_query:
            return
        try:
            self.parent.controller.ensure_playlist_handler()
        except Exception:
            pass
        try:
            prev_before = getattr(self.parent, 'video_prev_page_token', None)
            next_before = getattr(self.parent, 'video_next_page_token', None)
            max_results = int(self.parent.video.page_size_var.get())
            try:
                resp = self.parent.controller.playlist_handler.search_videos(self.parent.video_search_query, max_results=max_results, page_token=page_token)
            except Exception as e:
                try:
                    self.parent.status_bar.configure(text="API quota/error — loading last saved page")
                except Exception:
                    pass
                try:
                    path = ConfigManager.get_last_search_path('videos')
                    data = ConfigManager.load_json(path) or {}
                    videos = data.get('videos', [])
                    self.parent.current_videos = videos
                    self.parent.video_next_page_token = data.get('nextPageToken')
                    self.parent.video_prev_page_token = data.get('prevPageToken')
                    self.parent.video_search_ids = set([v.get('videoId') for v in videos if v.get('videoId')])
                    self.parent.video_total_results = data.get('totalResults')
                    
                    self.populate_video_table(videos, clear=True, apply_marks=True)
                    return
                except Exception:
                    messagebox.showerror("Error", f"Failed to fetch videos page: {e}")
                    return
            videos = resp.get('videos', [])
            self.parent.current_videos = videos
            self.parent.video_next_page_token = resp.get('nextPageToken')
            self.parent.video_prev_page_token = resp.get('prevPageToken')
            self.parent.video_total_results = resp.get('totalResults')
            
            self.parent.video_search_ids = set([v.get('videoId') for v in videos if v.get('videoId')])
            self.parent.video_total_results = resp.get('totalResults')
            
            # Enrich and Populate
            self._enrich_videos_with_metadata(videos)
            self.populate_video_table(videos, clear=True, apply_marks=True)

            try:
                self._update_results_ids()
            except Exception:
                pass
            try:
                if page_token is None:
                    # Reset page index for new searches
                    self.parent.video_search_page_index = 1
                elif page_token == next_before:
                    self.parent.video_search_page_index = int(getattr(self.parent, 'video_search_page_index', 1) or 1) + 1
                elif page_token == prev_before:
                    self.parent.video_search_page_index = max(1, int(getattr(self.parent, 'video_search_page_index', 1) or 1) - 1)
                
                # Update page indicator manually if needed, but pagination bar handles it
                # self.parent.video.page_indicator["text"] = f"Results page {int(getattr(self.parent, 'video_search_page_index', 1) or 1)}"
            except Exception:
                pass
            
            self._update_pagination_state()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch videos: {e}")
