import requests
import logging

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class YouTubeAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://www.googleapis.com/youtube/v3'

    def make_request(self, endpoint, params):
        """Make a GET request to the YouTube Data API."""
        params['key'] = self.api_key
        try:
            response = requests.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()  # Raise an error for bad responses
            logging.info(f"API request successful: {endpoint} with params {params}")
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred: {http_err}")
        except Exception as err:
            logging.error(f"An error occurred: {err}")
        return None

    def search(self, query, search_type, max_results=5):
        """Search for playlists or videos."""
        params = {
            'part': 'snippet',
            'q': query,
            'type': search_type,
            'maxResults': max_results
        }
        return self.make_request('search', params)

    def get_playlist_videos(self, playlist_id, max_results=5):
        """Retrieve videos from a playlist."""
        params = {
            'part': 'snippet',
            'playlistId': playlist_id,
            'maxResults': max_results
        }
        return self.make_request('playlistItems', params)

    def get_playlist_title_from_video(self, video_id):
        """Retrieve the playlist title if the video belongs to a playlist."""
        params = {'part': 'snippet', 'videoId': video_id}
        data = self.make_request('playlistItems', params)
        if data and 'items' in data and len(data['items']) > 0:
            return data['items'][0]['snippet'].get('playlistTitle')
        return None
