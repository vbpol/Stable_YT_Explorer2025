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

    def search_playlists(self, query: str):
        """Execute playlist search and update UI."""
        try:
            playlists = self.controller.playlist_handler.search_playlists(query)
            enriched = []
            for playlist in playlists:
                try:
                    video_count = self.controller.playlist_handler.get_details(playlist["playlistId"])
                    playlist["video_count"] = video_count
                except Exception:
                    playlist["video_count"] = "N/A"
                enriched.append(playlist)
            
            self.render_playlists(enriched)
            StateManager.save_playlists_search_state(query, enriched)
            self.main_page.video.update_back_button_state(False)
            
        except PlaylistError as e:
            messagebox.showerror("Search Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch playlists: {e}")
            logger.error(f"Error searching playlists: {e}")

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
