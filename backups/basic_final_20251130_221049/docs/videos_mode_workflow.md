# Videos Mode Workflow

## Goals
- Map each searched video to playlists and display only those playlists in Videos mode.
- Ensure contiguous numbering for playlists in Videos mode and consistent mapping in UI.
- Keep scans fast and robust with caching, minimal API calls, and deterministic updates.

## Data Flow
- video → playlist resolution: `_resolve_video_playlist`
- dataset build: `build_videos_mode_dataset`
- local indices: `recompute_video_local_indices`
- playlists normalization: `normalize_playlist_indices`

## Resolution Logic
- Check datastore reverse map and local `video_playlist_cache` first.
- Confirm membership for known playlists with `playlist_contains_video(playlistId, videoId)`.
- If no candidates exist, search by `channelTitle`/`title` (max 5) and confirm membership.
- Enrich playlist info with `get_playlist_info(playlistId)`.

## Dataset Build
1. Scan all current videos for playlist memberships.
2. Deduplicate playlists; sort by `title`.
3. Assign contiguous local numbers 1..N for these playlists.
4. Apply numbers to videos and playlists table.
5. Persist reverse cache for quick reentry.

## UI Updates
- Videos table `Playlist` column uses local numbers.
- Playlists table shows only playlists found for current videos.
- Tooltip on videos shows `playlistId` and playlist title.
- Selecting a video focuses its playlist and highlights related videos.

## Performance
- Membership results cached per `(playlistId, videoId)` to avoid repeated checks.
- Fallback search limited to 5 candidates per video.
- Playlist info fetched by ID only when needed.

## Logging & Validation
- Resolver start, candidates, hits, and final mapping logged.
- Validation reports totals, cache/index-mapped counts, and mismatches.

## Debugging Scripts
- `python -m scripts.validate_app_ui_flow` → contiguous indices and mode shift check.
- `python -m scripts.print_videos_table_test_preview` → rows preview from test scenario.

## Tests
- `tests/test_videos_mode_mapping.py` → ensures no gaps and consistent No column.
- `tests/test_back_to_video_results.py` → restores indices and cache correctly.

## Known Limits
- API rate limits can impact membership checks; caching mitigates cost.
- Fallback search works best when `channelTitle`/`title` is descriptive; otherwise fewer matches.

## Graceful Exit
- KeyboardInterrupt during UI now closes the window without a stack trace.

## Open Issues & TODOs
- Restore last videos search keyword reliably on app start and on mode switch (Videos).
- Ensure playlists table seeds from last videos result even when background mapping has not run yet.
- Guarantee playlist title/channel always present in playlists table (use `get_playlist_info` when needed).
- Speed up initial mapping via small parallel membership checks; keep UI responsive.
- Persist membership cache with TTL in datastore to reuse across sessions.
- Verify playlist highlight consistently tags videos in large result sets.
- Add status bar summary for mapping results (mapped count, unmapped count).
