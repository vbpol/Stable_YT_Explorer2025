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
