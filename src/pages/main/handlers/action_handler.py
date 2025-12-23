import os
import sys
import subprocess
import csv
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Dict, Any, List, Optional
from src.logger import logger
from src.config_manager import ConfigManager

class ActionHandler:
    """
    Coordinates complex actions in the MainPage, such as search execution,
    pagination, and data fetching.
    """

    def __init__(self, main_page):
        self.main_page = main_page
        self.controller = main_page.controller
        self.video_section = main_page.video
        self.current_playlist_info = None

    def execute_search(self, query: str, mode_display: str):
        """Orchestrate search for both videos and playlists."""
        query = (query or '').strip()
        if not query:
            return

        mode = (mode_display or '').strip().lower()
        if mode not in ('playlists', 'videos'):
            mode = 'playlists'
            
        mp = self.main_page
        mp.search_mode = mode
        mp.clear_panels()
        
        try:
            mp.playlist_index_map = {}
            mp.pinned_playlist_id = None
        except Exception:
            pass

        if mode == 'playlists':
            self._execute_playlists_search(query)
        else:
            self._execute_videos_search(query)

    def _execute_playlists_search(self, query: str):
        mp = self.main_page
        ph = self.controller.playlist_handler
        
        try:
            mp.status_bar.configure(text=f"Searching playlists for '{query}'...")
            playlists = ph.search_playlists(query)
            
            # Efficient batch fetching of details
            pids = [p['playlistId'] for p in playlists if p.get('playlistId')]
            enriched = ph.get_playlists_batch(pids)
            
            mp.playlist_ui_handler.render_playlists(enriched)
            
            # Save search results for fallback
            ConfigManager.save_json(ConfigManager.get_last_search_path('playlists'), {
                'query': query,
                'playlists': enriched
            })
            mp.video.update_back_button_state(False)
            mp.status_bar.configure(text=f"Playlists search for '{query}' complete")
            
        except Exception as e:
            logger.error(f"Error in playlists search: {e}")
            mp.status_bar.configure(text="API quota/error — loading last saved results")
            
            # Fallback to last search
            try:
                path = ConfigManager.get_last_search_path('playlists')
                data = ConfigManager.load_json(path) or {}
                pls = data.get('playlists', [])
                if pls:
                    mp.playlist_ui_handler.render_playlists(pls)
                    messagebox.showinfo("Fallback", f"Using last search results for: {data.get('query','')}")
                else:
                    messagebox.showerror("Error", f"Failed to fetch playlists: {e}")
            except Exception:
                messagebox.showerror("Error", f"Failed to fetch playlists: {e}")

    def _execute_videos_search(self, query: str):
        mp = self.main_page
        ph = self.controller.playlist_handler
        mp.video_search_query = query
        
        try:
            mp.status_bar.configure(text=f"Searching videos for '{query}'...")
            mp.video.set_pagination_visible(False)
            
            try:
                max_results = int(mp.video.page_size_var.get())
            except Exception:
                max_results = 10
                
            resp = ph.search_videos(query, max_results=max_results)
            videos = resp.get('videos', [])
            mp.current_videos = videos
            mp.video_next_page_token = resp.get('nextPageToken')
            mp.video_prev_page_token = resp.get('prevPageToken')
            
            mp.video_search_ids = {v.get('videoId') for v in videos if v.get('videoId')}
            mp.video_ui_handler.render_videos(videos, mp.video_search_ids)
            mp.video_results_ids = mp.video_search_ids
            
            # Background playlist scanning
            threading.Thread(target=self._background_playlist_scan, args=(videos, query), daemon=True).start()
            
        except Exception as e:
            logger.error(f"Error in videos search: {e}")
            mp.status_bar.configure(text="API quota/error — loading last saved results")
            
            try:
                path = ConfigManager.get_last_search_path('videos')
                data = ConfigManager.load_json(path) or {}
                vids = data.get('videos', [])
                if vids:
                    mp.current_videos = vids
                    mp.video_next_page_token = data.get('nextPageToken')
                    mp.video_prev_page_token = data.get('prevPageToken')
                    mp.video_search_ids = {v.get('videoId') for v in vids if v.get('videoId')}
                    mp.video_ui_handler.render_videos(vids, mp.video_search_ids)
                    
                    # Also restore playlists if available
                    pls = data.get('playlists', [])
                    if pls:
                        mp.playlist_ui_handler.render_playlists(pls)
                        mp.playlist_ui_handler.map_videos_to_playlists(vids)
                else:
                    messagebox.showerror("Error", f"Failed to fetch videos: {e}")
            except Exception:
                messagebox.showerror("Error", f"Failed to fetch videos: {e}")

    def _background_playlist_scan(self, videos, query):
        mp = self.main_page
        mp._safe_ui(lambda: mp.set_mid_job_title('Mapping playlists'))
        mp._safe_ui(lambda t=len(videos): mp.video.show_scan(t))
        
        collected_local = []
        scanner = mp.video_scanner
        
        def _on_pl(pl):
            pi = mp.assign_playlist_index(pl.get('playlistId'))
            mp._safe_ui(lambda d=pl: mp.playlist.update_playlist(d))
            if mp.media_index:
                mp.media_index.add_playlists([pl])
            collected_local.append(pl)
            return pi

        def _prefetch(pid):
            try:
                ph = scanner._get_service()
                resp = ph.get_videos(pid, None, max_results=10)
                mp._cache_playlist_videos(pid, None, resp)
                if mp.media_index:
                    vids = [x.get('videoId') for x in (resp.get('videos', []) or []) if x.get('videoId')]
                    mp.media_index.bulk_link_playlist_videos(pid, vids)
            except Exception: pass

        def _progress(done, total):
            mp._safe_ui(lambda x=done, t=total: mp.status_bar.configure(text=f"Scanning playlists... {x}/{t}"))
            mp._safe_ui(lambda x=done, t=total: mp.video.update_scan_progress(x, t))

        def _index(vid, pid, idx):
            mp._safe_ui(lambda v_id=vid, p_id=pid: mp._update_video_row_by_vid(v_id, p_id))
            if mp.media_index:
                mp.media_index.link_video_to_playlist(pid, vid, idx)

        try:
            scanner.scan(videos, _on_pl, _prefetch, _progress, _index)
            # Final persistence
            try:
                ConfigManager.save_json(ConfigManager.get_last_search_path('videos'), {
                    'query': query,
                    'videos': videos,
                    'playlists': collected_local,
                    'nextPageToken': mp.video_next_page_token,
                    'prevPageToken': mp.video_prev_page_token,
                    'videoIds': list(mp.video_search_ids)
                })
            except Exception: pass
        except Exception as e:
            logger.error(f"Error in background scan: {e}")

    def back_to_video_results(self):
        """Restore previous search results from fallback storage."""
        mp = self.main_page
        if mp.search_mode != 'videos':
            return
            
        # Try Loading from persistence
        data = mp.search_persistence.load_last_videos_result()
        if not data:
            data = mp.search_persistence.load_last_search_from_config('videos')
            
        if not data:
            return

        mp.clear_panels()
        mp.playlist_index_map = {}
        
        videos = data.get('videos', [])
        playlists = data.get('playlists', [])
        
        # Restore state
        mp.current_videos = videos
        mp.collected_playlists = playlists
        mp.video_next_page_token = data.get('nextPageToken')
        mp.video_prev_page_token = data.get('prevPageToken')
        mp.video_search_query = data.get('query', '')
        
        ids = data.get('videoIds') or []
        mp.video_search_ids = set([i for i in ids if i])
        
        # Update Media Index if available
        if mp.media_index:
            try:
                mp.media_index.add_videos(videos)
                mp.media_index.add_playlists(playlists)
            except Exception: pass

        # UI Rendering
        mp.video_ui_handler.render_videos(videos, mp.video_search_ids, mp.video_search_query)
        mp.playlist_ui_handler.render_playlists(playlists)
        
        # Restore mappings
        mp.playlist_ui_handler.map_videos_to_playlists(videos)
        
        # Final UI polish
        mp.video.update_back_button_state(False)
        mp._preview_active = False
        mp._preview_only_hits = False
        mp.playlist.playlist_tree.configure(selectmode='extended')
        
        # Update search entry
        if mp.video_search_query:
            mp.search.search_entry.delete(0, 'end')
            mp.search.search_entry.insert(0, mp.video_search_query)
            
        mp.status_bar.configure(text=f"Restored results for '{mp.video_search_query}'")

    def on_video_select(self, event=None):
        """Handle video selection and update pinned playlist."""
        mp = self.main_page
        if mp.search_mode != 'videos':
            return
            
        sel = mp.video.video_tree.selection()
        if not sel:
            return
            
        try:
            # We assume single selection for this specific logic
            item_id = sel[0]
            # Find the video in current_videos by index in tree
            tree_idx = mp.video.video_tree.index(item_id)
            if tree_idx < 0 or tree_idx >= len(mp.current_videos):
                return
                
            video = mp.current_videos[tree_idx]
            vid = video.get('videoId')
            if not vid:
                return
            
            # Priority 1: Check if video already has playlistId assigned
            plid = video.get('playlistId')
            
            # Priority 2: Check video_playlist_cache
            if not plid:
                plid = mp.video_playlist_cache.get(vid)
            
            if plid:
                # We have the playlist - pin and select it
                self._pin_and_select_playlist(plid, vid, video, item_id)
                return
                
            # Priority 3: Search via API in background
            self._find_playlist_for_video(vid, tree_idx, item_id)
            
        except Exception as e:
            logger.error(f"Error in on_video_select: {e}")

    def _pin_and_select_playlist(self, plid, vid, video, tree_item_id):
        """Pin a playlist and update video row when playlist is known."""
        mp = self.main_page
        try:
            # Update cache
            mp.video_playlist_cache[vid] = plid
            video['playlistId'] = plid
            
            # Assign/get index
            pi = mp.assign_playlist_index(plid)
            video['playlistIndex'] = pi
            
            # Update video row
            mp.video.video_tree.item(tree_item_id, values=mp.video_ui_handler._video_row(video))
            
            # Pin and select playlist
            mp._set_pinned_playlist(plid)
            
            # Select in tree if exists
            if mp.playlist.playlist_tree.exists(plid):
                mp.playlist.playlist_tree.selection_set(plid)
                mp.playlist.playlist_tree.see(plid)
                
                # Report hits
                mp.playlist_ui_handler._report_playlist_hits(plid)
                mp.status_bar.configure(text=f"Playlist {pi} pinned")
            else:
                mp.status_bar.configure(text=f"Playlist not in current results")
        except Exception as e:
            logger.error(f"Error in _pin_and_select_playlist: {e}")

    def _find_playlist_for_video(self, vid, tree_idx, tree_item_id):
        mp = self.main_page
        if getattr(mp, '_highlighting_video_id', None) == vid:
            return
        mp._highlighting_video_id = vid
        
        def _worker():
            try:
                mp._safe_ui(lambda: mp.status_bar.configure(text="Finding playlist for selected video..."))
                # Use scanner service to search
                ph = mp.video_scanner._get_service()
                
                # Get video info
                video = mp.current_videos[tree_idx]
                queries = [video.get('title', ''), f"{video.get('channelTitle','')} {video.get('title','')}"]
                
                for q in queries:
                    if not q.strip():
                        continue
                    try:
                        pls = ph.search_playlists(q, max_results=5)
                    except Exception:
                        continue
                        
                    for pl in pls:
                        plid = pl.get('playlistId')
                        if not plid:
                            continue
                        try:
                            if ph.playlist_contains_video(plid, vid):
                                # Found it! Update UI on main thread
                                def _update_ui(p=pl, p_id=plid, v_id=vid, v=video, iid=tree_item_id):
                                    mp.playlist.update_playlist(p)
                                    self._pin_and_select_playlist(p_id, v_id, v, iid)
                                mp._safe_ui(_update_ui)
                                return
                        except Exception:
                            continue
                
                mp._safe_ui(lambda: mp.status_bar.configure(text="No playlist found for this video yet."))
            except Exception as e:
                logger.error(f"Error in _find_playlist_for_video worker: {e}")
            finally:
                mp._highlighting_video_id = None
                
        threading.Thread(target=_worker, daemon=True).start()

    def show_videos_search_page(self, page_token=None):
        """Fetch and display a specific page of video search results."""
        mp = self.main_page
        if mp.search_mode != 'videos' or not mp.video_search_query:
            return
            
        try:
            prev_token = mp.video_prev_page_token
            next_token = mp.video_next_page_token
            max_results = int(mp.video.page_size_var.get())
            
            # Fetch data
            try:
                resp = mp.controller.playlist_handler.search_videos(mp.video_search_query, max_results=max_results, page_token=page_token)
            except Exception as e:
                logger.warning(f"Failed to fetch video page via API: {e}. Falling back to config.")
                data = mp.search_persistence.load_last_search_from_config('videos')
                if data:
                    videos = data.get('videos', [])
                    mp.current_videos = videos
                    mp.video_next_page_token = data.get('nextPageToken')
                    mp.video_prev_page_token = data.get('prevPageToken')
                    mp.video_ui_handler.render_videos(videos, mp.video_search_ids, mp.video_search_query)
                    return
                else:
                    messagebox.showerror("Error", f"Failed to fetch videos: {e}")
                    return

            videos = resp.get('videos', [])
            mp.current_videos = videos
            mp.video_next_page_token = resp.get('nextPageToken')
            mp.video_prev_page_token = resp.get('prevPageToken')
            
            # Update UI
            mp.video_ui_handler.render_videos(videos, mp.video_search_ids, mp.video_search_query)
            
            # Update page index
            if page_token is None:
                mp.video_search_page_index = 1
            elif page_token == next_token:
                mp.video_search_page_index = int(getattr(mp, 'video_search_page_index', 1) or 1) + 1
            elif page_token == prev_token:
                mp.video_search_page_index = max(1, int(getattr(mp, 'video_search_page_index', 1) or 1) - 1)
            
            mp.video.page_indicator["text"] = f"Results page {mp.video_search_page_index}"
            
            # Update buttons and progress
            has_prev = bool(mp.video_prev_page_token)
            has_next = bool(mp.video_next_page_token)
            mp.video.prev_page_btn["state"] = "normal" if has_prev else "disabled"
            mp.video.next_page_btn["state"] = "normal" if has_next else "disabled"
            
            try:
                count_items = len(mp.video.video_tree.get_children())
                mp.video._panel.update_pages(index=mp.video_search_page_index, has_prev=has_prev, has_next=has_next, total_items=count_items)
            except Exception: pass
            
            # Trigger background scan for new videos
            self._background_playlist_scan(videos, mp.video_search_query)
            
        except Exception as e:
            logger.error(f"Error in show_videos_search_page: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
    def search_playlists(self):
        """Search for playlists from the search entry."""
        mp = self.main_page
        query = mp.search.search_entry.get()
        if not query:
            messagebox.showerror("Error", "Please enter a keyword.")
            return

        self._execute_playlists_search(query)

    def show_playlist_videos(self, event=None, page_token=None):
        """Fetch and display videos from a selected playlist."""
        mp = self.main_page
        
        # 1. Identity selected playlist
        if event:
            selected_item = mp.playlist.get_selected_playlist()
        else:
            sel = mp.playlist.playlist_tree.selection()
            selected_item = sel[0] if sel else None
        
        if not selected_item:
            return

        playlist_id = selected_item
        
        # 2. Ensure info exists
        try:
            if not mp.playlist.playlist_tree.exists(playlist_id):
                info = self.controller.playlist_handler.get_playlist_info(playlist_id)
                mp.playlist.update_playlist(info)
        except Exception: pass
        
        # 3. Get UI values
        playlist_values = mp.playlist.playlist_tree.item(selected_item)["values"]
        playlist_title = playlist_values[1] if len(playlist_values) > 1 else "Unknown"
        
        # 4. Update state
        mp.search_mode = 'playlists' # Ensure we know we are in playlist viewing mode
        mp._set_pinned_playlist(playlist_id)
        mp._preview_active = False 

        # Set current_playlist_info for other actions
        self.current_playlist_info = {
            "title": playlist_title,
            "channel": playlist_values[2] if len(playlist_values) > 2 else "Unknown",
            "id": playlist_id
        }
        mp.video.update_mode_ui(False) # show pagination if needed
        
        try:
            max_results = int(mp.video.page_size_var.get())
        except Exception:
            max_results = 10
            
        # 5. Fetch process (with caching)
        mp.status_bar.configure(text=f"Loading videos for '{playlist_title}'...")
        
        def _on_success(resp):
            videos = resp.get("videos", [])
            mp.current_videos = videos
            mp.current_page_token = resp.get("nextPageToken")
            mp.prev_page_token = resp.get("prevPageToken")
            
            # Persist to cache
            mp._cache_playlist_videos(playlist_id, page_token, resp)
            
            # Map indices
            pi = mp.assign_playlist_index(playlist_id)
            for v in videos:
                v['playlistIndex'] = pi
                vid = v.get('videoId')
                if vid: mp.video_playlist_cache[vid] = playlist_id
                
            mq = getattr(mp, 'video_search_query', '')
            ms = getattr(mp, 'video_search_ids', set())
            
            # Render
            mp.video_ui_handler.render_videos(videos, ms, mq)
            
            # Update Pagination UI
            has_prev = bool(mp.prev_page_token)
            has_next = bool(mp.current_page_token)
            
            mp.video.update_back_button_state(True)
            try:
                # Update page number - simplified
                total_videos = 0
                try: total_videos = int(playlist_values[3])
                except Exception: pass
                
                total_pages = (total_videos + max_results - 1) // max_results if total_videos > 0 else 1
                # (Page index math skipped for brevity, keeping it simple)
                mp.video._panel.update_pages(index=1, has_prev=has_prev, has_next=has_next, total_items=total_videos)
            except Exception: pass
            
            mp.status_bar.configure(text=f"Loaded {len(videos)} videos from '{playlist_title}'")

        def _worker():
            try:
                # Check cache first
                cached = mp._get_cached_playlist_page(playlist_id, page_token)
                if cached:
                    mp._safe_ui(lambda: _on_success(cached))
                    return
                
                # Fetch from API
                ph = self.controller.playlist_handler
                resp = ph.get_videos(playlist_id, page_token, max_results=max_results)
                mp._safe_ui(lambda: _on_success(resp))
            except Exception as e:
                logger.error(f"Error fetching playlist videos: {e}")
                mp._safe_ui(lambda: messagebox.showerror("Error", f"Failed to load playlist: {e}"))

        threading.Thread(target=_worker, daemon=True).start()

    def download_selected_videos(self):
        """Download videos selected in the video table."""
        try:
            sel = self.video_section.video_tree.selection()
            if not sel:
                messagebox.showerror("Error", "Please select one or more videos.")
                return
                
            videos = []
            current_videos = list(self.main_page.current_videos or [])
            for iid in sel:
                try:
                    idx = self.video_section.video_tree.index(iid)
                    if 0 <= idx < len(current_videos):
                        videos.append(current_videos[idx])
                except Exception:
                    continue
                    
            if not videos:
                messagebox.showerror("Error", "Selected rows not found.")
                return
                
            self._start_download_for_videos(videos, None)
        except Exception as e:
            logger.error(f"Error downloading selected videos: {e}")

    def download_single_video(self):
        """Download a single selected video."""
        try:
            sel = self.video_section.video_tree.selection()
            if not sel:
                messagebox.showerror("Error", "Please select a video.")
                return
                
            idx = self.video_section.video_tree.index(sel[0])
            current_videos = list(self.main_page.current_videos or [])
            if idx < 0 or idx >= len(current_videos):
                return
                
            v = current_videos[idx]
            self._start_download_for_videos([v], None)
        except Exception as e:
            logger.error(f"Error downloading single video: {e}")

    def download_selected_playlists(self):
        """Download all videos in the selected playlists."""
        try:
            sel = list(self.main_page.playlist.playlist_tree.selection())
            if not sel:
                messagebox.showerror("Error", "Please select one or more playlists.")
                return
                
            all_videos = []
            try:
                mr = int(self.video_section.page_size_var.get())
            except Exception:
                mr = 10
                
            for pid in sel:
                vids = []
                cached = self.main_page._get_cached_playlist_page(pid, None)
                if cached:
                    vids = list(cached.get('videos', []) or [])
                else:
                    try:
                        resp = self.controller.playlist_handler.get_videos(pid, None, max_results=mr)
                        self.main_page._cache_playlist_videos(pid, None, resp)
                        vids = list(resp.get('videos', []) or [])
                    except Exception:
                        vids = []
                
                for v in vids:
                    if not v.get('playlistId'):
                        v['playlistId'] = pid
                all_videos.extend(vids)
                
            if not all_videos:
                messagebox.showerror("Error", "No videos found in selected playlists.")
                return
                
            self._start_download_for_videos(all_videos, None)
        except Exception as e:
            logger.error(f"Error downloading selected playlists: {e}")

    def _start_download_for_videos(self, videos: List[Dict[str, Any]], folder: Optional[str] = None):
        """Initiate the download process for a list of videos."""
        try:
            self._enrich_video_playlist_info(videos)
            
            try:
                from .download_options_dialog import DownloadOptionsDialog
            except Exception:
                from src.pages.main.download_options_dialog import DownloadOptionsDialog
                
            dlg = DownloadOptionsDialog(self.main_page)
            if not getattr(dlg, 'result', None):
                return
                
            try:
                from .download_manager import DownloadManager
            except Exception:
                from src.pages.main.download_manager import DownloadManager
                
            DownloadManager(self.main_page, list(videos or []), folder, dlg.result).start()
        except Exception as e:
            logger.error(f"Error starting download: {e}")

    def _enrich_video_playlist_info(self, videos: List[Dict[str, Any]]):
        """Attempt to associate videos with their parent playlists for better organization."""
        try:
            for v in list(videos or []):
                vid = v.get('videoId')
                pid = v.get('playlistId')
                
                if not pid:
                    pid = self.main_page.video_playlist_cache.get(vid)
                    
                if not pid:
                    # Look in playlist_video_ids cache
                    for k, ids in (getattr(self.main_page, 'playlist_video_ids', {}) or {}).items():
                        if vid in ids:
                            pid = k
                            break
                            
                if not pid:
                    # Search through visible playlists
                    existing = list(self.main_page.playlist.playlist_tree.get_children())
                    for plid in existing:
                        try:
                            if self.controller.playlist_handler.playlist_contains_video(plid, vid):
                                pid = plid
                                break
                        except Exception:
                            continue
                
                if pid:
                    v['playlistId'] = pid
                    self.main_page.video_playlist_cache[vid] = pid
        except Exception as e:
            logger.error(f"Error enriching video info: {e}")

    def cache_playlist_videos(self, playlist_id: str, page_token: Optional[str], response: Dict[str, Any]):
        """Cache videos for a playlist page to reduce API calls."""
        try:
            mp = self.main_page
            cache = mp.playlist_videos_cache.setdefault(playlist_id, {'pages': {}, 'tokens': {}})
            key = page_token or '__first__'
            vids = list(response.get('videos', []))
            cache['pages'][key] = vids
            cache['tokens'][key] = (response.get('prevPageToken'), response.get('nextPageToken'))
            
            ids = {v.get('videoId') for v in vids if v.get('videoId')}
            
            # Update local memory index
            cur_ids = mp.playlist_video_ids.setdefault(playlist_id, set())
            for vid in ids:
                cur_ids.add(vid)
                
            # Update persistent media index
            if hasattr(mp, 'media_index') and mp.media_index:
                mp.media_index.bulk_link_playlist_videos(playlist_id, list(ids))
                
        except Exception as e:
            logger.error(f"Error caching playlist videos: {e}")

    def get_cached_playlist_page(self, playlist_id: str, page_token: Optional[str]) -> Optional[Dict[str, Any]]:
        """Retrieve a cached page of playlist videos."""
        try:
            mp = self.main_page
            cache = mp.playlist_videos_cache.get(playlist_id)
            if not cache:
                return None
                
            key = page_token or '__first__'
            vids = cache.get('pages', {}).get(key)
            toks = cache.get('tokens', {}).get(key, (None, None))
            
            if vids is None:
                return None
                
            return {
                'videos': vids,
                'prevPageToken': toks[0],
                'nextPageToken': toks[1]
            }
        except Exception as e:
            logger.error(f"Error getting cached playlist page: {e}")
            return None

    def assign_playlist_index(self, playlist_id: str) -> int:
        """Assign or retrieve a 1-based index for a playlist (used for display)."""
        mp = self.main_page
        if playlist_id in mp.playlist_index_map:
            return mp.playlist_index_map[playlist_id]
            
        idx = len(mp.playlist_index_map) + 1
        mp.playlist_index_map[playlist_id] = idx
        return idx

    def download_playlist_videos(self):
        """Download videos from the current playlist."""
        mp = self.main_page
        selected_playlist = mp.playlist.get_selected_playlist()
        if not selected_playlist:
            messagebox.showerror("Error", "Please select a playlist first.")
            return
            
        try:
            if not self.current_playlist_info:
                try:
                    vals = mp.playlist.playlist_tree.item(selected_playlist).get('values', [])
                except Exception:
                    vals = []
                ttl = vals[1] if len(vals) > 1 else ''
                chn = vals[2] if len(vals) > 2 else ''
                self.current_playlist_info = {"title": ttl or str(selected_playlist), "channel": chn, "id": selected_playlist}
        except Exception:
            pass
            
        if not mp.current_videos:
            self.show_playlist_videos()
            if not mp.current_videos:
                messagebox.showerror("Error", "No videos found in the selected playlist.")
                return
                
        try:
            folder = os.path.join(self.controller.default_folder, f"Playlist - {self.current_playlist_info['title']}")
            os.makedirs(folder, exist_ok=True)
            self._start_download_for_videos(mp.current_videos, folder)
        except Exception as e:
            logger.error(f"Error downloading playlist videos: {e}")

    def view_downloaded_videos(self):
        """Open a window to view downloaded videos."""
        mp = self.main_page
        if not self.current_playlist_info:
            messagebox.showerror("Error", "No playlist selected.")
            return

        playlist_folder = os.path.join(
            self.controller.default_folder,
            f"Playlist - {self.current_playlist_info['title']}"
        )

        if not os.path.exists(playlist_folder):
            messagebox.showerror("Error", "No downloaded videos found for this playlist.")
            return

        try:
            from src.pages.main.video_player import VideoPlayer
        except ImportError:
            from .video_player import VideoPlayer
            
        player = VideoPlayer(mp, playlist_folder)
        videos = [f for f in os.listdir(playlist_folder) if f.endswith('.mp4')]
        for video in videos:
            player.video_listbox.insert(tk.END, video)

    def save_playlist(self):
        """Save the selected playlist details to a file."""
        mp = self.main_page
        if not self.current_playlist_info or not mp.current_videos:
            messagebox.showerror("Error", "No playlist selected or no videos found.")
            return

        playlist_title = self.current_playlist_info["title"]
        channel_title = self.current_playlist_info["channel"]

        try:
            file_path = os.path.join(
                self.controller.default_folder,
                f"{playlist_title}.txt"
            )
            
            with open(file_path, 'w', encoding='utf-8') as txtfile:
                txtfile.write(f"Playlist: {playlist_title}\n")
                txtfile.write(f"Channel: {channel_title}\n")
                txtfile.write("\nVideos:\n")
                for i, video in enumerate(mp.current_videos, 1):
                    txtfile.write(f"\n{i}. {video['title']}\n")
                    txtfile.write(f"   URL: https://www.youtube.com/watch?v={video['videoId']}\n")

            messagebox.showinfo("Success", f"Playlist saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save playlist: {str(e)}")

    def export_playlist_csv(self):
        """Export the current playlist to a CSV file."""
        mp = self.main_page
        if not self.current_playlist_info or not mp.current_videos:
            messagebox.showerror("Error", "No playlist selected or no videos found.")
            return

        try:
            file_path = os.path.join(
                self.controller.default_folder,
                f"{self.current_playlist_info['title']}.csv"
            )
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Title', 'Video ID', 'URL', 'Duration'])
                for video in mp.current_videos:
                    writer.writerow([
                        video['title'],
                        video['videoId'],
                        f"https://www.youtube.com/watch?v={video['videoId']}",
                        video['duration']
                    ])

            messagebox.showinfo("Success", f"Playlist exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export playlist: {str(e)}")

    def export_playlist_txt(self):
        """Export the current playlist to a text file."""
        mp = self.main_page
        if not self.current_playlist_info or not mp.current_videos:
            messagebox.showerror("Error", "No playlist selected or no videos found.")
            return

        try:
            file_path = os.path.join(
                self.controller.default_folder,
                f"{self.current_playlist_info['title']}_export.txt"
            )
            
            with open(file_path, 'w', encoding='utf-8') as txtfile:
                txtfile.write(f"Playlist: {self.current_playlist_info['title']}\n")
                txtfile.write(f"Channel: {self.current_playlist_info['channel']}\n")
                txtfile.write(f"Total Videos: {len(mp.current_videos)}\n\n")
                
                for i, video in enumerate(mp.current_videos, 1):
                    txtfile.write(f"{i}. {video['title']} ({video['duration']})\n")
                    txtfile.write(f"   https://www.youtube.com/watch?v={video['videoId']}\n\n")

            messagebox.showinfo("Success", f"Playlist exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export playlist: {str(e)}")

    def change_download_folder(self):
        """Allow the user to change the default download folder."""
        new_folder = filedialog.askdirectory()
        if new_folder:
            self.controller.update_config(self.controller.api_key, new_folder)
            messagebox.showinfo("Success", f"Download folder updated to {new_folder}")

    def open_download_folder(self):
        """Open the download folder in file explorer."""
        if not self.current_playlist_info:
            return

        folder_path = os.path.join(
            self.controller.default_folder,
            f"Playlist - {self.current_playlist_info['title']}"
        )
        
        if os.path.exists(folder_path):
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder_path])
            else:
                subprocess.run(["xdg-open", folder_path])

    def print_playlist_videos_to_terminal(self, playlist_id: str):
        """Fetch and print names of all videos in a playlist to terminal."""
        mp = self.main_page
        try:
            vals = mp.playlist.playlist_tree.item(playlist_id).get('values', [])
            ttl = (vals[1] if isinstance(vals, (list, tuple)) and len(vals) > 1 else '') or ''
        except Exception:
            ttl = ''
            
        try:
            mr_main = int(mp.video.page_size_var.get())
        except Exception:
            mr_main = 10
            
        def _printer(resp):
            try:
                vids = list(resp.get('videos', []) or [])
                print(f"[Playlist] {ttl or playlist_id} ({playlist_id})")
                for v in vids:
                    try:
                        pub = mp.video_ui_handler._fmt_date(v.get('published',''))
                        vs = v.get('views','')
                        print(f" - {v.get('title','')} | {v.get('duration','')} | {pub} | {vs}")
                    except Exception:
                        pass
            except Exception:
                pass
                
        def _worker(mr):
            try:
                cached = self.get_cached_playlist_page(playlist_id, None)
                if cached is not None:
                    _printer(cached)
                    return
                    
                resp = self.controller.playlist_handler.get_videos(playlist_id, None, max_results=mr)
                if resp:
                    self.cache_playlist_videos(playlist_id, None, resp)
                    _printer(resp)
            except Exception as e:
                logger.error(f"Error printing playlist videos: {e}")
                
        threading.Thread(target=_worker, args=(mr_main,), daemon=True).start()
