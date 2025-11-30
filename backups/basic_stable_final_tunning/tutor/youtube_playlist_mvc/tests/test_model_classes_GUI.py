import sys
import os
import unittest
import tkinter as tk
from tkinter import messagebox
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the src directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from models.models import Base, Playlist, Video  # Import your models

class TestModelClasses(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up the test database and create tables."""
        cls.engine = create_engine('sqlite:///:memory:')  # Use in-memory database for testing
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        """Create a new session for each test."""
        self.session = self.Session()

    def tearDown(self):
        """Close the session after each test."""
        self.session.close()

    def test_create_playlist(self):
        """Test creating a new playlist."""
        playlist = Playlist(title='Test Playlist', description='A playlist for testing.')
        self.session.add(playlist)
        self.session.commit()
        retrieved_playlist = self.session.query(Playlist).filter_by(title='Test Playlist').one()
        self.assertEqual(retrieved_playlist.title, 'Test Playlist')

    def test_create_video(self):
        """Test creating a new video."""
        playlist = Playlist(title='Test Playlist')
        self.session.add(playlist)
        self.session.commit()
        video = Video(title='Test Video', playlist_id=playlist.id, description='A video for testing.')
        self.session.add(video)
        self.session.commit()
        retrieved_video = self.session.query(Video).filter_by(title='Test Video').one()
        self.assertEqual(retrieved_video.title, 'Test Video')

    def test_get_number_of_videos(self):
        """Test getting the number of videos in a playlist."""
        playlist = Playlist(title='Test Playlist')
        self.session.add(playlist)
        self.session.commit()

        video1 = Video(title='Test Video 1', playlist_id=playlist.id)
        video2 = Video(title='Test Video 2', playlist_id=playlist.id)
        self.session.add(video1)
        self.session.add(video2)
        self.session.commit()

        self.assertEqual(playlist.get_number_of_videos(self.session), 2)

    def test_get_videos(self):
        """Test retrieving videos from a playlist."""
        playlist = Playlist(title='Test Playlist')
        self.session.add(playlist)
        self.session.commit()

        video1 = Video(title='Test Video 1', playlist_id=playlist.id)
        video2 = Video(title='Test Video 2', playlist_id=playlist.id)
        self.session.add(video1)
        self.session.add(video2)
        self.session.commit()

        videos = playlist.get_videos(self.session)
        self.assertEqual(len(videos), 2)

    def test_video_download_status(self):
        """Test checking if a video is downloaded."""
        video = Video(title='Test Video', playlist_id='dummy_playlist_id')
        self.assertFalse(video.is_downloaded('downloads'))  # Assuming the video is not downloaded

    def test_to_dataframe(self):
        """Test converting video information to a DataFrame."""
        playlist = Playlist(title='Test Playlist')
        self.session.add(playlist)
        self.session.commit()

        video = Video(title='Test Video', playlist_id=playlist.id)
        self.session.add(video)
        self.session.commit()

        df = video.to_dataframe()
        self.assertEqual(df.shape[0], 1)  # Check that the DataFrame has one row
        self.assertEqual(df['Title'][0], 'Test Video')

# GUI Application
class TestApp:
    def __init__(self, master):
        self.master = master
        master.title("Model Classes Test Runner")

        self.test_cases = [
            ("Create Playlist", self.run_test_create_playlist),
            ("Create Video", self.run_test_create_video),
        ]

        self.buttons = []
        for test_name, test_method in self.test_cases:
            button = tk.Button(master, text=test_name, command=test_method, width=20)
            button.pack(pady=10)
            self.buttons.append(button)

    def run_test_create_playlist(self):
        """Run the create playlist test."""
        self.run_test(TestModelClasses.test_create_playlist)

    def run_test_create_video(self):
        """Run the create video test."""
        self.run_test(TestModelClasses.test_create_video)

    def run_test(self, test_method):
        """Run a test method and update button color based on result."""
        suite = unittest.TestSuite()
        suite.addTest(TestModelClasses(test_method.__name__))
        result = unittest.TextTestRunner(verbosity=0).run(suite)

        # Update button color based on test result
        button = self.buttons[self.get_test_index(test_method)]
        if result.wasSuccessful():
            button.config(bg='green')
            messagebox.showinfo("Test Result", f"{test_method.__name__} passed!")
        else:
            button.config(bg='red')
            messagebox.showerror("Test Result", f"{test_method.__name__} failed!")

    def get_test_index(self, test_method):
        """Get the index of the test method in the test cases."""
        for index, (name, method) in enumerate(self.test_cases):
            if method == test_method:
                return index
        return -1

if __name__ == "__main__":
    root = tk.Tk()
    app = TestApp(root)
    root.mainloop() 