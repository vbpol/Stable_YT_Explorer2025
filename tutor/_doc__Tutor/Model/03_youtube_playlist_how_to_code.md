# How to Search for Playlists Using YouTube Data API

This tutorial explains how to use the YouTube Data API to search for playlists using an `api_key`.

---

## Prerequisites

1. **API Key**: Obtain an API key from the [Google Cloud Console](https://console.cloud.google.com/).
2. **Python Installed**: Ensure Python is installed on your system.
3. **Install `requests` Library**: Run `pip install requests` to install the required library.

---

## Scalability and DRY Principle

To ensure the code is scalable and adheres to the DRY (Don't Repeat Yourself) principle:
1. **Encapsulate API Requests**:
   - Create a reusable class or function for making API requests to avoid duplicating request logic.
2. **Use Object-Oriented Programming (OOP)**:
   - Define a `YouTubeAPI` class to encapsulate API-related logic, such as constructing URLs, handling responses, and managing errors.
3. **Reusable Methods**:
   - Implement reusable methods for common tasks like fetching playlists, videos, or checking relationships.

---

## Step-by-Step Guide

### 1. Set Up Your API Key and Base URL

The YouTube Data API provides a base URL for search operations. Use the following base URL:
```
https://www.googleapis.com/youtube/v3/search
```

### 2. Write the Python Code

Below is an example Python script to search for playlists and videos by keywords in the title, and retrieve the playlist title if a video belongs to a playlist:

```python
# ...existing code...
class YouTubeAPI:
    # ...existing code...
    def search(self, query, search_type, max_results=5):
        """Search for playlists or videos."""
        params = {
            'part': 'snippet',
            'q': query,
            'type': search_type,
            'maxResults': max_results
        }
        return self.make_request('search', params)

    def get_playlist_title_from_video(self, video_id):
        """Retrieve the playlist title if the video belongs to a playlist."""
        params = {'part': 'snippet', 'videoId': video_id}
        data = self.make_request('playlistItems', params)
        if data and 'items' in data and len(data['items']) > 0:
            return data['items'][0]['snippet'].get('playlistTitle')
        return None

# ...existing code...
```

---

### 3. Explanation of the Code

- **Search for Both Playlists and Videos**:
  - The `type` parameter is set to `video,playlist` to include both playlists and videos in the search results.
- **Retrieve Playlist Title for a Video**:
  - The `get_playlist_title_from_video` function uses the `playlistItems` endpoint to check if a video belongs to a playlist and retrieves the playlist title if available.

---

### 4. Run the Script

Save the script as `search_playlists_and_videos.py` and run it using:
```
python search_playlists_and_videos.py
```

---

### 5. Example Output

```
Playlist Title: Python Programming Tutorials
Playlist ID: PL1234567890ABCDEFG
----------------------------------------
Video Title: Introduction to Python
Video ID: abc123xyz456
Part of Playlist: Python Programming Tutorials
----------------------------------------
Video Title: Python Functions Explained
Video ID: def789uvw123
Part of Playlist: Python Programming Tutorials
----------------------------------------
```

---

## Additional Resources

- [YouTube Data API Documentation](https://developers.google.com/youtube/v3/docs)
- [Google Cloud Console](https://console.cloud.google.com/)
