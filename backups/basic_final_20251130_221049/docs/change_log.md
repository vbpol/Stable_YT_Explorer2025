# Change Log — Current Session

## Fixes
- Prioritize last used mode at startup via `last_mode.json`.
  - `src/main.py:65-77` reads last-mode and sets `MainPage` accordingly.
  - `src/pages/main/main_page.py:167-174` saves last-mode on search.
- Save related playlists found in Videos mode and restore them.
  - Saved to datastore and JSON after background collection `src/pages/main/main_page.py:341-353`.
  - Restored on mode set and startup `src/pages/main/main_page.py:83-107, 110-133`.
- Determinate progress popup for playlist collection with percentage and counts.
  - Created and updated in `src/pages/main/main_page.py:389-406` and `src/pages/main/main_page.py:346-364`.
  - Safe closure at 100% and on errors `src/pages/main/main_page.py:373-386`.
- Reset playlist numbering on every search (session-scoped).
  - `src/pages/main/main_page.py:144-151` resets maps and caches.
- Ensure Back to Results shows playlist No by loading playlists first.
  - `src/pages/main/main_page.py:482-496` loads playlists before rendering videos.
- Avoid NoneType destroy during popup close.
  - Guarded closures `src/pages/main/main_page.py:373-386`.

## Enhancements
- JSON persistence helpers restored (data dir, paths, save/load).
  - `src/config_manager.py:85-114` adds `get_data_dir`, `get_last_search_path`, `save_json`, `load_json`.
- Explicit last-mode persistence paths.
  - `src/config_manager.py:116-144` adds `get_last_mode_path`, `save_last_mode`, `load_last_mode`.
- Persistence mode detection for datastore factory.
  - `src/config_manager.py:147-154`, `src/data/factory.py:1-32`.
- Documentation expanded with a clear System Prompt and Developer Checklist (`docs/dev_workflow.md`).

## 2025-11-30 Additions
- Mode-aware double-click/single-click in Playlists table (no navigation in Videos mode)
- Right-click menu with Popup, Print, Populate (preview)
- Preview rendering in Videos table without changing mode; Back restores search results
- Intersection-only star marking in Videos, Popup, Terminal
- Cache-first mapping via playlist video ID sets and cached pages
- Persist `playlistPages` and `playlistIds` in last search JSON; restore on load
- Corrected Title/Channel/Videos column mapping for playlist opens
- Popup highlights only intersection; terminal lines show star on matches

## User-Facing Behavior
- Videos and Playlists modes restore last query and results on startup.
- Progress dialog shows detailed status and closes automatically at 100%.
- “No” column restarts from 1 for each search and appears correctly after Back to Results.

## Notes
- UI playlist numbering is session-only; do not persist globally.
- Related playlists from Videos searches are saved and restored for a seamless workflow.
