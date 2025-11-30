import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import timedelta
import isodate
import json

class Playlist:
    def __init__(self, api_key):
        self.youtube = build('youtube', 'v3', developerKey=api_key)

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

    def search_videos(self, query, max_results=10, page_token=None):
        request = self.youtube.search().list(
            part="snippet",
            maxResults=max_results,
            q=query,
            type="video",
            pageToken=page_token
        )
        try:
            response = request.execute()
        except HttpError as err:
            try:
                data = json.loads(err.content.decode())
                reason = data.get("error", {}).get("errors", [{}])[0].get("reason", "unknown")
                message = data.get("error", {}).get("message", "")
                raise Exception(f"API error: {reason}: {message}")
            except Exception:
                raise Exception("API error while searching videos")

        video_ids = [item['id']['videoId'] for item in response.get('items', [])]
        details = self._get_video_details(video_ids)

        videos = []
        for item in response.get('items', []):
            vid = item['id']['videoId']
            d = details.get(vid, {})
            videos.append({
                'videoId': vid,
                'title': item['snippet']['title'],
                'channelTitle': item['snippet']['channelTitle'],
                'channelId': item['snippet']['channelId'],
                'duration': d.get('duration', 'N/A'),
                'published': d.get('published', ''),
                'views': d.get('views', '0')
            })
        return {
            'videos': videos,
            'nextPageToken': response.get('nextPageToken'),
            'prevPageToken': response.get('prevPageToken')
        }

    def get_channel_playlists(self, channel_id, max_results=10):
        request = self.youtube.playlists().list(
            part="snippet,contentDetails",
            channelId=channel_id,
            maxResults=max_results
        )
        try:
            response = request.execute()
        except HttpError as err:
            try:
                data = json.loads(err.content.decode())
                reason = data.get("error", {}).get("errors", [{}])[0].get("reason", "unknown")
                message = data.get("error", {}).get("message", "")
                raise Exception(f"API error: {reason}: {message}")
            except Exception:
                raise Exception("API error while getting channel playlists")

        playlists = []
        for item in response.get('items', []):
            playlists.append({
                'playlistId': item['id'],
                'title': item['snippet']['title'],
                'channelTitle': item['snippet']['channelTitle'],
                'thumbnail': item['snippet']['thumbnails'].get('default', {}).get('url', '')
            })
        return playlists

    def get_details(self, playlist_id):
        """Get the number of videos in a playlist."""
        request = self.youtube.playlists().list(
            part="contentDetails",
            id=playlist_id
        )
        response = request.execute()
        return response['items'][0]['contentDetails']['itemCount']

    def get_videos(self, playlist_id, page_token=None, max_results=10):
        """Get videos from a playlist with pagination."""
        request = self.youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=max_results,
            pageToken=page_token
        )
        response = request.execute()

        # Get video durations
        video_ids = [item['contentDetails']['videoId'] for item in response['items']]
        durations = self._get_video_durations(video_ids)
        details = self._get_video_details(video_ids)

        videos = []
        for item in response['items']:
            video_id = item['contentDetails']['videoId']
            video = {
                'videoId': video_id,
                'title': item['snippet']['title'],
                'channelTitle': item['snippet'].get('channelTitle', ''),
                'duration': durations.get(video_id, 'N/A'),
                'published': details.get(video_id, {}).get('published', ''),
                'views': details.get(video_id, {}).get('views', '0')
            }
            videos.append(video)

        return {
            'videos': videos,
            'nextPageToken': response.get('nextPageToken'),
            'prevPageToken': response.get('prevPageToken')
        }

    def get_playlists_by_video(self, video_id, max_results=50):
        """Return playlists that contain the specified video."""
        # Not supported directly by API; use helper on channel playlists externally
        return []

    def playlist_contains_video(self, playlist_id, video_id):
        """Return True if a playlist includes the given video (fast check)."""
        try:
            resp = self.youtube.playlistItems().list(
                part="id",
                playlistId=playlist_id,
                videoId=video_id,
                maxResults=1
            ).execute()
            return len(resp.get('items', [])) > 0
        except HttpError:
            return False

    def _get_video_durations(self, video_ids):
        """Get durations for a list of videos."""
        if not video_ids:
            return {}

        request = self.youtube.videos().list(
            part="contentDetails",
            id=','.join(video_ids)
        )
        response = request.execute()

        durations = {}
        for item in response['items']:
            duration = isodate.parse_duration(item['contentDetails']['duration'])
            formatted = str(timedelta(seconds=int(duration.total_seconds())))
            if formatted.startswith('0:'):  # Remove leading 0 hour
                formatted = formatted[2:]
            durations[item['id']] = formatted

        return durations

    def _get_video_details(self, video_ids):
        if not video_ids:
            return {}
        request = self.youtube.videos().list(
            part="contentDetails,snippet,statistics",
            id=','.join(video_ids)
        )
        try:
            response = request.execute()
        except HttpError as err:
            try:
                data = json.loads(err.content.decode())
                reason = data.get("error", {}).get("errors", [{}])[0].get("reason", "unknown")
                message = data.get("error", {}).get("message", "")
                raise Exception(f"API error: {reason}: {message}")
            except Exception:
                raise Exception("API error while getting video details")
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