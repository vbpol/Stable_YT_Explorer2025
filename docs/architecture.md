# Architecture Overview

## App Structure
- Entry: `src/main.py` launches `YouTubeApp` and wires a datastore.
- Core: `src/youtube_app.py:8` constructs frames and shows `SetupPage` or `MainPage`.
- Pages:
  - Main: `src/pages/main/main_page.py:19`
  - Sections: `playlist_section.py:6`, `video_section.py:5`, `search_section.py`
- Data access: `src/playlist.py` for YouTube API, `src/data/*` for last-results and durable storage.

## UI Flow
- Mode switch: `set_search_mode` in `src/pages/main/main_page.py:59`
- Search:
  - Playlists: `execute_search` in `src/pages/main/main_page.py:114`
  - Videos: same function; adds highlights and background mapping
- Playlist view: `show_playlist_videos` in `src/pages/main/main_page.py:558`
- Preview into Videos: `populate_videos_table_preview` shows playlist videos without mode switch
- Back to Results: `back_to_video_results` in `src/pages/main/main_page.py:309`
- Progress dialog: created and updated in `src/pages/main/main_page.py:389-406` and `src/pages/main/main_page.py:346-364`; closes safely `src/pages/main/main_page.py:373-386`
- Startup performance: `_load_last_search` restores cached results with no network calls (`src/pages/main/main_page.py:619-694`).

## Videos Mapping
- Search videos: `search_videos` in `src/playlist.py:40`
- Get channel playlists: `get_channel_playlists` in `src/playlist.py:148`
- Check membership: `playlist_contains_video` in `src/playlist.py:164`
- Cache-first mapping via:
  - `playlist_videos_cache` (first pages + tokens)
  - `playlist_video_ids` (id sets for fast membership checks)
- Persisted in last videos search JSON as `playlistPages` and `playlistIds`.
- Enrich playlist rows with counts: `get_details` call inside mapping `src/pages/main/main_page.py:224`

## Tables & Interactions
- Videos table: created at `src/pages/main/video_section.py:20`
  - Sort: `sort_videos_by` in `src/pages/main/main_page.py:420`
  - Filter: `on_video_header_double_click` in `src/pages/main/main_page.py:440`
- Playlists table: created at `src/pages/main/playlist_section.py:18`
  - Sort: `sort_playlists_by` in `src/pages/main/main_page.py:475`
  - Filter: `on_playlist_header_double_click` in `src/pages/main/main_page.py:510`
  - Right-click context menu: Popup, Print dataset, Populate Videos table
  - Double-click in Videos mode is consumed; pin/print/highlight only (no navigation)

## Persistence
- Last-results snapshots via datastore
  - Save Videos (including related playlists): `src/pages/main/main_page.py:341-353`
  - Load Videos last-results: `src/pages/main/main_page.py:78-107`
  - Save Playlists: `src/pages/main/main_page.py:167-174`
  - Load Playlists last-results and fallback: `src/pages/main/main_page.py:110-133`
- Durable relations (future parity): `playlist_videos` in SQLite/Django
- Intersection-only marking logic enforced by `_preview_only_hits` and `video_search_ids`.

## Config & Paths
- JSON helpers: `src/config_manager.py:85-114` provide `get_data_dir`, `get_last_search_path`, `save_json`, `load_json`.
- Last-mode persistence: `src/config_manager.py:116-144` (`get_last_mode_path`, `save_last_mode`, `load_last_mode`).
- Datastore selection: `src/config_manager.py:147-154` and factory `src/data/factory.py:1-32`.

## Window Management
- Foreground lift: `src/youtube_app.py:22` deiconify, lift, topmost toggle
