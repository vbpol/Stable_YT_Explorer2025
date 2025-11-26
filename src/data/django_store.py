import os
from typing import List, Dict, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'app.sqlite3')

class DjangoStore:
    def __init__(self):
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure(
                INSTALLED_APPS=['django.contrib.contenttypes', 'backend.media'],
                DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': DB_FILE}},
                USE_TZ=False,
                SECRET_KEY='basic-final-secret',
            )
            django.setup()
        # Import models after setup
        from backend.media.models import Playlist, Video, PlaylistVideo, LastResult, LastResultVideo, LastResultPlaylist
        self.Playlist = Playlist
        self.Video = Video
        self.PlaylistVideo = PlaylistVideo
        self.LastResult = LastResult
        self.LastResultVideo = LastResultVideo
        self.LastResultPlaylist = LastResultPlaylist

    def upsert_playlist(self, pl: Dict):
        self.Playlist.objects.update_or_create(
            playlist_id=pl.get('playlistId'),
            defaults={
                'title': pl.get('title'),
                'channel_title': pl.get('channelTitle'),
                'video_count': self._to_int(pl.get('video_count')),
            }
        )

    def upsert_video(self, v: Dict):
        self.Video.objects.update_or_create(
            video_id=v.get('videoId'),
            defaults={
                'title': v.get('title'),
                'channel_title': v.get('channelTitle'),
                'duration': v.get('duration'),
                'published': v.get('published'),
                'views': self._to_int(v.get('views')),
            }
        )

    def link_video_to_playlist(self, playlist_id: str, video_id: str, position: Optional[int] = None):
        pl = self.Playlist.objects.filter(playlist_id=playlist_id).first()
        vd = self.Video.objects.filter(video_id=video_id).first()
        if not pl or not vd:
            return
        self.PlaylistVideo.objects.update_or_create(
            playlist=pl, video=vd,
            defaults={'position': position}
        )

    def save_last_videos_result(self, query: str, videos: List[Dict], playlists: List[Dict], next_token: Optional[str], prev_token: Optional[str], video_ids: List[str]) -> None:
        last = self.LastResult.objects.create(mode='videos', query=query, next_page_token=next_token, prev_page_token=prev_token)
        for v in videos:
            self.upsert_video(v)
            vid = v.get('videoId')
            if vid:
                self.LastResultVideo.objects.create(last=last, video_id=vid)
        for p in playlists:
            self.upsert_playlist(p)
            pid = p.get('playlistId')
            if pid:
                self.LastResultPlaylist.objects.create(last=last, playlist_id=pid)

    def load_last_videos_result(self) -> Dict:
        last = self.LastResult.objects.filter(mode='videos').order_by('-id').first()
        if not last:
            return {'videos': [], 'playlists': [], 'nextPageToken': None, 'prevPageToken': None, 'query': ''}
        vids = []
        v_ids = []
        for rv in self.LastResultVideo.objects.filter(last=last).select_related('video'):
            v = rv.video
            vids.append({'videoId': v.video_id, 'title': v.title, 'channelTitle': v.channel_title, 'duration': v.duration, 'published': v.published, 'views': v.views})
            v_ids.append(v.video_id)
        pls = []
        for rp in self.LastResultPlaylist.objects.filter(last=last).select_related('playlist'):
            p = rp.playlist
            pls.append({'playlistId': p.playlist_id, 'title': p.title, 'channelTitle': p.channel_title, 'video_count': p.video_count})
        return {'videos': vids, 'playlists': pls, 'nextPageToken': last.next_page_token, 'prevPageToken': last.prev_page_token, 'query': last.query, 'videoIds': v_ids}

    def save_last_playlists_result(self, query: str, playlists: List[Dict]) -> None:
        last = self.LastResult.objects.create(mode='playlists', query=query)
        for p in playlists:
            self.upsert_playlist(p)
            pid = p.get('playlistId')
            if pid:
                self.LastResultPlaylist.objects.create(last=last, playlist_id=pid)

    def load_last_playlists_result(self) -> Dict:
        last = self.LastResult.objects.filter(mode='playlists').order_by('-id').first()
        if not last:
            return {'playlists': [], 'query': ''}
        pls = []
        for rp in self.LastResultPlaylist.objects.filter(last=last).select_related('playlist'):
            p = rp.playlist
            pls.append({'playlistId': p.playlist_id, 'title': p.title, 'channelTitle': p.channel_title, 'video_count': p.video_count})
        return {'playlists': pls, 'query': last.query}

    def _to_int(self, v):
        try:
            return int(v)
        except Exception:
            return None