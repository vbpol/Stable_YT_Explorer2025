import tkinter as tk
from tkinter import messagebox
from typing import Dict, Any, List, Optional, Set
from src.logger import logger
from src.playlist import PlaylistError
from src.state_manager import StateManager

class PlaylistUIHandler:
    """
    Handles playlist-related UI logic for the MainPage.
    Responsible for rendering the playlist tree, executing playlist searches,
    and managing playlist mapping/updates.
    """

    def __init__(self, main_page):
        self.main_page = main_page
        self.playlist_section = main_page.playlist
        self.controller = main_page.controller

    def render_playlists(self, playlists: List[Dict[str, Any]]):
        """Render a list of playlists to the playlist tree."""
        try:
            self.playlist_section.playlist_tree.delete(*self.playlist_section.playlist_tree.get_children())
            
            def _ins_chunk(s):
                try:
                    ch = 30
                    e = min(s + ch, len(playlists))
                    for i in range(s, e):
                        self.playlist_section.update_playlist(playlists[i])
                    if e < len(playlists):
                        self.main_page.after(0, lambda st=e: _ins_chunk(st))
                except Exception as e:
                    logger.error(f"Error rendering playlist chunk: {e}")
            
            _ins_chunk(0)
        except Exception as e:
            logger.error(f"Error rendering playlists: {e}")

    def map_videos_to_playlists(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Map videos to playlists based on intersection of video IDs.
        Returns a list of collected playlist info.
        """
        collected = []
        try:
            # Get current playlist IDs from tree
            children = list(self.playlist_section.playlist_tree.get_children())
            
            # Get IDs of current videos
            result_ids = {v.get('videoId') for v in list(videos or []) if v.get('videoId')}
            
            hits_by_playlist = {}
            for pid in children:
                ids = set()
                try:
                    if self.main_page.media_index:
                        ids = set(list(self.main_page.media_index.get_playlist_video_ids(pid) or []))
                    else:
                        ids = set(list(self.main_page.playlist_video_ids.get(pid, set()) or set()))
                except Exception:
                    ids = set(list(self.main_page.playlist_video_ids.get(pid, set()) or set()))
                
                inter = ids.intersection(result_ids)
                if inter:
                    hits_by_playlist[pid] = inter

            # Update index map
            index_map = dict(self.main_page.playlist_index_map or {})
            for pid in hits_by_playlist.keys():
                if pid not in index_map:
                    index_map[pid] = len(index_map) + 1
                
                try:
                    info = self.controller.playlist_handler.get_playlist_info(pid)
                except Exception:
                    info = {'playlistId': pid, 'title': '', 'channelTitle': '', 'video_count': 'N/A'}
                collected.append(info)

            # Map video IDs to Playlist IDs for cache
            vid_to_pid = {}
            for pid, vids in hits_by_playlist.items():
                for vid in vids:
                    vid_to_pid[vid] = pid

            # Update video objects with playlist info
            for v in list(videos or []):
                vid = v.get('videoId')
                pid = vid_to_pid.get(vid)
                if not pid:
                    continue
                v['playlistId'] = pid
                v['playlistIndex'] = index_map.get(pid)
                self.main_page.video_playlist_cache[vid] = pid

            self.main_page.playlist_index_map = index_map
            
            # Update Playlist Tree UI to show only hits
            existing = list(self.playlist_section.playlist_tree.get_children())
            for iid in existing:
                if iid not in index_map:
                    try:
                        self.playlist_section.playlist_tree.detach(iid)
                    except Exception:
                        pass
                else:
                    try:
                        vals = self.playlist_section.playlist_tree.item(iid).get('values', [])
                        new_vals = ((index_map.get(iid) or ""),) + tuple(vals[1:]) if vals else ((index_map.get(iid) or ""),)
                        self.playlist_section.playlist_tree.item(iid, values=new_vals)
                        self.playlist_section.playlist_tree.set(iid, 'No', str(index_map.get(iid)))
                    except Exception:
                        pass
            
            # Reattach in order
            for pid in sorted(index_map.keys(), key=lambda k: index_map[k]):
                try:
                    self.playlist_section.playlist_tree.reattach(pid, '', 'end')
                except Exception:
                    pass

            # Refresh video table to show new indices
            self.main_page.video_ui_handler.render_videos(
                videos, 
                getattr(self.main_page, 'video_search_ids', set()),
                getattr(self.main_page, 'video_search_query', '')
            )

            self.main_page.collected_playlists = collected
            
            return collected

        except Exception as e:
            logger.error(f"Error mapping videos to playlists: {e}")
            return []
    def set_pinned_playlist(self, playlist_id: str):
        """Pin a playlist to the top and mark it as pinned in the UI."""
        try:
            mp = self.main_page
            # Unpin old
            if mp.pinned_playlist_id and self.playlist_section.playlist_tree.exists(mp.pinned_playlist_id):
                vals = self.playlist_section.playlist_tree.item(mp.pinned_playlist_id).get('values', [])
                if len(vals) >= 5 and isinstance(vals[4], str):
                    new_vals = list(vals)
                    new_vals[4] = new_vals[4].replace(' • Pinned', '')
                    self.playlist_section.playlist_tree.item(mp.pinned_playlist_id, values=tuple(new_vals))
            
            mp.pinned_playlist_id = playlist_id
            
            # Pin new
            if self.playlist_section.playlist_tree.exists(playlist_id):
                vals = self.playlist_section.playlist_tree.item(playlist_id).get('values', [])
                if len(vals) >= 5 and isinstance(vals[4], str) and ' • Pinned' not in vals[4]:
                    new_vals = list(vals)
                    new_vals[4] = f"{new_vals[4]} • Pinned"
                    self.playlist_section.playlist_tree.item(playlist_id, values=tuple(new_vals))
            
            self.bring_playlist_to_top(playlist_id)
        except Exception as e:
            logger.error(f"Error pinning playlist: {e}")

    def bring_playlist_to_top(self, playlist_id: str):
        """Move a playlist to the first position in the treeview."""
        try:
            self.playlist_section.playlist_tree.move(playlist_id, '', 0)
            self.playlist_section.playlist_tree.see(playlist_id)
        except Exception as e:
            logger.error(f"Error bringing playlist to top: {e}")

    def _count_downloaded_files(self, folder: str) -> int:
        """Count video files in a folder."""
        try:
            import os
            if not os.path.exists(folder):
                return 0
            exts = ('.mp4', '.webm', '.mkv')
            return len([f for f in os.listdir(folder) if any(f.lower().endswith(e) for e in exts)])
        except Exception:
            return 0

    def playlist_folder_by_id(self, playlist_id: str) -> str:
        """Get the expected download folder for a playlist."""
        try:
            import os
            ttl = ''
            if self.playlist_section.playlist_tree.exists(playlist_id):
                vals = self.playlist_section.playlist_tree.item(playlist_id).get('values', [])
                ttl = vals[1] if len(vals) > 1 else ''
            
            base_folder = getattr(self.controller, 'default_folder', os.getcwd())
            return os.path.join(base_folder, f"Playlist - {ttl or 'Unknown'}")
        except Exception:
            return getattr(self.controller, 'default_folder', os.getcwd())

    def playlist_download_status(self, playlist_id: str, expected_count: Any) -> str:
        """Get the download status string for a playlist."""
        try:
            import os
            folder = self.playlist_folder_by_id(playlist_id)
            if not os.path.exists(folder):
                return "Not Downloaded"
            
            cnt = self._count_downloaded_files(folder)
            try:
                exp = int(expected_count or 0)
            except Exception:
                exp = 0
                
            if cnt == 0:
                return "Empty Folder"
            if exp and cnt >= exp:
                return "Complete"
            if exp:
                return f"{cnt}/{exp}"
            return str(cnt)
        except Exception:
            return "Unknown"

    def normalize_playlist_indices(self):
        """Re-assign indices to playlists currently in the tree based on their position."""
        try:
            children = list(self.playlist_section.playlist_tree.get_children())
            new_map = {}
            for i, pid in enumerate(children, start=1):
                new_map[pid] = i
            self.main_page.playlist_index_map = new_map
            
            # Update tree UI
            self.playlist_section.normalize_numbers()
            
            # Sync indexed videos
            for v in list(self.main_page.current_videos or []):
                pid = v.get('playlistId')
                if pid in new_map:
                    v['playlistIndex'] = new_map[pid]
                    
            # Refresh video table to show new indices
            self.main_page.video_ui_handler.refresh_video_statuses()
        except Exception as e:
            logger.error(f"Error normalizing playlist indices: {e}")

    def highlight_videos_for_playlist(self, playlist_id: str):
        """Highlight videos in the current results that belong to the specified playlist."""
        try:
            self.main_page.video_ui_handler.clear_video_playlist_highlights()
            
            # Get video IDs for this playlist
            ids = set()
            try:
                if self.main_page.media_index:
                    ids = set(self.main_page.media_index.get_playlist_video_ids(playlist_id) or [])
                else:
                    ids = set(self.main_page.playlist_video_ids.get(playlist_id, set()) or set())
            except Exception:
                ids = set(self.main_page.playlist_video_ids.get(playlist_id, set()) or set())

            if not ids:
                return

            # Find matching items in the video tree
            items = self.main_page.video.video_tree.get_children()
            count = 0
            for i, iid in enumerate(items):
                if i < len(self.main_page.current_videos):
                    v = self.main_page.current_videos[i]
                    if v.get('videoId') in ids:
                        # Add highlight tag
                        tags = list(self.main_page.video.video_tree.item(iid, 'tags') or [])
                        if 'playlist_match' not in tags:
                            tags.append('playlist_match')
                            self.main_page.video.video_tree.item(iid, tags=tuple(tags))
                        
                        # Apply star to title if not already there
                        vals = list(self.main_page.video.video_tree.item(iid, 'values') or [])
                        if vals and isinstance(vals[1], str) and not vals[1].startswith('★'):
                            vals[1] = f"★ {vals[1]}"
                            self.main_page.video.video_tree.item(iid, values=tuple(vals))
                        count += 1
            
            if count > 0:
                self.main_page.status_bar.configure(text=f"Highlighted {count} videos from selected playlist")
        except Exception as e:
            logger.error(f"Error highlighting playlist videos: {e}")

    def on_videos_mode_playlist_click(self, playlist_id: str):
        """Handle playlist selection when in videos search mode."""
        try:
            if not playlist_id:
                return
                
            busy = bool(getattr(self.main_page, '_videos_mode_click_busy', False))
            if busy:
                self.main_page.status_bar.configure(text="Busy… please wait")
                return
                
            self.main_page._videos_mode_click_busy = True
            self.set_pinned_playlist(playlist_id)
            self.main_page.status_bar.configure(text="Loading playlist context…")
            
            # Run highlight on UI thread
            self.main_page.after(0, lambda pid=playlist_id: self.highlight_videos_for_playlist(pid))
            
            # Defer printing so highlight appears quickly
            self.main_page.after(50, lambda pid=playlist_id: self.main_page.print_playlist_videos_to_terminal(pid))
            
            # Report hits after a short delay
            self.main_page.after(80, lambda pid=playlist_id: self._report_playlist_hits(pid))
            
        except Exception as e:
            logger.error(f"Error in on_videos_mode_playlist_click: {e}")
        finally:
            self.main_page._videos_mode_click_busy = False

    def _report_playlist_hits(self, playlist_id: str):
        """Report number of matches for a playlist in current search results."""
        try:
            mp = self.main_page
            vids = set(mp.video_results_ids or set())
            
            ids = set()
            try:
                if mp.media_index:
                    ids = set(mp.media_index.get_playlist_video_ids(playlist_id) or [])
                else:
                    ids = set(mp.playlist_video_ids.get(playlist_id, set()) or set())
            except Exception:
                ids = set(mp.playlist_video_ids.get(playlist_id, set()) or set())
                
            hits = vids.intersection(ids)
            count = len(hits)
            
            # Update playlist row in tree to show intersection count
            if mp.playlist.playlist_tree.exists(playlist_id):
                vals = list(mp.playlist.playlist_tree.item(playlist_id).get('values', []))
                if len(vals) >= 5:
                    vals[4] = f"Intersecting: {count}"
                    mp.playlist.playlist_tree.item(playlist_id, values=tuple(vals))
                    
        except Exception as e:
            logger.error(f"Error reporting playlist hits: {e}")

    def sort_playlists_by(self, column_name: str):
        """Sort the playlist tree by a specific column."""
        try:
            idx_map = {"No": 0, "Title": 1, "Channel": 2, "Videos": 3, "Status": 4, "Actions": 5}
            idx = idx_map.get(column_name)
            if idx is None:
                return
                
            asc = self.main_page.playlist_sort_state.get(column_name, False)
            rows = []
            for item in self.playlist_section.playlist_tree.get_children(''):
                vals = self.playlist_section.playlist_tree.item(item).get('values', [])
                rows.append((item, vals))
                
            def _key(row):
                v = row[1][idx] if idx < len(row[1]) else ''
                if idx in (0, 3): # No, Videos
                    try: return int(str(v))
                    except: return 0
                return str(v).lower()
                
            rows.sort(key=_key, reverse=not asc)
            self.main_page.playlist_sort_state[column_name] = not asc
            
            for i, (item, _) in enumerate(rows):
                self.playlist_section.playlist_tree.move(item, '', i)
        except Exception as e:
            logger.error(f"Error sorting playlists by {column_name}: {e}")

    def on_playlist_header_double_click(self, column_name: str, q=None):
        """Filter playlists currently in the tree."""
        try:
            import tkinter.simpledialog as simpledialog
            idx_map = {"No": 0, "Title": 1, "Channel": 2, "Videos": 3, "Status": 4, "Actions": 5}
            idx = idx_map.get(column_name)
            if idx is None:
                return
                
            if q is None:
                q = simpledialog.askstring("Filter", f"Filter {column_name} contains:")
            if q is None:
                return
                
            ql = (q or '').strip().lower()
            for item in self.playlist_section.playlist_tree.get_children():
                vals = self.playlist_section.playlist_tree.item(item).get('values', [])
                s = str(vals[idx]) if idx < len(vals) else ''
                if ql and ql not in s.lower():
                    self.playlist_section.playlist_tree.detach(item)
                else:
                    try:
                        self.playlist_section.playlist_tree.reattach(item, '', 'end')
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"Error filtering playlists by {column_name}: {e}")
