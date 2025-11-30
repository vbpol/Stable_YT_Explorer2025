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

    def upsert_playlist(self, pl: Dict) -> None:
        raise NotImplementedError

    def upsert_video(self, v: Dict) -> None:
        raise NotImplementedError

    def link_video_to_playlist(self, playlist_id: str, video_id: str, position: Optional[int] = None) -> None:
        raise NotImplementedError

    def get_playlist_videos(self, playlist_id: str, limit: int, offset: int) -> List[Dict]:
        raise NotImplementedError
