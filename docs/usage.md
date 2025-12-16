# Usage Guide

## Startup
- Configure API key and default folder via Setup.
- Window foreground lift is enabled (`src/youtube_app.py:22`).
- No network calls at startup; the app restores last saved results instantly.
- Background mapping and API queries occur only after a user-initiated search.

## Modes
- Toggle Mode in the Search row (Playlists vs Videos).
- Enter a keyword and press Search.

-## Videos Mode
- Columns: Title, Playlist No, Channel, Duration, Published, Views.
- Mapping uses targeted search with membership confirmation; only intersecting playlists are shown and numbered.
- Single-click a playlist: pins and highlights intersection videos only (no table clear).
- Double-click a playlist: populates the Videos table with that playlist's videos; Back to Results becomes active.
- Right-click a playlist: popup menu includes Highlight, Show Videos (Popup), Print Dataset, Populate Videos Table.
- A progress dialog appears while collecting related playlists with percentage and counts.
- Select a video to highlight its playlist and move it to top.
- Back to Results reloads playlists first so the Playlist No is correctly shown (`src/pages/main/main_page.py:482-496`).
 - Mapping is persisted during highlight/preview and restored automatically when you click Back to Results.
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
- On API errors or quota limits, the UI loads last saved Videos results automatically.
- Startup prioritizes last-mode (`Videos` or `Playlists`) based on `last_mode.json`.
- UI Playlist No is session-only and resets on each search (`src/pages/main/main_page.py:144-151`).

## Packaging
- Portable zip includes README and `.env.example`; extract and run `YouTubePlaylistExplorer.exe`.
- Lite zip is smaller; may re-fetch discovery caches on first use.
