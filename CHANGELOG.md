# Changelog - YouTube Playlist Explorer (AntiGravity)

## [3.0.1.0] - 2025-12-29

### Added
- **Session Management System**: Implemented a `_search_session` ID to invalidate stale background tasks. If a new search starts, old rendering and mapping tasks are aborted immediately, preventing UI collisions.
- **Thread-Local YouTube API Services**: Refactored the `Playlist` handler to use `threading.local()`. Each background thread now has its own dedicated connection, resolving "Access Violation" crashes during concurrent API calls.
- **MediaIndex Persistence**: Added serialization and snapshotting for the `MediaIndex`, ensuring video-playlist mappings are preserved across mode switches and app restarts.

### Changed
- **Modular Architecture**: Monolithic `MainPage.py` refactored into specialized handlers:
  - `VideoUIHandler`: Manages video table rendering and status updates.
  - `PlaylistUIHandler`: Handles playlist tree logic and video-playlist mapping.
  - `ActionHandler`: Coordinates complex actions like searches and pagination.
  - `SearchPersistenceHandler`: Manages state restoration and search history.
- **Optimized UI Progress**: Renamed search labels for better clarity:
  - "Mapping playlists" → "Videos analyzed"
  - "Scanning playlists" → "Analyzing associations"
- **Improved Thread Safety**: Audit and implementation of `threading.Lock` across all shared data structures (caches, index maps, model dictionaries).

### Fixed
- **Persistent Search Crash**: Resolved low-level Segmentation Faults (`0xC0000005`) by removing thread-unsafe Tkinter calls (like `winfo_exists()`) from background threads.
- **Dictionary Mutation Errors**: Fixed `RuntimeError: dictionary changed size during iteration` during data serialization by wrapping access in locks.
- **"Back to Results" Logic**: Fixed state loss when returning from a specific playlist view to global search results.
- **Initial Search Stability**: Resolved crash occurring on application startup when last search was restored.

### Optimized
- **Bulk Linking**: Optimized `MediaIndex.bulk_link_playlist_videos` to acquire locks once per batch, reducing overhead.
- **Chunked Rendering**: Improved `render_videos` and `render_playlists` to handle large datasets without freezing the UI, now with session-aware cancellation.
