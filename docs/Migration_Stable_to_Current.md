# Migration: Last Stable -> Current Codebase

## Goal
Restore last stable functionality as the runtime while preserving current code for incremental porting and fixes.

## Approach
- Entry launch proxy: `src/main.py` now delegates to `backups/basic_final_stable/src/main.py` using a subprocess with `cwd` set to the backup root. This prevents import recursion and ensures the full backup `src` tree is used at runtime.
- Preserve current entrypoint: prior `src/main.py` content is saved as `src/main.pre_recover.py` for reference.

## Functional Fixes Applied in Stable Runtime
- Last keyword persistence
  - Added `ConfigManager.save_last_query(query, mode)` and `load_last_query()` with storage in `data/last_query.json`.
  - Playlists/Videos saves now include `'query'` and write to `last_query.json`.
  - Startup/mode switch loaders populate the search box from saved `query` or fallback to `last_query.json`.
  - Files: `backups/basic_final_stable/src/config_manager.py`, `backups/basic_final_stable/src/pages/main/main_page.py`.
- Numbering reset
  - `clear_panels()` resets `playlist_index_map` and `pinned_playlist_id` to reinit numbering per view/search.
  - Indexing remains deterministic within a session via `assign_playlist_index`.
- Highlight protection
  - When selecting a video, highlight and pin playlists; when selecting a playlist, highlight matching videos.
  - Guards ensure tags, tokens, and IDs exist; fallbacks prevent errors if data is missing.

## Differences vs Current Code
- Current code may already implement additional UI polish or different highlight semantics.
- Stable runtime now includes query persistence and loader fallbacks; current code previously lacked them.
- Entry proxy ensures you can run with stable behavior without overwriting current work.

## Remaining Issues and How-To Fix
1) Refine playlist numbering correctness
- Ensure numbering reflects discovery order and remains consistent when pinning/moving items.
- Strategy: rebuild `playlist_index_map` deterministically from the playlists tree on each new search, assign indices by visible order, and update videos’ `playlistIndex` accordingly.
- Impact: consistent indices regardless of background collection timing.
2) Videos highlight when playlist selected
- Current version appears improved; stable now guards for both `videoIds` matches and fuzzy query match.
- Strategy: unify logic so highlight derives from selected playlist membership and last search query; ensure no exceptions when fields missing.
- Impact: reliable highlight with clear visual markers and status messages.

## Lesson Learned & Behavioral Alignment
- Mode-specific behavior for playlist selection:
  - In Playlists mode, selecting a playlist should navigate to its videos list (replace top panel).
  - In Videos mode, selecting a playlist should not replace the search results, but highlight videos among the current search results that belong to that playlist and annotate the Playlist column with the proper index.
  - Single-click on a playlist now highlights matches in Videos mode using a distinct tag/color (`playlist_hit`), while double-click continues to open and paginate the playlist videos (previous feature recovered).
  - Clicking a video sets a separate tag/color (`video_hit`) to distinguish direct-click marking from playlist-based highlighting.
- Double-click behavior is enforced at the source: single-click handler performs highlighting; double-click calls `show_playlist_videos` unconditionally, and `show_playlist_videos` no longer branches by mode so it always opens the playlist videos. Pinning is applied on open so star marks persist.
  - Added network-robust fetch for playlist videos: retry once with reduced `max_results` on SSL errors; if still failing, fall back to highlighting to keep UX responsive.

## Workflow & Validation
- Focus on one feature at a time, preserve validated paths.
- For each change:
  - Identify impacted files and UI bindings
  - Implement guarded logic with fallbacks
  - Verify via manual steps and automated checks
- Playlist open refactor:
  - Unified method `show_playlist_videos` for both modes
  - Background thread fetch + single retry on network error
  - Fallback to highlight if still failing
- Validation checklist:
  - Startup restores last mode and query
  - Single-click highlights in Videos mode
  - Double-click opens playlist videos in both modes
  - Progress bar updates during collection
  - Star persists across refresh/pagination
  - Terminal lists videos on playlist double-click (both modes)
  - No mode change on playlist double-click in Videos mode
  - Prefetch first pages during videos search and reuse cache on open
  - Watchdog highlights if videos fail to load within timeout
