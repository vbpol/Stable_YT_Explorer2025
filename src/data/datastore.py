from typing import List, Dict, Optional

class DataStore:
    def save_last_videos_result(self, query: str, videos: List[Dict], playlists: List[Dict], next_token: Optional[str], prev_token: Optional[str], video_ids: List[str]) -> None:
        raise NotImplementedError

    def load_last_videos_result(self) -> Dict:
        raise NotImplementedError

    def save_last_playlists_result(self, query: str, playlists: List[Dict]) -> None:
        raise NotImplementedError

    def load_last_playlists_result(self) -> Dict:
        raise NotImplementedError