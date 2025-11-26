import os
import sqlite3
from typing import List, Dict, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'app.sqlite3')

class SqliteStore:
    def __init__(self):
        os.makedirs(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data'), exist_ok=True)
        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.conn.execute('PRAGMA foreign_keys=ON')
        self._init_schema()

    def _init_schema(self):
        cur = self.conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS playlists (playlist_id TEXT PRIMARY KEY, title TEXT, channel_title TEXT, video_count INTEGER, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)')
        cur.execute('CREATE TABLE IF NOT EXISTS videos (video_id TEXT PRIMARY KEY, title TEXT, channel_title TEXT, duration TEXT, published TEXT, views INTEGER)')
        cur.execute('CREATE TABLE IF NOT EXISTS playlist_videos (playlist_id TEXT, video_id TEXT, position INTEGER, PRIMARY KEY (playlist_id, video_id))')
        cur.execute('CREATE TABLE IF NOT EXISTS last_results (id INTEGER PRIMARY KEY AUTOINCREMENT, mode TEXT, query TEXT, saved_at DATETIME DEFAULT CURRENT_TIMESTAMP, next_page_token TEXT, prev_page_token TEXT)')
        cur.execute('CREATE TABLE IF NOT EXISTS last_result_videos (last_id INTEGER, video_id TEXT)')
        cur.execute('CREATE TABLE IF NOT EXISTS last_result_playlists (last_id INTEGER, playlist_id TEXT)')
        self.conn.commit()

    def upsert_playlist(self, pl: Dict):
        self.conn.execute('INSERT OR REPLACE INTO playlists (playlist_id, title, channel_title, video_count) VALUES (?,?,?,?)', (
            pl.get('playlistId'), pl.get('title'), pl.get('channelTitle'), self._to_int(pl.get('video_count'))
        ))

    def upsert_video(self, v: Dict):
        views = self._to_int(v.get('views'))
        self.conn.execute('INSERT OR REPLACE INTO videos (video_id, title, channel_title, duration, published, views) VALUES (?,?,?,?,?,?)', (
            v.get('videoId'), v.get('title'), v.get('channelTitle'), v.get('duration'), v.get('published'), views
        ))

    def link_video_to_playlist(self, playlist_id: str, video_id: str, position: Optional[int] = None):
        self.conn.execute('INSERT OR REPLACE INTO playlist_videos (playlist_id, video_id, position) VALUES (?,?,?)', (
            playlist_id, video_id, position
        ))

    def save_last_videos_result(self, query: str, videos: List[Dict], playlists: List[Dict], next_token: Optional[str], prev_token: Optional[str], video_ids: List[str]) -> None:
        cur = self.conn.cursor()
        cur.execute('INSERT INTO last_results (mode, query, next_page_token, prev_page_token) VALUES (?,?,?,?)', (
            'videos', query, next_token, prev_token
        ))
        last_id = cur.lastrowid
        for v in videos:
            self.upsert_video(v)
            cur.execute('INSERT INTO last_result_videos (last_id, video_id) VALUES (?,?)', (last_id, v.get('videoId')))
        for p in playlists:
            self.upsert_playlist(p)
            cur.execute('INSERT INTO last_result_playlists (last_id, playlist_id) VALUES (?,?)', (last_id, p.get('playlistId')))
        self.conn.commit()

    def load_last_videos_result(self) -> Dict:
        cur = self.conn.cursor()
        cur.execute("SELECT id, query, next_page_token, prev_page_token FROM last_results WHERE mode='videos' ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        if not row:
            return {'videos': [], 'playlists': [], 'nextPageToken': None, 'prevPageToken': None, 'query': ''}
        last_id = row[0]
        cur.execute('SELECT v.video_id, v.title, v.channel_title, v.duration, v.published, v.views FROM last_result_videos r JOIN videos v ON v.video_id=r.video_id WHERE r.last_id=?', (last_id,))
        videos = []
        video_ids = []
        for vr in cur.fetchall():
            videos.append({'videoId': vr[0], 'title': vr[1], 'channelTitle': vr[2], 'duration': vr[3], 'published': vr[4], 'views': vr[5]})
            video_ids.append(vr[0])
        cur.execute('SELECT p.playlist_id, p.title, p.channel_title, p.video_count FROM last_result_playlists r JOIN playlists p ON p.playlist_id=r.playlist_id WHERE r.last_id=?', (last_id,))
        playlists = []
        for pr in cur.fetchall():
            playlists.append({'playlistId': pr[0], 'title': pr[1], 'channelTitle': pr[2], 'video_count': pr[3]})
        return {'videos': videos, 'playlists': playlists, 'nextPageToken': row[2], 'prevPageToken': row[3], 'query': row[1], 'videoIds': video_ids}

    def save_last_playlists_result(self, query: str, playlists: List[Dict]) -> None:
        cur = self.conn.cursor()
        cur.execute('INSERT INTO last_results (mode, query) VALUES (?,?)', ('playlists', query))
        last_id = cur.lastrowid
        for p in playlists:
            self.upsert_playlist(p)
            cur.execute('INSERT INTO last_result_playlists (last_id, playlist_id) VALUES (?,?)', (last_id, p.get('playlistId')))
        self.conn.commit()

    def load_last_playlists_result(self) -> Dict:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM last_results WHERE mode='playlists' ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        if not row:
            return {'playlists': [], 'query': ''}
        last_id = row[0]
        cur.execute('SELECT query FROM last_results WHERE id=?', (last_id,))
        qrow = cur.fetchone()
        query = qrow[0] if qrow else ''
        cur.execute('SELECT p.playlist_id, p.title, p.channel_title, p.video_count FROM last_result_playlists r JOIN playlists p ON p.playlist_id=r.playlist_id WHERE r.last_id=?', (last_id,))
        playlists = []
        for pr in cur.fetchall():
            playlists.append({'playlistId': pr[0], 'title': pr[1], 'channelTitle': pr[2], 'video_count': pr[3]})
        return {'playlists': playlists, 'query': query}

    def _to_int(self, v):
        try:
            return int(v)
        except Exception:
            return None