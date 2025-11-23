import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Playlist, Video  # Import your models

# Configure logging
logging.basicConfig(
    filename='app.log',  # Log file location
    level=logging.DEBUG,  # Log level
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_session(database_url='sqlite:///youtube.db'):
    """Create and return a new SQLAlchemy session."""
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        logging.info("Database session created successfully.")
        return Session()
    except Exception as e:
        logging.error(f"Failed to create database session: {e}")
        return None

def update_is_downloaded(entity, session, is_downloaded=True):
    """
    Update the is_downloaded field for a playlist or video in the database.
    :param entity: The playlist or video object to update
    :param session: The SQLAlchemy session
    :param is_downloaded: Boolean indicating whether the entity is downloaded
    """
    try:
        entity.is_downloaded = is_downloaded
        session.commit()
        logging.info(f"Updated is_downloaded for {entity.__class__.__name__} with ID: {entity.id}")
    except Exception as e:
        session.rollback()
        logging.error(f"Failed to update is_downloaded: {e}")

# CRUD Operations for Playlist
def create_playlist(session, title, description=None):
    """Create a new playlist."""
    try:
        new_playlist = Playlist(title=title, description=description)
        session.add(new_playlist)
        session.commit()
        logging.info(f"Created new playlist: {title}")
        return new_playlist
    except Exception as e:
        session.rollback()
        logging.error(f"Failed to create playlist: {e}")
        return None

def read_playlists(session):
    """Retrieve all playlists."""
    try:
        playlists = session.query(Playlist).all()
        logging.info("Retrieved all playlists.")
        return playlists
    except Exception as e:
        logging.error(f"Failed to retrieve playlists: {e}")
        return []

def update_playlist(session, playlist_id, title=None, description=None):
    """Update an existing playlist."""
    try:
        playlist = session.query(Playlist).filter(Playlist.id == playlist_id).one()
        if title:
            playlist.title = title
        if description:
            playlist.description = description
        session.commit()
        logging.info(f"Updated playlist ID {playlist_id}.")
        return playlist
    except Exception as e:
        session.rollback()
        logging.error(f"Failed to update playlist ID {playlist_id}: {e}")
        return None

def delete_playlist(session, playlist_id):
    """Delete a playlist."""
    try:
        playlist = session.query(Playlist).filter(Playlist.id == playlist_id).one()
        session.delete(playlist)
        session.commit()
        logging.info(f"Deleted playlist ID {playlist_id}.")
        return True
    except Exception as e:
        session.rollback()
        logging.error(f"Failed to delete playlist ID {playlist_id}: {e}")
        return False

# CRUD Operations for Video
def create_video(session, title, playlist_id, description=None):
    """Create a new video."""
    try:
        new_video = Video(title=title, playlist_id=playlist_id, description=description)
        session.add(new_video)
        session.commit()
        logging.info(f"Created new video: {title} in playlist ID {playlist_id}.")
        return new_video
    except Exception as e:
        session.rollback()
        logging.error(f"Failed to create video: {e}")
        return None

def read_videos(session, playlist_id):
    """Retrieve all videos from a specific playlist."""
    try:
        videos = session.query(Video).filter(Video.playlist_id == playlist_id).all()
        logging.info(f"Retrieved videos for playlist ID {playlist_id}.")
        return videos
    except Exception as e:
        logging.error(f"Failed to retrieve videos for playlist ID {playlist_id}: {e}")
        return []

def update_video(session, video_id, title=None, description=None):
    """Update an existing video."""
    try:
        video = session.query(Video).filter(Video.id == video_id).one()
        if title:
            video.title = title
        if description:
            video.description = description
        session.commit()
        logging.info(f"Updated video ID {video_id}.")
        return video
    except Exception as e:
        session.rollback()
        logging.error(f"Failed to update video ID {video_id}: {e}")
        return None

def delete_video(session, video_id):
    """Delete a video."""
    try:
        video = session.query(Video).filter(Video.id == video_id).one()
        session.delete(video)
        session.commit()
        logging.info(f"Deleted video ID {video_id}.")
        return True
    except Exception as e:
        session.rollback()
        logging.error(f"Failed to delete video ID {video_id}: {e}")
        return False
