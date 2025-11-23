import unittest
from unittest.mock import patch, MagicMock
from playlist import Playlist

class TestPlaylist(unittest.TestCase):
    def setUp(self):
        """Set up the Playlist instance with a mock API key."""
        self.api_key = 'fake_api_key'
        self.playlist = Playlist(api_key=self.api_key)

    @patch('playlist.build')
    def test_search_playlists(self, mock_build):
        """Test searching for playlists."""
        # Mock the response from the YouTube API
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.search().list().execute.return_value = {
            'items': [
                {
                    'id': {'playlistId': 'PL123'},
                    'snippet': {
                        'title': 'Test Playlist',
                        'channelTitle': 'Test Channel',
                        'thumbnails': {'default': {'url': 'http://example.com/thumbnail.jpg'}}
                    }
                }
            ]
        }

        result = self.playlist.search_playlists('Test')
        expected = [{
            'playlistId': 'PL123',
            'title': 'Test Playlist',
            'channelTitle': 'Test Channel',
            'thumbnail': 'http://example.com/thumbnail.jpg'
        }]
        self.assertEqual(result, expected)

    @patch('playlist.build')
    def test_get_details(self, mock_build):
        """Test getting the number of videos in a playlist."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.playlists().list().execute.return_value = {
            'items': [{
                'contentDetails': {'itemCount': 5}
            }]
        }

        result = self.playlist.get_details('PL123')
        self.assertEqual(result, 5)

    @patch('playlist.build')
    def test_get_videos(self, mock_build):
        """Test getting videos from a playlist."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.playlistItems().list().execute.return_value = {
            'items': [
                {
                    'contentDetails': {'videoId': 'abc123'},
                    'snippet': {'title': 'Test Video'}
                }
            ],
            'nextPageToken': 'next_token',
            'prevPageToken': 'prev_token'
        }

        with patch.object(self.playlist, '_get_video_durations', return_value={'abc123': '00:02:30'}):
            result = self.playlist.get_videos('PL123')
            expected = {
                'videos': [{'videoId': 'abc123', 'title': 'Test Video', 'duration': '00:02:30'}],
                'nextPageToken': 'next_token',
                'prevPageToken': 'prev_token'
            }
            self.assertEqual(result, expected)

    @patch('playlist.build')
    def test_get_video_durations(self, mock_build):
        """Test getting video durations."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.videos().list().execute.return_value = {
            'items': [
                {
                    'id': 'abc123',
                    'contentDetails': {'duration': 'PT2M30S'}
                }
            ]
        }

        result = self.playlist._get_video_durations(['abc123'])
        expected = {'abc123': '0:02:30'}
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main() 