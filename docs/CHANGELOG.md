# Changelog

## 2025-12-16 (v1.1.0)

### New Features

- **Popup Notification**: Added a popup dialog on search completion showing the total number of videos found for the keyword.
  - Code: `src/pages/main/main_page.py`

### Bug Fixes & Improvements

- **Pagination Counts**: Fixed "crazy" pagination counts (e.g., "Page 2 of 100000") by correctly interpreting YouTube API `totalResults` as an estimate and formatting it with commas for readability.
  - Code: `src/ui/pagination_bar.py`, `src/pages/main/videos_mode_handler.py`
- **Video Marks**: Fixed issue where video selection marks (stars/highlights) were lost during pagination or view switching.
  - Code: `src/pages/main/video_section.py`
- **Playlist Numbers**: Fixed missing playlist numbers in the videos panel when navigating Next/Previous pages.
  - Code: `src/pages/main/videos_mode_handler.py` (`_enrich_videos_with_metadata`)
- **Page Index Drift**: Fixed page index not resetting to 1 on new searches.
- **Cache Persistence**: Ensured `video_total_results` is correctly saved to and loaded from cache.

## 2025-12-03

### UI

- Window resized and minimum size set via `ui.window_size` (default `1100x720`).
  - Code: `src/youtube_app.py:21`
- Single mid-row progress with dynamic labels ("Mapping playlists" / "Refreshing statuses").
  - Code: `src/pages/main/main_page.py:180`, `src/pages/main/playlist_section.py:335`
- Status bar summary now reads: `Collected <playlists> playlists for <videos> videos` in Videos mode.
  - Code: `src/pages/main/main_page.py:515`, `src/pages/main/main_page.py:704`

### Tables & Pagination

- Introduced reusable components:
  - `PaginationBar` (one-row controls) — `src/ui/pagination_bar.py`
  - `TablePanel` (vertical stack: PaginationBar above table) — `src/ui/table_panel.py`
- Integrated components in Videos and Playlists sections.
  - Videos: `src/pages/main/video_section.py:18`, `src/pages/main/video_section.py:129`
  - Playlists: `src/pages/main/playlist_section.py:18`
- Pagination visibility is dynamic per table using threshold `ui.pagination_min_rows` (default 10) or `PAGINATION_MIN_ROWS` env var.
  - Loader: `src/config_manager.py:158`
  - Visibility hook: `src/ui/table_panel.py:22`
  - Videos apply: `src/pages/main/video_section.py:152`
  - Playlists apply: `src/pages/main/playlist_section.py:308`

### Pagination Refinements (Count-Based, Stable)

- Page indicator and visibility now use count-based pages regardless of API tokens:
  - Total pages = `ceil(total_items / page_size)`.
  - Indicator shows `Page X of Y`.
  - Bar hides when `Y == 1`.
  - Code: `src/ui/table_panel.py:29`.
- Total label reflects the actual number of rows in the visible table to avoid races:
  - Code: `src/pages/main/main_page.py:556`, `src/pages/main/main_page.py:655`, `src/pages/main/main_page.py:931`.
- Default indicator updated to avoid `0/0` pre-search state:
  - Code: `src/ui/pagination_bar.py:18`.
- Videos page-size combobox triggers Videos search, not playlists:
  - Code: `src/pages/main/video_section.py:134`.

### Before/After Highlights

- Before: `Page 0 of 0`, `Total: 0` could appear after search due to timing.
- After: `Page 1 of 1` and `Total: <actual rows>`, bar hidden when only one page.
- Before: Changing videos page size didn’t refresh videos.
- After: Changing videos page size re-runs the videos search with the new size.

### Scanning & Stability

- Refactored videos→playlists scanning into `src/services/video_playlist_scanner.py` (thread pool, per-worker client).
  - Integration: `src/pages/main/main_page.py:432`
- Removed duplicate progress bars; mid-row is the single indicator.
  - Videos progress forwarding: `src/pages/main/video_section.py:141`
  - StatusBar simplified: `src/pages/main/status_bar.py`

### CI

- Added basic GitHub Actions workflow for compile and tests: `.github/workflows/ci.yml`

### Settings

- New settings in `config.json` (under `ui`):
  - `window_size`: e.g., `"1100x720"`
  - `pagination_min_rows`: default `10`
  - Environment override: `PAGINATION_MIN_ROWS`
