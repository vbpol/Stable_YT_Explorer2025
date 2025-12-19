import json
import os
from typing import Dict, Any, Optional, List, Set
from src.config_manager import ConfigManager
from src.logger import logger

class StateManager:
    """
    Centralized manager for application state persistence.
    Handles saving and restoring search results, playlist mappings, and pagination tokens.
    """

    @staticmethod
    def save_videos_search_state(
        query: str,
        videos: List[Dict[str, Any]],
        playlists: List[Dict[str, Any]],
        next_page_token: Optional[str],
        prev_page_token: Optional[str],
        video_ids: Set[str],
        playlist_pages: Dict[str, Any],
        playlist_ids: Dict[str, Any]
    ) -> None:
        """Save the current video search state to file."""
        try:
            # Convert sets to lists for JSON serialization
            v_ids_list = list(video_ids)
            p_ids_map = {
                pid: list(vids) if isinstance(vids, (set, list)) else []
                for pid, vids in playlist_ids.items()
            }

            data = {
                'query': query,
                'videos': videos,
                'playlists': playlists,
                'nextPageToken': next_page_token,
                'prevPageToken': prev_page_token,
                'videoIds': v_ids_list,
                'playlistPages': playlist_pages,
                'playlistIds': p_ids_map
            }
            
            path = ConfigManager.get_last_search_path('videos')
            ConfigManager.save_json(path, data)
            logger.info("Video search state saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save video search state: {e}")

    @staticmethod
    def load_videos_search_state() -> Dict[str, Any]:
        """Load the last saved video search state."""
        try:
            path = ConfigManager.get_last_search_path('videos')
            data = ConfigManager.load_json(path) or {}
            if not isinstance(data, dict):
                return {}
            return data
        except Exception as e:
            logger.error(f"Failed to load video search state: {e}")
            return {}

    @staticmethod
    def save_playlists_search_state(query: str, playlists: List[Dict[str, Any]]) -> None:
        """Save the current playlist search state."""
        try:
            data = {
                'query': query,
                'playlists': playlists
            }
            path = ConfigManager.get_last_search_path('playlists')
            ConfigManager.save_json(path, data)
        except Exception as e:
            logger.error(f"Failed to save playlist search state: {e}")

    @staticmethod
    def load_playlists_search_state() -> Dict[str, Any]:
        """Load the last saved playlist search state."""
        try:
            path = ConfigManager.get_last_search_path('playlists')
            data = ConfigManager.load_json(path) or {}
            if not isinstance(data, dict):
                return {}
            return data
        except Exception as e:
            logger.error(f"Failed to load playlist search state: {e}")
            return {}
