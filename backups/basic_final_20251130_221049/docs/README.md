# YouTube Playlist Explorer

A desktop application for exploring, downloading, and managing YouTube playlists with a built-in video player.

## Current Features

- Search YouTube playlists
- View playlist videos with pagination (5, 10, 20, 50 videos per page)
- Export playlists to different formats (CSV, TXT)
- Built-in video player for downloaded videos
- Video playback features:
  - Basic controls (Play/Pause, Stop)
  - Speed control (0.5x - 2.0x)
  - Time seeking
  - Volume control
  - Playlist panel toggle

## Installation

1. Requirements:
   ```bash
   # Install Python dependencies
   pip install python-vlc isodate google-api-python-client
   
   # Install VLC media player
   # Windows: Download from videolan.org
   # Linux: sudo apt install vlc
   # macOS: brew install vlc
   ```

2. YouTube API Key:
   - Go to Google Cloud Console
   - Create a new project
   - Enable YouTube Data API v3
   - Create API credentials
   - Copy the API key

3. First Run:
   - Launch the application
   - Enter your YouTube API key
   - Select default download folder
   - Click Save to continue

## Usage

### Searching Playlists
1. Enter keywords in the search box
2. Click "Search" or press Enter
3. Results show:
   - Playlist name
   - Channel name
   - Number of videos

### Managing Videos
1. Select a playlist to view its videos
2. Use page size selector (5, 10, 20, 50 videos per page)
3. Navigate using Previous/Next buttons
4. Double-click video to open in browser

### Exporting Playlists
- CSV Export: File > Export Playlist (CSV)
- Text Export: File > Export Playlist (TXT)
- Quick Save: "Save Playlist" button

### Video Player
1. Click "View Downloaded" to open player
2. Available controls:
   - Play/Pause button
   - Time slider
   - Speed controls (0.5x, 1.0x, 1.5x, 2.0x)
   - Volume slider
   - Playlist panel toggle

## Project Structure

```
youtube-playlist-explorer/
├── main.py                 # Application entry point
├── src/
│   ├── youtube_app.py      # Main application class
│   ├── config_manager.py   # Configuration handling
│   ├── pages/
│   │   ├── main/          # Main page components
│   │   │   ├── main_page.py
│   │   │   ├── video_player.py
│   │   │   ├── menu_section.py
│   │   │   ├── search_section.py
│   │   │   ├── playlist_section.py
│   │   │   ├── video_section.py
│   │   │   └── status_bar.py
│   │   └── setup_page.py  # Initial setup page
├── playlist.py            # YouTube API handling
└── config.json           # User configuration
```

## Developer Resources

- Dev Workflow and Regression Guards: see `docs/dev_workflow.md` (System Prompt and Developer Checklist).

## Configuration

The application uses a JSON configuration file (`config.json`):
```json
{
    "api_key": "your_youtube_api_key",
    "default_folder": "path/to/download/folder"
}
```

## Current Limitations

1. Video Player:
   - Basic playback controls only
   - No keyboard shortcuts yet
   - Fullscreen mode needs improvement

2. Pagination:
   - Page size changes reset current page
   - No direct page number input

3. File Operations:
   - Basic export formats only (CSV, TXT)
   - No import functionality

See `test.md` for detailed testing procedures and known issues. 
