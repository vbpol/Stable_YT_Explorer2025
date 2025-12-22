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
                        vals = self.parent.playlist.get_playlist_values(playlist_id) or []
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
            vals = list(self.parent.playlist.get_playlist_values(playlist_id) or [])
            if vals:
                new_vals = (
                    vals[0] if len(vals)>0 else "",
                    vals[1] if len(vals)>1 else "",
                    vals[2] if len(vals)>2 else "",
                    vals[3] if len(vals)>3 else "",
                    f"Intersecting: {len(hits)}",
                    vals[5] if len(vals)>5 else "❌",
                )
                self.parent.playlist.update_playlist_item(playlist_id, tuple(new_vals))
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
            vals = self.parent.playlist.get_playlist_values(playlist_id) or []
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
                    self.parent.playlist.set_selection_mode('none')
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
                self.parent.playlist.clear_playlists()
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
                    self.parent.playlist.set_selection_mode('browse')
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
            # We must use the full collected list, not just what's in the UI tree (which might be paginated)
            playlists = getattr(self.parent, 'collected_playlists', []) or []
            
            # Rebuild index map if needed or ensure it's up to date
            index_map = getattr(self.parent, 'playlist_index_map', {})
            
            # Always rebuild map from source of truth (collected_playlists) to ensure consistency
            if playlists:
                index_map = {}
                for i, pl in enumerate(playlists):
                    pid = pl.get('playlistId')
                    if pid:
                         # Use persisted sequence number if available (Best Source)
                         seq = pl.get('sequence_number')
                         if seq:
                             try:
                                 index_map[pid] = int(seq)
                                 continue
                             except Exception:
                                 pass
                         
                         # Fallback to simple enumeration
                         index_map[pid] = i + 1
                self.parent.playlist_index_map = index_map

            # Now enrich videos
            if self.parent.media_index:
                # Add new videos to MediaIndex so they can be queried
                self.parent.media_index.add_videos(videos)
                
                # Check for intersections using MediaIndex
                for v in videos:
                    vid = v.get('videoId')
                    if not vid:
                        continue
                        
                    # 1. Check if MediaIndex already knows the playlist for this video
                    # This is O(1)
                    found_pid = self.parent.media_index.get_video_playlist(vid)
                    
                    if found_pid and found_pid in index_map:
                        v['playlistIndex'] = index_map[found_pid]
                    # No fallback iteration needed as MediaIndex is SSOT for linked videos

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
                                    is_hit = bool(vid) and (vid in vs)
                                
                                if is_hit:
                                    tags.append('search_hit')
                            
                            row = self.parent._video_row(v)
                            
                            # Inline highlight check if pinned playlist exists
                            pinned = getattr(self.parent, 'pinned_playlist_id', None)
                            if pinned and not preview_only and apply_marks:
                                try:
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

    def load_last_search_data(self):
        """
        Loads the last search data from disk.
        Safe to run in a background thread (no UI calls).
        """
        try:
            path = ConfigManager.get_last_search_path('videos')
            data = ConfigManager.load_json(path) or {}
            return data
        except Exception:
            return {}

    def populate_from_last_search(self, data):
        """
        Populates the UI with the loaded search data.
        MUST be run on the main thread.
        """
        try:
            self.parent.video._panel.pagination.set_visible(False)
        except Exception:
            pass

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
            # Note: access to parent.playlist_index_map happens here.
            # Since this method is on main thread, it is safe.
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

    def load_last_search(self):
        """Legacy method: Loads and populates on current thread (blocking if main)."""
        data = self.load_last_search_data()
        self.populate_from_last_search(data)

    def _update_pagination_state(self):
        try:
            mode = 'videos' if getattr(self.parent, 'search_mode', '') == 'videos' else 'playlists'
            try:
                self.parent.video._pagination.set_mode(mode)
            except Exception:
                pass
            
            # CRITICAL: If we are in 'playlists' mode, pagination is handled by main_page.show_playlist_videos
            # via API tokens. We MUST NOT overwrite it with local slicing logic based on current_videos count.
            if mode != 'videos':
                return
        except Exception:
            pass
        
        try:
            # Use local slicing for pagination (Search Results only)
            videos = getattr(self.parent, 'current_videos', []) or []
            total_loaded = len(videos)
            
            try:
                ps = int(self.parent.video.page_size_var.get())
            except Exception:
                ps = 10
            
            # Calculate total pages
            import math
            total_pages = math.ceil(total_loaded / ps) if ps > 0 else 1
            
            try:
                idx = int(getattr(self.parent, 'video_search_page_index', 1) or 1)
            except Exception:
                idx = 1
                
            # Bound check
            if idx < 1: idx = 1
            if idx > total_pages: idx = total_pages
            self.parent.video_search_page_index = idx

            has_prev = (idx > 1)
            has_next = (idx < total_pages)
            
            # Use unified pagination update
            try:
                self.parent.video.update_pagination(idx, total_loaded, has_prev=has_prev, has_next=has_next)
            except Exception:
                pass
            
            try:
                # Show global total but emphasize loaded subset
                total_res = getattr(self.parent, 'video_total_results', None)
                if total_res is not None:
                    # e.g. "Total: 1,000,000 (Loaded 40)"
                    est_total = f"Total: {int(total_res):,} (Loaded {total_loaded})"
                else:
                    est_total = f"Total: {total_loaded}"
                
                # Direct update to label to support custom text format
                self.parent.video._panel.pagination.set_total_text(est_total)
            except Exception:
                pass
        except Exception:
            pass

    def show_videos_search_page(self, page_token=None, direction=None):
        """
        Actually renders the current page slice from self.parent.current_videos.
        Does NOT fetch from API unless explicitly needed (which we moved to main_page search).
        """
        if self.parent.search_mode != 'videos':
            return

        try:
            # Check pagination toggle
            try:
                use_pagination = self.parent.search.pagination_var.get()
            except Exception:
                use_pagination = True

            # 1. Determine new page index
            try:
                current_idx = int(getattr(self.parent, 'video_search_page_index', 1) or 1)
            except Exception:
                current_idx = 1
                
            if direction == 'next':
                current_idx += 1
            elif direction == 'prev':
                current_idx = max(1, current_idx - 1)
            elif direction == 'reset':
                current_idx = 1
            
            # 2. Update page size and slice
            try:
                ps = int(self.parent.video.page_size_var.get())
            except Exception:
                ps = 10
                
            videos = getattr(self.parent, 'current_videos', []) or []
            
            # Ensure sorting is consistent BEFORE slicing
            # Sort by playlist index to keep groups together
            try:
                 # Helper to get sort key safely
                def _sort_key(v):
                    try:
                        # Use enriched playlistIndex if available, else huge number
                        idx = v.get('playlistIndex')
                        if idx in (None, ''):
                            return 999999
                        return int(idx)
                    except Exception:
                        return 999999
                
                videos.sort(key=_sort_key)
            except Exception:
                pass

            total = len(videos)
            
            if use_pagination:
                # Bound check
                import math
                total_pages = math.ceil(total / ps) if ps > 0 else 1
                if current_idx > total_pages: current_idx = total_pages
                if current_idx < 1: current_idx = 1
                
                self.parent.video_search_page_index = current_idx
                
                # Slice
                start = (current_idx - 1) * ps
                end = start + ps
                page_videos = videos[start:end]
            else:
                # No pagination: show all
                self.parent.video_search_page_index = 1
                page_videos = videos

            # 3. Populate
            self.populate_video_table(page_videos, clear=True, apply_marks=True)
            
            # 4. Update Pagination UI
            self._update_pagination_state()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to render video page: {e}")
