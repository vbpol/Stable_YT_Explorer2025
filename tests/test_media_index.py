import unittest
from src.services.media_index import MediaIndex, VideoModel, PlaylistModel

class TestMediaIndex(unittest.TestCase):
    def setUp(self):
        self.index = MediaIndex()

    def test_add_videos(self):
        videos = [
            {'videoId': 'v1', 'title': 'Title 1', 'channelTitle': 'Channel 1'},
            {'videoId': 'v2', 'title': 'Title 2'}
        ]
        self.index.add_videos(videos)
        self.assertEqual(len(self.index.videos), 2)
        self.assertEqual(self.index.videos['v1'].title, 'Title 1')
        self.assertEqual(self.index.videos['v2'].title, 'Title 2')

    def test_add_playlists(self):
        playlists = [
            {'playlistId': 'pl1', 'title': 'PL 1', 'video_count': 10},
            {'id': 'pl2', 'title': 'PL 2'}
        ]
        self.index.add_playlists(playlists)
        self.assertEqual(len(self.index.playlists), 2)
        self.assertEqual(self.index.playlists['pl1'].title, 'PL 1')
        self.assertEqual(self.index.playlists['pl2'].title, 'PL 2')

    def test_link_video_to_playlist(self):
        self.index.link_video_to_playlist('pl1', 'v1')
        
        # Check playlist side
        pl = self.index.get_playlist('pl1')
        self.assertIsNotNone(pl)
        self.assertIn('v1', pl.video_ids)
        
        # Check video side (video didn't exist before, should be created?)
        # Implementation of link_video_to_playlist:
        # v = self.videos.get(video_id)
        # if v: v.playlistId = playlist_id
        # So if video doesn't exist, it only updates playlist.
        
        v = self.index.videos.get('v1')
        self.assertIsNone(v) # As per current implementation

        # Now add video and link
        self.index.add_videos([{'videoId': 'v1'}])
        self.index.link_video_to_playlist('pl1', 'v1', index=5)
        
        v = self.index.videos.get('v1')
        self.assertIsNotNone(v)
        self.assertEqual(v.playlistId, 'pl1')
        self.assertEqual(v.playlistIndex, 5)

    def test_bulk_link(self):
        self.index.add_videos([{'videoId': 'v1'}, {'videoId': 'v2'}])
        self.index.bulk_link_playlist_videos('pl1', ['v1', 'v2'])
        
        pl = self.index.get_playlist('pl1')
        self.assertEqual(pl.video_ids, {'v1', 'v2'})
        
        self.assertEqual(self.index.videos['v1'].playlistId, 'pl1')
        self.assertEqual(self.index.videos['v2'].playlistId, 'pl1')

    def test_get_playlist_video_ids(self):
        self.index.link_video_to_playlist('pl1', 'v1')
        ids = self.index.get_playlist_video_ids('pl1')
        self.assertEqual(ids, {'v1'})
        
        ids_empty = self.index.get_playlist_video_ids('nonexistent')
        self.assertEqual(ids_empty, set())

    def test_get_video_playlist(self):
        self.index.add_videos([{'videoId': 'v1'}])
        self.index.link_video_to_playlist('pl1', 'v1')
        self.assertEqual(self.index.get_video_playlist('v1'), 'pl1')
        self.assertIsNone(self.index.get_video_playlist('v2'))

    def test_serialization(self):
        self.index.add_videos([{'videoId': 'v1', 'title': 'T1'}])
        self.index.add_playlists([{'playlistId': 'pl1', 'title': 'P1'}])
        self.index.link_video_to_playlist('pl1', 'v1', 1)
        
        data = self.index.to_dict()
        
        new_index = MediaIndex()
        new_index.load_from_dict(data)
        
        self.assertEqual(len(new_index.videos), 1)
        self.assertEqual(len(new_index.playlists), 1)
        self.assertEqual(new_index.videos['v1'].title, 'T1')
        self.assertEqual(new_index.videos['v1'].playlistId, 'pl1')
        self.assertEqual(new_index.videos['v1'].playlistIndex, 1)
        self.assertEqual(new_index.playlists['pl1'].video_ids, {'v1'})

if __name__ == '__main__':
    unittest.main()
