# How to Implement CRUD Operations for YouTube Models

This tutorial explains how to implement Create, Read, Update, and Delete (CRUD) operations for the Playlist and Video models in a YouTube downloader application using SQLAlchemy.

---

## Prerequisites

1. **SQLAlchemy Installed**: Ensure you have SQLAlchemy installed in your environment.
   ```bash
   pip install sqlalchemy
   ```
2. **Database Setup**: Ensure your database is set up and accessible.

---

## Overview of CRUD Operations

### 1. Create Operations

- **Creating a Playlist**:
  Use the `create_playlist` function to add a new playlist to the database.

  ```python
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
  ```

- **Creating a Video**:
  Use the `create_video` function to add a new video to a specific playlist.

  ```python
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
  ```

### 2. Read Operations

- **Reading All Playlists**:
  Use the `read_playlists` function to retrieve all playlists from the database.

  ```python
  def read_playlists(session):
      """Retrieve all playlists."""
      try:
          playlists = session.query(Playlist).all()
          logging.info("Retrieved all playlists.")
          return playlists
      except Exception as e:
          logging.error(f"Failed to retrieve playlists: {e}")
          return []
  ```

- **Reading Videos from a Playlist**:
  Use the `read_videos` function to retrieve all videos associated with a specific playlist.

  ```python
  def read_videos(session, playlist_id):
      """Retrieve all videos from a specific playlist."""
      try:
          videos = session.query(Video).filter(Video.playlist_id == playlist_id).all()
          logging.info(f"Retrieved videos for playlist ID {playlist_id}.")
          return videos
      except Exception as e:
          logging.error(f"Failed to retrieve videos for playlist ID {playlist_id}: {e}")
          return []
  ```

### 3. Update Operations

- **Updating a Playlist**:
  Use the `update_playlist` function to modify an existing playlist's title or description.

  ```python
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
  ```

- **Updating a Video**:
  Use the `update_video` function to modify an existing video's title or description.

  ```python
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
  ```

### 4. Delete Operations

- **Deleting a Playlist**:
  Use the `delete_playlist` function to remove a playlist from the database.

  ```python
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
  ```

- **Deleting a Video**:
  Use the `delete_video` function to remove a video from the database.

  ```python
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
  ```

---

## Conclusion

By implementing these CRUD operations, you can effectively manage playlists and videos in your YouTube downloader application. This structure allows for easy data manipulation and ensures that your application adheres to best practices in software development.

For further details, refer to the individual tutorials linked in the previous sections.