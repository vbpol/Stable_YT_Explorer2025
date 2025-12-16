# Media–Videos–Playlists Consistency Resolution

## Overview
- Introduce centralized `MediaIndex` holding `VideoModel`, `PlaylistModel`, and relationships.
- Drive UI highlights and panel population from `MediaIndex` to avoid divergence.
- Persist known membership from cache/prefetch; enrich progressively via scanning.

## Impact Analysis
- UI: `MainPage.highlight_videos_for_playlist` prefers `MediaIndex` membership when available.
- UI Safety: Debounced playlist clicks in Videos mode via `_videos_mode_click_busy` to prevent overlapping work and crashes.
- UI Feedback: Status bar messages on mode changes, search start, and playlist click processing.
- Pagination: `PaginationBar` hidden by default on entering Videos mode and during new video searches; becomes visible only when item count exceeds page size; page indicator updates dynamically on Next/Previous.
- Data flow: scanning callbacks update both UI and `MediaIndex` with playlist discovery and video links.
- Persistence: last results restore hydrates `MediaIndex` alongside legacy caches for backward compatibility.
- Risk: minimal; index is additive and does not remove existing paths. If unavailable, legacy sets are still used.

## Architecture Changes
- New module `src/services/media_index.py`:
  - `VideoModel(videoId, title, channelTitle, channelId, duration, published, views, playlistId?, playlistIndex?)`
  - `PlaylistModel(playlistId, title, channelTitle, video_count, video_ids set)`
  - `MediaIndex`: `add_videos`, `add_playlists`, `link_video_to_playlist`, `bulk_link_playlist_videos`, getters.
- `MainPage` integration:
  - Initialize/reset `media_index`.
  - Hydrate index on video search and on restore of last results.
  - Update index during scanning and when caching playlist pages.
  - Guarded handler `on_videos_mode_playlist_click(playlist_id)` serializes pin → print → highlight with a busy flag.
  - Pagination updates routed through `TablePanel.pagination.set_page_info` for consistent visibility and indicators.

## Migration / Rollback
- Rollback plan: remove `media_index` usage and module; UI falls back to existing `playlist_video_ids`/`video_playlist_cache` paths.
- UI safety can be retained independently; if removed, reintroduce click debouncing to avoid overlap.
- No schema migration; purely in-memory.

## TODO List
- Replace remaining direct uses of `playlist_video_ids`/`video_playlist_cache` with `MediaIndex`.
- Persist `MediaIndex` to JSON alongside last results for offline continuity.
- Add unit tests for `MediaIndex` linking and retrieval.
- Maintain dev tooling commands for lint (`ruff`) and typecheck (`mypy`).
- Add stress test for rapid playlist clicks in Videos mode (busy flag correctness).

## Validation Checklist
- Videos mode search:
  - Page indicator and visibility correct based on dataset size.
  - `MediaIndex` contains all `videoId` items with fields populated.
- Playlist discovery via scanner:
  - Discovered playlists added to `MediaIndex`.
  - Prefetched playlist page links `video_ids` into `MediaIndex`.
  - `_index(vid, pid, idx)` sets `playlistId` and `playlistIndex` in `MediaIndex`.
- Click playlist in Videos mode:
  - Intersection highlights only rows that belong to the playlist and exist in current results.
  - No API round-trip required for highlight when index has membership.
  - Busy flag prevents overlapping clicks; no freeze/crash under repeated clicks.
- Restore last results:
  - `MediaIndex` hydrated from saved `playlistIds` and videos/playlists arrays.
 - Pagination:
   - Hidden on Videos mode entry and new search until counts are known.
   - Next/Previous updates page index and button states correctly.

## Notes
- Index is authoritative; UI should prefer it when available.
- Cached pages push membership into index to keep behavior consistent.