- Implementation:
  - Added `highlight_videos_for_playlist(playlist_id)` and branched `show_playlist_videos` when `search_mode == 'videos'` to call the highlighter instead of replacing the list.
  - The highlighter runs in a background thread, checks membership via `playlist_contains_video`, updates `video_playlist_cache`, sets `playlistIndex`, and re-tags rows with `search_hit`. Status messages communicate the outcome.
  - Restored star-mark on matched videos in Videos mode by prefixing the Title with `★` during in-place updates; avoids duplication and preserves existing styling.
  - Persisted star-mark reliably by making `_video_row` star the title when the video belongs to the currently pinned playlist (via `video_playlist_cache` or `playlistIndex`), so refreshes and pagination keep the visual cue.
  - Added Treeview tags: `playlist_hit` (light blue) and `video_hit` (pink) to provide visual differentiation of marks, configured in `VideoSection` and applied in the respective code paths.
- Impact:
  - Addresses cases where a numbered playlist (e.g., No. 5) appears without mapped videos by actively checking membership on selection. If no matches exist, a clear status indicates this is expected for that playlist.
  - Guarded the menu command for changing download folder to avoid startup crashes if `MainPage.change_download_folder` is not yet resolved; a safe fallback prompts for a folder and updates config directly.
  - Ensures consistent user cues: yellow `search_hit` highlight plus a leading `★` next to matched titles in Videos mode.
  - Differentiates user actions visually: playlist-click highlights vs video-click marks for clarity, improving UX without impacting performance.

## Logging & Recovery
- Added lightweight logger `MainPage._log` to print and mirror messages on `StatusBar`.
- Instrumented `show_playlist_videos` to log playlist open with page token and pin the playlist.
- Implemented background worker with single retry reducing `max_results` on fetch failure; if repeated failure, triggers `highlight_videos_for_playlist` as a responsive fallback.
- Added recovery path in `back_to_video_results`: if playlists are empty but videos exist, re-collect playlists in a background thread and persist the result.
- File references:
  - `src/pages/main/main_page.py:92` for `_log` attach
  - `src/pages/main/main_page.py:398` for back recovery and re-collection
  - `src/pages/main/main_page.py:658` for unified open with retry and async worker
  - `src/pages/main/main_page.py:695` for unified render and terminal listing
  - `src/pages/main/main_page.py:114` for playlist videos cache helpers
  - `backups/basic_final_stable/src/pages/main/main_page.py:80` for `_log` and helpers
  - `backups/basic_final_stable/src/pages/main/main_page.py:831` for open with cache, retry, and render printing
  - `backups/basic_final_stable/src/pages/main/main_page.py:400` for playlist collection with prefetch caching
  - `backups/basic_final_stable/src/pages/main/main_page.py:256` last search load restores cached pages

## Robustness: Prefetch & Caching
- Prefetch first-page videos for newly collected playlists in background during videos search with limited concurrency and short delays.
- Cache playlist pages per `playlist_id` and `page_token` to avoid redundant API calls and speed up UI.
- Serve cached pages immediately on double-click and still print formatted listing to terminal.
- Prefetch logs are informational; failures are harmless and do not affect opening playlists.

## Rollback/Porting Guidance
- To port stable fixes into current code:
  - Copy `save_last_query/load_last_query` helpers into current `src/config_manager.py`.
  - Mirror loader/save changes from stable `main_page.py` into current `src/pages/main/main_page.py`.
  - Verify `clear_panels()` performs numbering reset and guarded UI updates.
- To rollback proxy and run current code:
  - Restore `src/main.py` from `src/main.pre_recover.py`.

## Run Instructions
- Run `python -m src.main` from project root; the proxy launches the stable runtime.
- Last query and mode will restore after your first search with the new format.

## Commit
- Changes have been committed to local git with a message summarizing migration and fixes.
