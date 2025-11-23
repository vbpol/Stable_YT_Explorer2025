# How to Handle Model Attributes in Python for YouTube Models

This tutorial explains how to manage and utilize model attributes in the context of a YouTube downloader application using SQLAlchemy. It covers the attributes of the `Playlist` and `Video` models, including how to implement methods for data retrieval and manipulation.

---

## Overview of Model Attributes

### 1. Playlist Model Attributes
The `Playlist` model includes the following attributes:
- **id**: Unique identifier for the playlist.
- **title**: Title of the playlist.
- **description**: Description of the playlist.
- **is_bookmarked**: Boolean indicating if the playlist is bookmarked.
- **is_downloaded**: Boolean indicating if the playlist has been downloaded.
- **remove_from_list**: Boolean indicating if the playlist is marked for removal.

### 2. Video Model Attributes
The `Video` model includes the following attributes:
- **id**: Unique identifier for the video.
- **title**: Title of the video.
- **description**: Description of the video.
- **playlist_id**: Foreign key linking the video to its playlist.
- **is_bookmarked**: Boolean indicating if the video is bookmarked.
- **is_downloaded**: Boolean indicating if the video has been downloaded.
- **remove_from_list**: Boolean indicating if the video is marked for removal.

---

## Implementing Methods for Model Attributes

### 1. Playlist Model Methods
- **Get Number of Videos**:
  ```python
  def get_number_of_videos(self, session):
      """Get the number of videos in the playlist."""
      return session.query(Video).filter(Video.playlist_id == self.id).count()
  ```

- **Get Videos**:
  ```python
  def get_videos(self, session):
      """Get a list of videos in the playlist."""
      return session.query(Video).filter(Video.playlist_id == self.id).all()
  ```

- **Get Videos DataFrame**:
  ```python
  def get_videos_df(self, session):
      """Get a Pandas DataFrame of videos for the playlist."""
      videos = self.get_videos(session)
      data = {
          'Title': [video.title for video in videos],
          'Channel': [video.get_channel_title() for video in videos],
          'is_bookmarked': [video.is_bookmarked for video in videos],
          'is_downloaded': [video.is_downloaded for video in videos],
          'remove_from_list': [video.remove_from_list for video in videos],
      }
      return pd.DataFrame(data)
  ```

### 2. Video Model Methods
- **Get Channel Title**:
  ```python
  def get_channel_title(self):
      """Get the channel title for the video."""
      # Implement logic to retrieve the channel title
      return "Channel Name"  # Placeholder
  ```

- **Get Duration**:
  ```python
  def get_duration(self):
      """Get the duration of the video."""
      # Implement logic to retrieve the video duration
      return "00:00:00"  # Placeholder
  ```

- **Check if Downloaded**:
  ```python
  def is_downloaded(self, downloads_folder):
      """Check if the video is downloaded."""
      video_file_path = os.path.join(downloads_folder, f"{self.title}.mp4")  # Assuming .mp4 format
      return os.path.exists(video_file_path)
  ```

- **Convert to DataFrame**:
  ```python
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
  ```

---

## Conclusion

By implementing these methods, you can effectively manage and utilize the attributes of the `Playlist` and `Video` models in your YouTube downloader application. This structure allows for easy data manipulation and ensures that your application adheres to best practices in software development.

For further details, refer to the individual tutorials linked in the previous sections. 