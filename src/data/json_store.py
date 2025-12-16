from typing import List, Dict, Optional
import os
try:
    from src.config_manager import ConfigManager
except ModuleNotFoundError:
    from config_manager import ConfigManager

class JsonStore:
    def save_last_videos_result(self, query: str, videos: List[Dict], playlists: List[Dict], next_token: Optional[str], prev_token: Optional[str], video_ids: List[str]) -> None:
        data = {
            'videos': videos,
            'playlists': playlists,
            'nextPageToken': next_token,
            'prevPageToken': prev_token,
            'videoIds': list(video_ids or []),
            'query': query or ''
        }
        ConfigManager.save_json(ConfigManager.get_last_search_path('videos'), data)

    def load_last_videos_result(self) -> Dict:
        data = ConfigManager.load_json(ConfigManager.get_last_search_path('videos')) or {}
        return {
            'videos': data.get('videos', []),
            'playlists': data.get('playlists', []),
            'nextPageToken': data.get('nextPageToken'),
            'prevPageToken': data.get('prevPageToken'),
            'videoIds': data.get('videoIds', []),
            'query': data.get('query', '')
        }

    def save_last_playlists_result(self, query: str, playlists: List[Dict]) -> None:
        data = playlists[:]
        ConfigManager.save_json(ConfigManager.get_last_search_path('playlists'), data)
        # Also store query in a small side file for older format compatibility
        meta = {'query': query or ''}
        ConfigManager.save_json(ConfigManager.get_last_search_path('playlists').replace('_search.json', '_meta.json'), meta)

    def load_last_playlists_result(self) -> Dict:
        playlists = ConfigManager.load_json(ConfigManager.get_last_search_path('playlists')) or []
        meta = ConfigManager.load_json(ConfigManager.get_last_search_path('playlists').replace('_search.json', '_meta.json')) or {}
        return {'playlists': playlists, 'query': meta.get('query', '')}

    def save_media_index_snapshot(self, videos: Dict, playlists: Dict) -> None:
        try:
            base = ConfigManager.get_data_dir()
            path = os.path.join(base, 'media_index.json')
        except Exception:
            try:
                path = 'media_index.json'
            except Exception:
                return
        data = {
            'videos': videos or {},
            'playlists': playlists or {}
        }
        ConfigManager.save_json(path, data)

    def load_media_index_snapshot(self) -> Dict:
        try:
            base = ConfigManager.get_data_dir()
            path = os.path.join(base, 'media_index.json')
        except Exception:
            path = 'media_index.json'
        data = ConfigManager.load_json(path) or {}
        return {
            'videos': data.get('videos', {}),
            'playlists': data.get('playlists', {})
        }
