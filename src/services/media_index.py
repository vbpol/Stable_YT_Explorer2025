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


class MediaIndex:
    def __init__(self):
        self.videos: Dict[str, VideoModel] = {}
        self.playlists: Dict[str, PlaylistModel] = {}

    def add_videos(self, videos: List[Dict]) -> None:
        for v in (videos or []):
            vid = v.get('videoId')
            if not vid:
                continue
            self.videos[vid] = VideoModel.from_dict(v)

    def add_playlists(self, playlists: List[Dict]) -> None:
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

    def link_video_to_playlist(self, playlist_id: str, video_id: str, index: Optional[int] = None) -> None:
        if not playlist_id or not video_id:
            return
        pl = self.playlists.setdefault(playlist_id, PlaylistModel(playlistId=playlist_id))
        pl.video_ids.add(video_id)
        v = self.videos.get(video_id)
        if v:
            v.playlistId = playlist_id
            if isinstance(index, int):
                v.playlistIndex = index

    def bulk_link_playlist_videos(self, playlist_id: str, video_ids: List[str]) -> None:
        for vid in (video_ids or []):
            self.link_video_to_playlist(playlist_id, vid)

    def get_playlist_video_ids(self, playlist_id: str) -> Set[str]:
        pl = self.playlists.get(playlist_id)
        return set(pl.video_ids) if pl else set()

    def get_video_playlist(self, video_id: str) -> Optional[str]:
        v = self.videos.get(video_id)
        return v.playlistId if v else None

    def get_playlist(self, playlist_id: str) -> Optional[PlaylistModel]:
        return self.playlists.get(playlist_id)

    def to_dict(self) -> Dict:
        """Serialize the index to a dictionary."""
        return {
            "videos": {
                k: {
                    "videoId": v.videoId,
                    "title": v.title,
                    "channelTitle": v.channelTitle,
                    "channelId": v.channelId,
                    "duration": v.duration,
                    "published": v.published,
                    "views": v.views,
                    "playlistId": v.playlistId,
                    "playlistIndex": v.playlistIndex
                } for k, v in self.videos.items()
            },
            "playlists": {
                k: {
                    "playlistId": p.playlistId,
                    "title": p.title,
                    "channelTitle": p.channelTitle,
                    "video_count": p.video_count,
                    "video_ids": list(p.video_ids)
                } for k, p in self.playlists.items()
            }
        }

    def load_from_dict(self, data: Dict) -> None:
        """Load the index from a dictionary."""
        if not data:
            return
            
        # Load videos
        videos_data = data.get("videos", {})
        for vid, v_data in videos_data.items():
            if vid:
                self.videos[vid] = VideoModel.from_dict(v_data)
                
        # Load playlists
        playlists_data = data.get("playlists", {})
        for pid, p_data in playlists_data.items():
            if pid:
                pl = PlaylistModel.from_dict(p_data)
                # Restore video_ids set
                vids = p_data.get("video_ids")
                if vids:
                    pl.video_ids = set(vids)
                # Restore intersect_video_ids set
                ivids = p_data.get("intersect_video_ids")
                if ivids:
                    pl.intersect_video_ids = set(ivids)
                self.playlists[pid] = pl

