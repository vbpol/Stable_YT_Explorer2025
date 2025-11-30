import logging
import os
import pandas as pd
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

Base = declarative_base()

class BaseModel(Base):
    """Base model with common fields."""
    __abstract__ = True
    id = Column(String, primary_key=True)
    is_bookmarked = Column(Boolean, default=False)  # Indicates if the item is bookmarked
    is_downloaded = Column(Boolean, default=False)  # Indicates if the item has been downloaded
    remove_from_list = Column(Boolean, default=False)  # Indicates if the item is marked for removal

class Playlist(BaseModel):
    __tablename__ = 'playlists'
    title = Column(String, nullable=False)
    description = Column(String)
    videos = relationship('Video', back_populates='playlist')

    def __init__(self, title, description=None):
        self.title = title
        self.description = description
        logging.info(f"Playlist created: {self.title}")

    def get_number_of_videos(self, session):
        """Get the number of videos in the playlist."""
        return session.query(Video).filter(Video.playlist_id == self.id).count()

    def get_videos(self, session):
        """Get a list of videos in the playlist."""
        return session.query(Video).filter(Video.playlist_id == self.id).all()

    def get_videos_df(self, session):
        """Get a Pandas DataFrame of videos for the playlist."""
        videos = self.get_videos(session)
        data = {
            'Title': [video.title for video in videos],
            'Channel': [video.get_channel_title() for video in videos],  # Assuming this method exists
            'is_bookmarked': [video.is_bookmarked for video in videos],
            'is_downloaded': [video.is_downloaded for video in videos],
            'remove_from_list': [video.remove_from_list for video in videos],
        }
        return pd.DataFrame(data)

class Video(BaseModel):
    __tablename__ = 'videos'
    title = Column(String, nullable=False)
    description = Column(String)
    playlist_id = Column(String, ForeignKey('playlists.id'), nullable=False)
    playlist = relationship('Playlist', back_populates='videos')

    def __init__(self, title, playlist_id, description=None):
        self.title = title
        self.playlist_id = playlist_id
        self.description = description
        logging.info(f"Video created: {self.title} in playlist ID: {self.playlist_id}")

    def get_channel_title(self):
        """Get the channel title for the video."""
        # Implement logic to retrieve the channel title
        return "Channel Name"  # Placeholder

    def get_duration(self):
        """Get the duration of the video."""
        # Implement logic to retrieve the video duration
        return "00:00:00"  # Placeholder

    def is_downloaded(self, downloads_folder):
        """Check if the video is downloaded."""
        video_file_path = os.path.join(downloads_folder, f"{self.title}.mp4")  # Assuming .mp4 format
        return os.path.exists(video_file_path)

    def to_dataframe(self):
        """Get a Pandas DataFrame for displaying video info."""
        data = {
            'Title': self.title,
            'Playlist': self.playlist.title if self.playlist else None,
            'Channel': self.get_channel_title(),
            'Duration': self.get_duration(),
            'is_bookmarked': self.is_bookmarked,
            'is_downloaded': self.is_downloaded,
            'remove_from_list': self.remove_from_list,
        }
        return pd.DataFrame([data])
