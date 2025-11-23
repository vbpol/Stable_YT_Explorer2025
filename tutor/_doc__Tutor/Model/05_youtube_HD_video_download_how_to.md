# How to Download HD Videos from YouTube Using Python

This tutorial explains how to download HD videos from YouTube using Python. The implementation uses the `pytube` library for video downloading. It also includes downloading all videos from a playlist and updating the `is_downloaded` field in the data model.

---

## Prerequisites

1. **Python Installed**: Ensure Python is installed on your system.
2. **Install `pytube` Library**: Run the following command to install the `pytube` library:
   ```
   pip install pytube
   ```
3. **Install `config.json`**: Ensure your `config.json` file is set up to store any required configurations.

---

## Scalability and DRY Principle

To ensure the code is scalable and adheres to the DRY principle:
1. **Encapsulate Download Logic**:
   - Use a reusable class like `YouTubeDownloader` to handle video and playlist downloads.
2. **Centralized Configuration**:
   - Manage configurations like the download directory in a single place.

---

## Example Refactor Using OOP

```python
# ...existing code...
class YouTubeDownloader:
    # ...existing code...
    def download_playlist(self, playlist_url):
        """Download all videos from a playlist."""
        try:
            playlist = Playlist(playlist_url)
            print(f"Downloading playlist: {playlist.title}")
            for video_url in playlist.video_urls:
                self.download_video(video_url)
            print(f"All videos from playlist '{playlist.title}' have been processed.")
        except Exception as e:
            print(f"An error occurred while processing the playlist: {e}")
# ...existing code...
```

---

### 4. Update `is_downloaded` Field in Data Model

Below is an example method to update the `is_downloaded` field in the playlist or video data model:

```python
# ...existing code...
def update_is_downloaded(entity, session, is_downloaded=True):
    """Update the is_downloaded field for a playlist or video in the database."""
    # ...existing code...
# ...existing code...
```

---

### 5. Example Usage

```python
# ...existing code...
downloader = YouTubeDownloader(DOWNLOAD_DIR)
downloader.download_playlist(playlist_url)
# ...existing code...
```

---

### 6. Explanation of the Code

1. **Download Playlist Videos**:
   - The `download_playlist` method in the `YouTubeDownloader` class iterates through all video URLs in a playlist and downloads each video using the `download_video` method.
2. **Update `is_downloaded` Field**:
   - The `update_is_downloaded` method updates the `is_downloaded` field for a playlist or video in the database using SQLAlchemy.

---

## Additional Resources

- [pytube Documentation](https://pytube.io/en/latest/)
- [YouTube Data API Documentation](https://developers.google.com/youtube/v3/docs)
