# AntiGravity Review and Recommendations

## Overview
- Scope: UI flows for Playlists/Videos modes, intersection highlighting, Back to Results restoration, persistence strategy, and refactor plan.
- Status: Nearly stable; tests pass for highlight, back-restore, pagination, and mapping.
- Version: v1.1.0. Title updated to include `[TRAE]`.

## Current Architecture
- Layers
  - UI: Tkinter pages under `src/pages/` orchestrated by `src/youtube_app.py`.
  - Services: YouTube API wrapper in `src/playlist.py`; playlist-video mapping via `src/services/media_index.py` and `src/services/video_playlist_scanner.py`.
  - Persistence: JSON/SQLite/Django via `src/data/`; last results using `ConfigManager`.
  - UI Components: `TablePanel` uses `PaginationBar` for controls.
- Single Source of Truth
  - `MediaIndex` maintains canonical mapping: video→playlist and per‑playlist video IDs.
  - UI reads from index and cached pages; no duplicate state beyond transient caches.

## Key Behaviors Verified
- Playlists Mode
  - Playlist open: cache-first loading; background threads; non-blocking rendering.
  - Pagination: consistent indicators via `PaginationBar`; Next/Prev state sync.
- Videos Mode
  - Intersection highlights: stars + `playlistIndex` update, cached map preserved.
  - Back to Results: restores videos, playlists, tags, numbering; rebuilds index and caches.
- Persistence
  - `last_videos_search.json` stores `query`, `videos`, `playlists`, `videoIds`, `playlistPages`, `playlistIds`.
  - Cache-only save path avoids overwriting restored result sets.

## Findings
- UI Responsibility: Rendering and events are clean; orchestration stays in services.
- Error Resilience: Widespread guarded try/except; chunked inserts prevent UI stalls.
- Mapping Consistency: Restored mapping aligns with prior search; tests verify playlist numbering preserved.
- Title/Version: Updated to `YouTube Playlist Explorer - [TRAE] - v1.1.0 [DEV/PROD]` from env.

## Recommendations
- Strengthen Data Shapes
  - Define typed dataclasses for UI rows to reduce defensive code.
  - Normalize `playlistIndex` handling with a dedicated mapper.
- Consolidate Persistence
  - Unify save/load helpers for cache vs. full-result updates.
  - Add integrity checks for `playlistIds` and `playlistPages` on load.
- Performance
  - Cap chunk size adaptively based on tree size; measure insert latency.
  - Defer heavy `get_details` calls and memoize with TTLs.
- UX
  - Inline indicators for pinned playlist and intersect count.
  - Quick filter chips for video and playlist tables.

## Refactor Plan (Branches)
- Branch: `feature/refactor-pagination-videosmapping`
  - PaginationBar: already modular; add callbacks contract and unit tests for visibility thresholds.
  - Video Results Mapping: extract a `ResultsMapper` in `src/services/results_mapper.py` to own:
    - Build `playlist_index_map` and `video_playlist_cache`
    - Persist `playlistPages`/`playlistIds`
    - Restore mapping on back-to-results
  - Wiring: `MainPage` delegates to `ResultsMapper` for map ops; UI keeps rendering responsibilities.

## Validation Checklist
- Uses centralized index (`MediaIndex`) for membership checks
- No duplicated state across layers
- Clean separation: UI vs. services vs. index
- Error‑resistant updates; no partial writes of result sets
- Unit tests pass for highlight, back-restore, pagination, mapping
- Title and version show `[TRAE]` and `v1.1.0`

## Rollback Strategy
- Backup copies retained for changed files when performing deeper refactors.
- Branch isolation ensures quick revert; main tagged at v1.1.0 before feature work.

## Next Steps
- Implement `ResultsMapper` with tests; integrate gradually.
- Add a diagnostics panel to inspect current `playlistIndex` and hit counts.
- Measure UI insert throughput; tune chunk sizes.

