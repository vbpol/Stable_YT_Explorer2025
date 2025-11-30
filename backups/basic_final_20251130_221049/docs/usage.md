# Usage Guide

## Startup
- Configure API key and default folder via Setup.
- Window foreground lift is enabled (`src/youtube_app.py:22`).

## Modes
- Toggle Mode in the Search row (Playlists vs Videos).
- Enter a keyword and press Search.

## Videos Mode
- Columns: Title, Playlist No, Channel, Duration, Published, Views.
- Mapping collects related playlists; only matched playlists get numbers.
- A progress dialog appears while collecting related playlists with percentage and counts.
- Select a video to highlight its playlist and move it to top.
- Double-click a playlist to open its videos; Back to Results enables to restore search list.
- Back to Results reloads playlists first so the Playlist No is correctly shown (`src/pages/main/main_page.py:482-496`).
- Sort: click column headers (`src/pages/main/main_page.py:420`).
- Filter: double-click headers (`src/pages/main/main_page.py:440`).

## Playlists Mode
- Columns: No, Title, Channel, Videos, Status, Actions.
- Counts enriched via API when missing.
- Sort: click headers (`src/pages/main/main_page.py:475`).
- Filter: double-click headers (`src/pages/main/main_page.py:510`).
- Double-click a row to load videos; Actions column supports removal.

## Persistence
- Last-results saved and loaded on mode changes; includes `query`, tokens, `videos` and related `playlists`.
- Startup prioritizes last-mode (`Videos` or `Playlists`) based on `last_mode.json`.
- UI Playlist No is session-only and resets on each search (`src/pages/main/main_page.py:144-151`).

## Packaging
- Portable zip includes README and `.env.example`; extract and run `YouTubePlaylistExplorer.exe`.
- Lite zip is smaller; may re-fetch discovery caches on first use.
