# How to Retrieve Videos from a Playlist Using YouTube Data API

This tutorial explains how to use the YouTube Data API to retrieve videos from a specific playlist using an `api_key`.

---

## Prerequisites

1. **API Key**: Obtain an API key from the [Google Cloud Console](https://console.cloud.google.com/).
2. **Python Installed**: Ensure Python is installed on your system.
3. **Install `requests` Library**: Run `pip install requests` to install the required library.

---

## Scalability and DRY Principle

To ensure the code is scalable and adheres to the DRY principle:
1. **Encapsulate API Requests**:
   - Use a reusable class like `YouTubeAPI` to handle API requests and responses.
2. **Reusable Methods**:
   - Implement methods for fetching playlist videos and checking relationships to avoid duplicating logic.

---

## Example Refactor Using OOP

```python
# ...existing code...
class YouTubeAPI:
    # ...existing code...
    def get_playlist_videos(self, playlist_id, max_results=5):
        """Retrieve videos from a playlist."""
        params = {
            'part': 'snippet',
            'playlistId': playlist_id,
            'maxResults': max_results
        }
        return self.make_request('playlistItems', params)
# ...existing code...
```

---

### 3. Explanation of the Code

- **Retrieve Playlist Videos**:
  - The `get_playlist_videos` method fetches videos from a playlist using the `playlistItems` endpoint.

---

### 4. Run the Script

Save the script as `get_playlist_videos.py` and run it using:
```
python get_playlist_videos.py
```

---

### 5. Example Output

```
Video Title: Introduction to Python
Video ID: abc123xyz456
----------------------------------------
Video Title: Python Functions Explained
Video ID: def789uvw123
----------------------------------------
```

---

## Additional Resources

- [YouTube Data API Documentation](https://developers.google.com/youtube/v3/docs)
- [Google Cloud Console](https://console.cloud.google.com/)
