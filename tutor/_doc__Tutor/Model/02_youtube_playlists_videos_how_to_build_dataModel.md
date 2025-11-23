# How to Build a Data Model for Playlists and Videos in an MVC Approach

This tutorial explains how to design a data model for playlists and their videos using an MVC (Model-View-Controller) approach.

---

## Scalability and DRY Principle

To ensure the data model is scalable and adheres to the DRY principle:
1. **Reusable Base Model**:
   - Create a base model class to handle common fields and methods.
2. **Extendable Relationships**:
   - Use SQLAlchemy relationships to manage associations between playlists and videos dynamically.

---

## Overview of the Data Model

The data model consists of two main entities:
1. **Playlist**: Represents a YouTube playlist.
2. **Video**: Represents a video within a playlist.

### Relationships
- A **Playlist** can have multiple **Videos**.
- Each **Video** belongs to a single **Playlist**.

---

## Playlist Model

The **Playlist** model includes the following fields:
- `id`: Unique identifier for the playlist.
- `title`: Title of the playlist.
- `description`: Description of the playlist.
- `is_bookmarked`: Boolean indicating if the playlist is bookmarked.
- `is_downloaded`: Boolean indicating if the playlist has been downloaded.
- `remove_from_list`: Boolean indicating if the playlist is marked for removal.

---

## Video Model

The **Video** model includes the following fields:
- `id`: Unique identifier for the video.
- `title`: Title of the video.
- `description`: Description of the video.
- `playlist_id`: Foreign key linking the video to its playlist.
- `is_bookmarked`: Boolean indicating if the video is bookmarked.
- `is_downloaded`: Boolean indicating if the video has been downloaded.
- `remove_from_list`: Boolean indicating if the video is marked for removal.

---

## Example Refactor Using a Base Model

```python
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
```

---

## Explanation of the Code

1. **Playlist Model**:
   - The `Playlist` model includes fields for metadata (`id`, `title`, `description`) and additional fields (`is_bookmarked`, `is_downloaded`, `remove_from_list`).
   - The `videos` relationship links the playlist to its videos.

2. **Video Model**:
   - The `Video` model includes fields for metadata (`id`, `title`, `description`) and additional fields (`is_bookmarked`, `is_downloaded`, `remove_from_list`).
   - The `playlist_id` field establishes a foreign key relationship with the `Playlist` model.
   - The `playlist` relationship links the video back to its playlist.

3. **Relationships**:
   - The `Playlist` model has a one-to-many relationship with the `Video` model.
   - The `Video` model has a many-to-one relationship with the `Playlist` model.

---

## Additional Features

You can extend the models with additional fields or methods as needed:
- **Timestamps**: Add `created_at` and `updated_at` fields for tracking changes.
- **Custom Methods**: Add methods to mark a playlist or video as downloaded, bookmarked, or removed.

---

## Example Usage

```python
# Example: Creating a playlist and adding videos
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database setup
engine = create_engine('sqlite:///youtube.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Create a playlist
playlist = Playlist(
    id='PL1234567890ABCDEFG',
    title='Python Programming Tutorials',
    description='Learn Python programming from scratch.',
    is_bookmarked=True
)

# Add videos to the playlist
video1 = Video(
    id='abc123xyz456',
    title='Introduction to Python',
    description='Learn the basics of Python programming.',
    playlist=playlist
)

video2 = Video(
    id='def789uvw123',
    title='Python Functions Explained',
    description='A deep dive into Python functions.',
    playlist=playlist
)

# Save to the database
session.add(playlist)
session.add(video1)
session.add(video2)
session.commit()

print("Playlist and videos added successfully!")
```

---

## Conclusion

This data model provides a flexible structure for managing playlists and their videos in an MVC-based application. The relationships between playlists and videos ensure data integrity and make it easy to extend the functionality with additional features.
