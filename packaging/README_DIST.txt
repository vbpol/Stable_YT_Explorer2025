YouTube Playlist Explorer — Windows Distribution

Usage
- Extract this zip anywhere (e.g., Desktop or Downloads).
- Open YouTubePlaylistExplorer.exe.
- On first run, use the Setup page to enter your YouTube API key and select a default download folder.

Requirements
- Windows 10/11
- VLC installed for video player features (optional for basic app usage)
 - ffmpeg on PATH to merge HD video+audio streams into MP4 (recommended)

Configuration
- Setup page saves your API key and folder to config.json next to the app.
- Alternatively, create a .env file with:
  YOUTUBE_API_KEY=your_key
  or
  YOUTUBE_API_KEYS=key1,key2

Persistence
- Use the Persistence menu to switch between JSON and SQLite. JSON is safest for first use.
- On network errors, the app shows last saved results.

Notes
- Logs are written to logs/app.log in the app folder.
- Do not edit files inside the _internal subfolders.
 - For HD with audio, choose "Best" or "720p" in Download Options; the app selects MP4+M4A streams and merges to MP4 when ffmpeg is available.

Troubleshooting
- If search fails, check internet and API quota.
- If video player features fail, verify VLC is installed.
