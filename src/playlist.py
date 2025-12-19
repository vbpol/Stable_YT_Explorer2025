from googleapiclient.discovery import build
from datetime import timedelta
import isodate

class Playlist:
    def __init__(self, api_key):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self._contains_cache = {}

    def validate_key(self):
        """
        Validate the API key using a low-cost endpoint (1 quota unit).
        Using channels list for 'GoogleDevelopers' as recommended.
        Returns True if valid, raises HttpError if invalid or quota exceeded.
        """
        self.youtube.channels().list(
            part="id",
            forUsername="GoogleDevelopers"
        ).execute()
        return True

    def search_playlists(self, query, max_results=10):
        """Search for playlists matching the query."""
        request = self.youtube.search().list(
            part="snippet",
            maxResults=max_results,
            q=query,
            type="playlist"
        )
        response = request.execute()

        playlists = []
        for item in response['items']:
            playlist = {
                'playlistId': item['id']['playlistId'],
                'title': item['snippet']['title'],
                'channelTitle': item['snippet']['channelTitle'],
                'thumbnail': item['snippet']['thumbnails']['default']['url']
            }
            playlists.append(playlist)
        return playlists

    def get_details(self, playlist_id):
        """Get the number of videos in a playlist."""
        request = self.youtube.playlists().list(
            part="contentDetails",
            id=playlist_id
        )
        response = request.execute()
        return response['items'][0]['contentDetails']['itemCount']

    def get_playlist_info(self, playlist_id):
        request = self.youtube.playlists().list(
            part="snippet,contentDetails",
            id=playlist_id
        )
        response = request.execute()
        items = response.get('items', [])
        if not items:
            return {'playlistId': playlist_id, 'title': '', 'channelTitle': '', 'video_count': 'N/A'}
        it = items[0]
        title = it.get('snippet', {}).get('title', '')
        channel = it.get('snippet', {}).get('channelTitle', '')
        count = it.get('contentDetails', {}).get('itemCount', 'N/A')
        try:
            count = int(count)
        except Exception:
            pass
        return {'playlistId': playlist_id, 'title': title, 'channelTitle': channel, 'video_count': count}

    def get_playlists_details(self, playlist_ids):
        """Get details for multiple playlists in one batch request."""
        if not playlist_ids:
            return {}
        
        # Process in batches of 50
        results = {}
        chunk_size = 50
        for i in range(0, len(playlist_ids), chunk_size):
            chunk = playlist_ids[i:i + chunk_size]
            try:
                request = self.youtube.playlists().list(
                    part="contentDetails",
                    id=','.join(chunk)
                )
                response = request.execute()
                for item in response.get('items', []):
                    pid = item['id']
                    count = item['contentDetails']['itemCount']
                    results[pid] = count
            except Exception:
                pass
        return results

    def search_videos(self, query, max_results=10, page_token=None):
        request = self.youtube.search().list(
            part="snippet",
            maxResults=max_results,
            q=query,
            type="video",
            pageToken=page_token
        )
        response = request.execute()
        video_ids = [item['id']['videoId'] for item in response.get('items', [])]
        # details now includes duration
        details = self._get_video_details(video_ids)
        videos = []
        for item in response.get('items', []):
            vid = item['id']['videoId']
            d = details.get(vid, {})
            videos.append({
                'videoId': vid,
                'title': item['snippet']['title'],
                'channelTitle': item['snippet'].get('channelTitle',''),
                'channelId': item['snippet'].get('channelId',''),
                'duration': d.get('duration', 'N/A'),
                'published': d.get('published', ''),
                'views': d.get('views', '0')
            })
        return {
            'videos': videos,
            'nextPageToken': response.get('nextPageToken'),
            'prevPageToken': response.get('prevPageToken')
        }

    def get_videos(self, playlist_id, page_token=None, max_results=10):
        """Get videos from a playlist with pagination."""
        request = self.youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=max_results,
            pageToken=page_token
        )
        response = request.execute()

        video_ids = [item['contentDetails']['videoId'] for item in response['items']]
        # details now includes duration
        details = self._get_video_details(video_ids)

        videos = []
        for item in response['items']:
            video_id = item['contentDetails']['videoId']
            d = details.get(video_id, {})
            video = {
                'videoId': video_id,
                'title': item['snippet']['title'],
                'channelTitle': item['snippet'].get('channelTitle', ''),
                'duration': d.get('duration', 'N/A'),
                'published': d.get('published', ''),
                'views': d.get('views', '0')
            }
            videos.append(video)

        return {
            'videos': videos,
            'nextPageToken': response.get('nextPageToken'),
            'prevPageToken': response.get('prevPageToken')
        }

    def _get_video_details(self, video_ids):
        if not video_ids:
            return {}
        
        # Batch in groups of 50
        result = {}
        chunk_size = 50
        
        for i in range(0, len(video_ids), chunk_size):
            chunk = video_ids[i:i + chunk_size]
            try:
                request = self.youtube.videos().list(
                    part="contentDetails,snippet,statistics",
                    id=','.join(chunk)
                )
                response = request.execute()
                for item in response.get('items', []):
                    try:
                        dur = isodate.parse_duration(item['contentDetails']['duration'])
                        duration = str(timedelta(seconds=int(dur.total_seconds())))
                        if duration.startswith('0:'):
                            duration = duration[2:]
                    except Exception:
                        duration = 'N/A'
                    published = item.get('snippet', {}).get('publishedAt', '')
                    views = item.get('statistics', {}).get('viewCount', '0')
                    result[item['id']] = {
                        'duration': duration,
                        'published': published,
                        'views': views
                    }
            except Exception:
                pass
                
        return result

    def get_channel_playlists(self, channel_id, max_results=10):
        request = self.youtube.playlists().list(
            part="snippet,contentDetails",
            channelId=channel_id,
            maxResults=max_results
        )
        response = request.execute()
        playlists = []
        for item in response.get('items', []):
            playlists.append({
                'playlistId': item['id'],
                'title': item['snippet']['title'],
                'channelTitle': item['snippet']['channelTitle'],
            })
        return playlists

    def playlist_contains_video(self, playlist_id, video_id):
        if not playlist_id or not video_id:
            return False
        key = (playlist_id, video_id)
        try:
            cached = self._contains_cache.get(key)
            if cached is not None:
                return cached
        except Exception:
            pass
        try:
            resp = self.youtube.playlistItems().list(
                part="id",
                playlistId=playlist_id,
                videoId=video_id,
                maxResults=1
            ).execute()
            has = len(resp.get('items', [])) > 0
        except Exception:
            has = False
        try:
            if len(self._contains_cache) > 4000:
                self._contains_cache.clear()
            self._contains_cache[key] = has
        except Exception:
            pass
        return has
