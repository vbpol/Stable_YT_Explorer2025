# No-Regressions Dev Workflow

## Principles

- Preserve existing behavior unless the change explicitly requires it.
- Maintain a single interface contract for data access (`DataStore`) with identical shapes across implementations.
- Stage changes behind a switch (config or menu). Keep the legacy path available until full parity is verified.
- Reuse existing restore functions (do not duplicate UI logic). Videos radio toggle must call the same function as Back to Results.
- Handle errors gracefully: if external calls fail, load last saved results from the datastore instead of showing empty tables.
- Preserve legacy paths while validating new behavior; remove only after parity is verified and documented.
- Required manual checks: startup restore, radio toggles, Back to Results, playlist No column, search input, progress popup open/close.
- Document changes with code references.
- Maintain a rollback plan (e.g., persistence mode toggle to JSON).

## System Prompt (for contributors)

- Preserve all declared features; do not remove working code paths without a documented replacement.
- Default to legacy behavior; stage changes behind controlled toggles and keep parity with the last stable version.
- Optimize performance without changing return shapes, UI flows, or persistence formats.
- When adding async/background work, show clear user feedback (e.g., determinate progress with percentage) and ensure safe closure.
- On any external failure, load last saved results; never leave views empty.
- Before merging, verify: startup restore, mode toggles, Back to Results ordering, playlist numbering reset, progress popup lifecycle.
- Document implementation locations with `file_path:line_number` references.

## Dev Workflow

- Baseline & Branching
  - Tag the current stable state (e.g., `vX.Y.Z-stable`) and create a feature branch.
  - Snapshot last-results files if applicable.

- Design & Contracts
  - Define exact data shapes to return from the datastore.
  - List integration points that consume the datastore (restore functions, searches, pagination).

- Implementation
  - Add a new store behind `DataStore` without changing UI logic.
  - Introduce a config/menu toggle to switch stores.
  - Implement graceful fallback to last results on external errors.

- Verification
- Manual checklist: startup restore, radio toggles, Back to Results (playlists load first), playlist No numbering per search, pagination, highlights, search input content, progress popup closure at 100%.

- Documentation
  - Update README and phase reports to include logging, store selection, and restore behavior.
  - Add change log entries with file paths and line references.

- Rollback
  - Flip the toggle back to legacy store or remove new store selection.
  - Confirm logs show the reverted store and restore functions behave identically.

## Templates

- PR Checklist
  - Interface shapes unchanged and documented
  - Toggle wired and default behavior preserved
  - Restore functions reused (no duplicates)
- Manual verification steps completed
- Docs updated with code references

## Developer Checklist

- Baseline parity
  - Compare against last stable: features present, UI flows identical.
  - Startup restores last-mode and results (`src/main.py:65-77`).
- Persistence
  - Videos saves include related playlists (`src/pages/main/main_page.py:341-353`).
  - Playlists saves include query, counts (`src/pages/main/main_page.py:167-174`).
  - Back to Results loads playlists before videos (`src/pages/main/main_page.py:482-496`).
- Numbering
  - Reset `playlist_index_map` each search (`src/pages/main/main_page.py:144-151`).
- Progress UX
  - Determinate progress shows percentage and counts; closes at 100% (`src/pages/main/main_page.py:346-364`, `373-386`).
- Data shapes
  - `load_last_videos_result` returns `{videos, playlists, nextPageToken, prevPageToken, videoIds, query}`.
  - JSON paths via `ConfigManager.get_last_search_path(kind)` (`src/config_manager.py:95-98`).
- Performance
  - Background threads do not block UI; use `after()` for UI updates.
  - Avoid unnecessary recomputation; reuse caches and maps safely per session.
  - Zero-lag startup: do not perform network calls on launch; restore last results instantly from `ConfigManager`. Defer mapping/searches until user presses Search (`src/pages/main/main_page.py:619-694`).
- Documentation
  - Update change log and architecture with references.
- Commit Message
  - Scope: feature/migration
  - Summary: what changed and why
  - Behavior: how legacy behavior is preserved
  - Verification: logs/tests run and outcomes

- Test Checklist
  - Startup restore (Playlists)
  - Videos restore via Back to Results
  - Radio toggle restore (Videos)
  - Pagination tokens states correct
  - Highlights remain
  - Search box query restored

- Migration Plan
  - New store adapter ready and returns identical shapes
  - Toggle added and defaults to legacy behavior
  - Fallback shows last results on errors
  - Documentation and change log updated

