# YouTube Playlist Explorer — Basic Final

A desktop app for exploring YouTube videos and playlists, mapping videos to their playlists, and managing downloads. This “basic_final” documentation highlights features and their implementation locations to help you extend or maintain the app.

## Quick Start

- Windows run script: `v0_basic\run_app.bat` (activates venv and runs `python -m src.main`)
- Requirements: `python-vlc`, `isodate`, `google-api-python-client` and VLC installed on the machine
- First run: provide YouTube API key and default folder in the Setup page

## Core Features

- Search modes on one row with radio group
  - Select `Playlists` or `Videos`; enter keyword; click `Search`
  - Implementation: `src/pages/main/search_section.py:12-35`

- Videos mode: collect playlists per video, not per channel
  - For each searched video, fetch its channel’s playlists and check membership
  - Implementation: `src/pages/main/main_page.py:248-310` inside `_fetch_playlists`
  - Membership check: `src/playlist.py:156-170` (`playlist_contains_video`)

- Playlist pinning and bring-to-top
  - When a video’s playlist is identified, it is pinned and scrolled into view
  - Implementation: video selection flow `src/pages/main/main_page.py:371-392`

- Playlists panel numbering
  - First column `No` shows stable numbering per search
  - Implementation: numbering and updates in `src/pages/main/playlist_section.py:18-41, 120-176`

- Videos panel shows matched playlist No
  - Column `Playlist` displays the playlist number for each video when known
  - Implementation: `_video_row` and mapping in `src/pages/main/main_page.py:41-97, 512-538`

- Status bar feedback
  - Shows background progress like collecting playlists, mapping results, and refresh status
  - Implementation: updates across `src/pages/main/main_page.py:294-308, 581-602` and `src/pages/main/playlist_section.py:140-176`

- Pagination
  - Videos search pagination retains tokens and current page on “Back to Results”
  - Implementation: search paging `src/pages/main/main_page.py:297-306, 405-423`; back navigation `src/pages/main/main_page.py:331-369`
  - Playlist paging and back button: `src/pages/main/main_page.py:523-548` and `src/pages/main/video_section.py:102-121, 146-150`

- Highlight matches in playlist view
  - Highlights videos in a playlist that match the current search (by `videoId` or keyword)
  - Tag style: `src/pages/main/video_section.py:75`
  - Rendering with match detection and `★` marker: `src/pages/main/main_page.py:585-602`

## How It Works

- Background collection (Videos mode)
  - After performing a videos search, the app collects relevant playlists by checking each video against the playlists of its channel and confirming membership via the YouTube Data API (`playlistItems.list` with `playlistId` + `videoId`).
  - Collected playlists are numbered and displayed as they arrive; the mapping updates the `Playlist` column for videos when the relationship is found.

- Video→Playlist mapping
  - Best-effort mapping based on playlist first page and membership check; keeps UI responsive using background threads and `after()` callbacks.

- Back to Results
  - Saves the results, playlists, tokens, and search `videoId`s to enable restoring the exact list with pagination state and highlights.

## Running the App

- Use `v0_basic\run_app.bat` from the project root; it will:
  - Activate venv: `venv\Scripts\activate.bat`
  - Run: `python -m src.main`
  - Deactivate venv on exit

## Implementation Reference

- Search UI
  - Radio group and single-row layout: `src/pages/main/search_section.py:12-35`

- Main page logic
  - Building video rows and playlist index: `src/pages/main/main_page.py:1-40, 41-97`
  - Videos search and initial render: `src/pages/main/main_page.py:220-247`
  - Background playlist collection and mapping: `src/pages/main/main_page.py:248-310`
  - Persist results and tokens: `src/pages/main/main_page.py:315-323`
  - Back to Results: `src/pages/main/main_page.py:331-369`
  - Playlist videos view and back/pagination: `src/pages/main/main_page.py:514-606`
  - Video selection highlight/pin: `src/pages/main/main_page.py:371-392`

- Playlists panel
  - Setup and `No` column: `src/pages/main/playlist_section.py:18-41`
  - Update/preserve pin indicator: `src/pages/main/playlist_section.py:120-139`
  - Refresh statuses with progress: `src/pages/main/playlist_section.py:140-176`

- Video panel
  - Columns and handlers: `src/pages/main/video_section.py:20-69, 88-121`
  - Tag style for highlight: `src/pages/main/video_section.py:75`

- YouTube API
  - Playlist items and membership: `src/playlist.py:110-155, 156-170`

## Configuration

- Config file `config.json` stores API key and default folder:
```json
{
  "api_key": "your_youtube_api_key",
  "default_folder": "path/to/download/folder"
}
```

## Notes & Limits

- Mapping depth is limited for responsiveness; expanding beyond first page or across non-owner channels increases API calls.
- UI highlights may vary slightly by OS theme; the `★` prefix guarantees visibility.
- Export features (CSV/TXT) and the downloaded video player are available; advanced player controls can be added as needed.

## Extending

- Deeper playlist mapping: batch `playlistItems.list` pages with rate limiting; update mapping progressively.
- Status detail: show current mode context like “Results page N” vs “Playlist ‘X’ page Y/Z”.
- Additional columns: add fields (duration, view counts) consistently across both panels.

For testing procedures and known issues, see `docs/test.md`.