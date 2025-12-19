from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import timedelta
import isodate
from typing import List, Dict, Any, Optional

try:
    from src.logger import setup_logger
    logger = setup_logger()
except ImportError:
    import logging
    logger = logging.getLogger("Playlist")

class PlaylistError(Exception):
    """Custom exception for playlist operations."""
    pass

class Playlist:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key is required")
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self._contains_cache = {}

    def search_playlists(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for playlists matching the query."""
        if not query:
            return []
        try:
            request = self.youtube.search().list(
                part="snippet",
                maxResults=max_results,
                q=query,
                type="playlist"
            )
            response = request.execute()
    
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
        except HttpError as e:
            logger.error(f"YouTube API error during search: {e}")
            raise PlaylistError(f"YouTube API error during search: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            raise PlaylistError(f"Unexpected error during search: {e}")

    def get_details(self, playlist_id: str) -> int:
        """Get the number of videos in a playlist."""
        if not playlist_id:
            raise ValueError("playlist_id is required")
        try:
            request = self.youtube.playlists().list(
                part="contentDetails",
                id=playlist_id
            )
            response = request.execute()
            items = response.get('items', [])
            if not items:
                raise PlaylistError(f"Playlist {playlist_id} not found")
            return items[0]['contentDetails']['itemCount']

        except HttpError as e:
            logger.error(f"YouTube API error getting details: {e}")
            raise PlaylistError(f"YouTube API error getting details: {e}")

    def get_playlist_info(self, playlist_id: str) -> Dict[str, Any]:
        if not playlist_id:
            raise ValueError("playlist_id is required")
        try:
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

        except Exception as e:
            logger.error(f"Error getting playlist info: {e}")
            raise PlaylistError(f"Error getting playlist info: {e}")

    def search_videos(self, query: str, max_results: int = 10, page_token: Optional[str] = None) -> Dict[str, Any]:
        if not query:
            return {'videos': [], 'nextPageToken': None, 'prevPageToken': None}
        try:
            request = self.youtube.search().list(
                part="snippet",
                maxResults=max_results,
                q=query,
                type="video",
                pageToken=page_token
            )
            response = request.execute()
            video_ids = [item['id']['videoId'] for item in response.get('items', [])]
            durations = self._get_video_durations(video_ids)
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
                    'duration': durations.get(vid, 'N/A'),
                    'published': d.get('published', ''),
                    'views': d.get('views', '0')
                })
            return {
                'videos': videos,
                'nextPageToken': response.get('nextPageToken'),
                'prevPageToken': response.get('prevPageToken')
            }

        except Exception as e:
            logger.error(f"Error searching videos: {e}")
            raise PlaylistError(f"Error searching videos: {e}")

    def get_videos(self, playlist_id: str, page_token: Optional[str] = None, max_results: int = 10) -> Dict[str, Any]:
        """Get videos from a playlist with pagination."""
        if not playlist_id:
            raise ValueError("playlist_id is required")
        try:
            request = self.youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=max_results,
                pageToken=page_token
            )
            response = request.execute()
    
            video_ids = [item['contentDetails']['videoId'] for item in response.get('items', [])]
            durations = self._get_video_durations(video_ids)
            details = self._get_video_details(video_ids)
    
            videos = []
            for item in response.get('items', []):
                video_id = item['contentDetails']['videoId']
                d = details.get(video_id, {})
                video = {
                    'videoId': video_id,
                    'title': item['snippet']['title'],
                    'channelTitle': item['snippet'].get('channelTitle', ''),
                    'duration': durations.get(video_id, 'N/A'),
                    'published': d.get('published', ''),
                    'views': d.get('views', '0')
                }
                videos.append(video)
    
            return {
                'videos': videos,
                'nextPageToken': response.get('nextPageToken'),
                'prevPageToken': response.get('prevPageToken')
            }

        except Exception as e:
            logger.error(f"Error getting videos from playlist: {e}")
            raise PlaylistError(f"Error getting videos from playlist: {e}")

    def _get_video_durations(self, video_ids: List[str]) -> Dict[str, str]:
        """Get durations for a list of videos."""
        if not video_ids:
            return {}
        try:
            request = self.youtube.videos().list(
                part="contentDetails",
                id=','.join(video_ids)
            )
            response = request.execute()
    
            durations = {}
            for item in response.get('items', []):
                duration = isodate.parse_duration(item['contentDetails']['duration'])
                formatted = str(timedelta(seconds=int(duration.total_seconds())))
                if formatted.startswith('0:'):  # Remove leading 0 hour
                    formatted = formatted[2:]
                durations[item['id']] = formatted
    
            return durations 
 
        except Exception as e:
            logger.error(f"Error getting video durations: {e}")
            return {}

    def _get_video_details(self, video_ids: List[str]) -> Dict[str, Dict[str, str]]:
        if not video_ids:
            return {}
        try:
            request = self.youtube.videos().list(
                part="contentDetails,snippet,statistics",
                id=','.join(video_ids)
            )
            response = request.execute()
            result = {}
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
            return result

        except Exception as e:
            logger.error(f"Error getting video details: {e}")
            return {}

    def get_channel_playlists(self, channel_id: str, max_results: int = 10) -> List[Dict[str, str]]:
        if not channel_id:
            raise ValueError("channel_id is required")
        try:
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

        except Exception as e:
            logger.error(f"Error getting channel playlists: {e}")
            raise PlaylistError(f"Error getting channel playlists: {e}")

    def playlist_contains_video(self, playlist_id: str, video_id: str) -> bool:
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
