from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()

class BaseModel(Base):
    """Base model with common fields."""
    __abstract__ = True
    id = Column(String, primary_key=True)
    is_bookmarked = Column(Boolean, default=False)
    is_downloaded = Column(Boolean, default=False)
    remove_from_list = Column(Boolean, default=False)

class Playlist(BaseModel):
    __tablename__ = 'playlists'
    title = Column(String, nullable=False)
    description = Column(String)
    videos = relationship('Video', back_populates='playlist')

class Video(BaseModel):
    __tablename__ = 'videos'
    title = Column(String, nullable=False)
    description = Column(String)
    playlist_id = Column(String, ForeignKey('playlists.id'), nullable=False)
    playlist = relationship('Playlist', back_populates='videos')
