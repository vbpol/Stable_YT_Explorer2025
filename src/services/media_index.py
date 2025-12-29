from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional


@dataclass
class VideoModel:
    videoId: str
    title: str = ''
    channelTitle: str = ''
    channelId: str = ''
    duration: str = 'N/A'
    published: str = ''
    views: str = '0'
    playlistId: Optional[str] = None
    playlistIndex: Optional[int] = None

    @staticmethod
    def from_dict(d: Dict) -> 'VideoModel':
        return VideoModel(
            videoId=d.get('videoId'),
            title=d.get('title',''),
            channelTitle=d.get('channelTitle',''),
            channelId=d.get('channelId',''),
            duration=d.get('duration','N/A'),
            published=d.get('published',''),
            views=d.get('views','0'),
            playlistId=d.get('playlistId'),
            playlistIndex=d.get('playlistIndex')
        )


@dataclass
class PlaylistModel:
    playlistId: str
    title: str = ''
    channelTitle: str = ''
    video_count: int | str = 'N/A'
    video_ids: Set[str] = field(default_factory=set)

    @staticmethod
    def from_dict(d: Dict) -> 'PlaylistModel':
        return PlaylistModel(
            playlistId=d.get('playlistId') or d.get('id') or d.get('playlist_id'),
            title=d.get('title',''),
            channelTitle=d.get('channelTitle',''),
            video_count=d.get('video_count','N/A')
        )


import threading

class MediaIndex:
    def __init__(self):
        self.videos: Dict[str, VideoModel] = {}
        self.playlists: Dict[str, PlaylistModel] = {}
        self._lock = threading.Lock()

    def add_videos(self, videos: List[Dict]) -> None:
        with self._lock:
            for v in (videos or []):
                vid = v.get('videoId')
                if not vid:
                    continue
                self.videos[vid] = VideoModel.from_dict(v)

    def add_playlists(self, playlists: List[Dict]) -> None:
        with self._lock:
            for p in (playlists or []):
                pid = p.get('playlistId') or p.get('id') or p.get('playlist_id')
                if not pid:
                    continue
                cur = self.playlists.get(pid)
                if cur is None:
                    cur = PlaylistModel.from_dict(p)
                    self.playlists[pid] = cur
                else:
                    cur.title = p.get('title', cur.title)
                    cur.channelTitle = p.get('channelTitle', cur.channelTitle)
                    vc = p.get('video_count')
                    if vc is not None:
                        cur.video_count = vc

    def _link_no_lock(self, playlist_id: str, video_id: str, index: Optional[int] = None) -> None:
        """Internal helper for linking without acquiring the lock."""
        pl = self.playlists.setdefault(playlist_id, PlaylistModel(playlistId=playlist_id))
        pl.video_ids.add(video_id)
        v = self.videos.get(video_id)
        if v:
            v.playlistId = playlist_id
            if isinstance(index, int):
                v.playlistIndex = index

    def link_video_to_playlist(self, playlist_id: str, video_id: str, index: Optional[int] = None) -> None:
        if not playlist_id or not video_id:
            return
        with self._lock:
            self._link_no_lock(playlist_id, video_id, index)

    def bulk_link_playlist_videos(self, playlist_id: str, video_ids: List[str]) -> None:
        if not playlist_id or not video_ids:
            return
        with self._lock:
            for vid in video_ids:
                if vid:
                    self._link_no_lock(playlist_id, vid)

    def get_playlist_video_ids(self, playlist_id: str) -> Set[str]:
        with self._lock:
            pl = self.playlists.get(playlist_id)
            return set(pl.video_ids) if pl else set()

    def get_video_playlist(self, video_id: str) -> Optional[str]:
        with self._lock:
            v = self.videos.get(video_id)
            return v.playlistId if v else None

    def get_playlist(self, playlist_id: str) -> Optional[PlaylistModel]:
        with self._lock:
            return self.playlists.get(playlist_id)

