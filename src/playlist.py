from googleapiclient.discovery import build
from datetime import timedelta
import isodate
from src.services.cache_manager import CacheManager

class Playlist:
    def __init__(self, api_key):
        self.api_key = api_key
        self._youtube = None
        self.cache = CacheManager()
        self._contains_cache = {}

    @property
    def youtube(self):
        if self._youtube is None:
            # cache_discovery=True is default, but explicit doesn't hurt.
            # It caches the discovery document to avoid an HTTP request for discovery.
            self._youtube = build('youtube', 'v3', developerKey=self.api_key, cache_discovery=True)
        return self._youtube

    def _execute_with_cache(self, resource_name, method_name, **kwargs):
        """
        Executes an API request with caching.
        resource_name: e.g. 'search', 'playlists', 'videos'
        method_name: e.g. 'list'
        kwargs: arguments for the method
        """
        params = kwargs.copy()
        
        # Check cache
        cached = self.cache.get('youtube', method_name, params)
        if cached:
            return cached
            
        # Execute request (lazy load service)
        # resource = self.youtube.search() -> getattr(self.youtube, 'search')()
        resource_factory = getattr(self.youtube, resource_name)
        resource = resource_factory()
        
        method = getattr(resource, method_name)
        request = method(**kwargs)
        response = request.execute()
        
        # Cache response
        self.cache.set('youtube', method_name, params, response)
        return response

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
        response = self._execute_with_cache(
            'search',
            'list',
            part="snippet",
            maxResults=max_results,
            q=query,
            type="playlist"
        )

        playlists = []
        for item in response.get('items', []):
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
        response = self._execute_with_cache(
            'playlists',
            'list',
            part="contentDetails",
            id=playlist_id
        )
        return response['items'][0]['contentDetails']['itemCount']

    def get_playlist_info(self, playlist_id):
        response = self._execute_with_cache(
            'playlists',
            'list',
            part="snippet,contentDetails",
            id=playlist_id
        )
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
                response = self._execute_with_cache(
                    'playlists',
                    'list',
                    part="contentDetails",
                    id=','.join(chunk)
                )
                for item in response.get('items', []):
                    pid = item['id']
                    count = item['contentDetails']['itemCount']
                    results[pid] = count
            except Exception:
                pass
        return results

    def search_videos(self, query, max_results=10, page_token=None):
        response = self._execute_with_cache(
            'search',
            'list',
            part="snippet",
            maxResults=max_results,
            q=query,
            type="video",
            pageToken=page_token
        )
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
            'prevPageToken': response.get('prevPageToken'),
            'totalResults': response.get('pageInfo', {}).get('totalResults')
        }

    def get_videos(self, playlist_id, page_token=None, max_results=10):
        """Get videos from a playlist with pagination."""
        response = self._execute_with_cache(
            'playlistItems',
            'list',
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=max_results,
            pageToken=page_token
        )

        video_ids = [item['contentDetails']['videoId'] for item in response.get('items', [])]
        # details now includes duration
        details = self._get_video_details(video_ids)

        videos = []
        for item in response.get('items', []):
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
                response = self._execute_with_cache(
                    'videos',
                    'list',
                    part="contentDetails,snippet,statistics",
                    id=','.join(chunk)
                )
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
        response = self._execute_with_cache(
            'playlists',
            'list',
            part="snippet,contentDetails",
            channelId=channel_id,
            maxResults=max_results
        )

        playlists = []
        for item in response.get('items', []):
            playlist = {
                'playlistId': item['id'],
                'title': item['snippet']['title'],
                'channelTitle': item['snippet']['channelTitle'],
                'video_count': item['contentDetails']['itemCount'],
                'thumbnail': item['snippet']['thumbnails']['default']['url']
            }
            playlists.append(playlist)
        return playlists

    def playlist_contains_video(self, playlist_id, video_id):
        if not playlist_id or not video_id:
            return False
            
        # 1. Check in-memory LRU cache first (fastest)
        key = (playlist_id, video_id)
        try:
            cached = self._contains_cache.get(key)
            if cached is not None:
                return cached
        except Exception:
            pass
            
        # 2. Check persistent cache via _execute_with_cache
        # Note: We can't easily cache "contains" result directly as boolean in CacheManager 
        # because CacheManager stores API responses.
        # But we can cache the playlistItems.list call.
        
        try:
            resp = self._execute_with_cache(
                'playlistItems',
                'list',
                part="id",
                playlistId=playlist_id,
                videoId=video_id,
                maxResults=1
            )
            has = len(resp.get('items', [])) > 0
        except Exception:
            has = False
            
        # Update in-memory cache
        try:
            if len(self._contains_cache) > 4000:
                self._contains_cache.clear()
            self._contains_cache[key] = has
        except Exception:
            pass
            
        return has