## Django Backend Exploration Checklist

- Environment
  - Django installed and importable; confirm active store via logs (`datastore=DjangoStore`).
  - SQLite file path consistent (`src/data/app.sqlite3`).
- Schema parity
  - Models map 1:1 to tables with `managed=False`; check field names and types.
  - Ensure identical return shapes: `{videos, playlists, nextPageToken, prevPageToken, query, videoIds}`.
- Restore parity
  - Startup Playlists restore with query.
  - Videos radio toggle and Back to Results restore via the same function.
  - Pagination tokens enable/disable correctly; page indicator updates.
  - Highlights present; search input restored.
- Performance
  - Measure load times for `load_last_videos_result` and playlist paging; add indices if needed.
  - Use `select_related` to avoid N+1 queries where applicable.
- Reliability
  - Network/TLS errors trigger datastore fallback (last saved results).
  - Logs capture selection, saves, loads, counts, tokens, queries.
  - Playlists mode also falls back to last saved playlists on errors.
- Toggle behavior
  - Switch between `JSON`, `SQLite`, `Django` without restart; views reload on change.
- Migration plan
  - Keep JSON default until Django passes all parity checks.
  - Rollback path documented; toggle to JSON if issues arise.

## Regression Guards

- Last-mode persistence: save on search and load at startup (`src/main.py:65-77`, `src/pages/main/main_page.py:167-174`).
- Snapshot completeness: Videos saves must include related playlists (`src/pages/main/main_page.py:341-353`).
- Restore ordering: Back to Results must load playlists before videos (`src/pages/main/main_page.py:482-496`).
- Numbering policy: reset `playlist_index_map` each search (`src/pages/main/main_page.py:144-151`).
- Progress UX: determinate progress updates and closure at 100% (`src/pages/main/main_page.py:346-364`, `src/pages/main/main_page.py:373-386`).
- DataStore shapes: `load_last_videos_result` returns `{videos, playlists, nextPageToken, prevPageToken, videoIds, query}` consistently.

## Store Toggle UI

- Menu entries
  - Persistence radio group in `src/pages/main/menu_section.py:50-52`.
- Handler
  - `set_persistence_mode` applies selection and reloads views `src/pages/main/main_page.py:874-848`.
- Behavior
  - Toggle between `JSON`, `SQLite`, `Django` without restart. Views reload to reflect the selected store.

## UI Behaviors

- Videos mode
  - Search shows 6 columns: Title, Playlist No, Channel, Duration, Published, Views.
  - Playlist mapping runs in background; only matched playlists get a No.
  - Selecting a video highlights and moves its playlist to the top.
  - Back to Results stays disabled until a playlist view is opened; then restores last-results.
- Playlists mode
  - Shows No, Title, Channel, Videos, Status, Actions.
  - Video counts enriched via API when missing.

## Sorting & Filtering

- Videos
  - Sort on header click → `src/pages/main/main_page.py:420`.
  - Filter on header double-click → `src/pages/main/main_page.py:440`.
- Playlists
  - Sort on header click → `src/pages/main/main_page.py:475`.
  - Filter on header double-click → `src/pages/main/main_page.py:510`.

## Persistence Strategy

- Snapshots (JSON via datastore)
  - Save/Load on mode switch and after search.
  - Stores `query`, tokens, `videoIds`, `videos`, `playlists`.
- Durable (SQLite/Django)
  - Entities: videos, playlists
  - Relation: playlist_videos(playlist_id, video_id)
  - UI No stays session-scoped and derived; do not persist globally.

## Smoke Script

- Steps
  - Start app and ensure `logs/app.log` is created.
  - Set Persistence → `SQLite`; confirm log line `set_persistence_mode` and `datastore=SqliteStore`.
  - Perform Videos search; confirm `execute_search`, `save_last_videos_result` and tokens in logs.
  - Toggle to `JSON`; use Back to Results; confirm `restore_videos` with counts.
  - Switch to Playlists mode; confirm `set_search_mode` and `save_last_playlists_result`.
  - Simulate playlists search error; confirm playlists fallback shows last saved data.

## SQLite Indices

- Added indices for performance parity:
  - `last_result_videos(last_id)`, `last_result_playlists(last_id)`
  - `playlist_videos(playlist_id)`, `playlist_videos(video_id)`

## Parity Verification Script

- Path: `scripts/verify_datastore_parity.py`
- Verifies `JsonStore` and `SqliteStore` return identical shapes for save/load.
- Skips `DjangoStore` if model schema is not aligned.
