# Changelog

## 2025-12-22 (v1.1.3)

### Features & UI
- **Pagination Toggle**: Added a "Pagination" checkbox in the search bar.
    - **Enabled (Default)**: Shows paginated results (e.g., 10 per page) with navigation controls.
    - **Disabled**: Hides pagination bar and shows ALL loaded videos in one scrollable list.
- **Search Flow Optimization**:
    - "Fetch More & Export" clarifies API limits vs. estimates.
    - Reduced startup lag by loading history asynchronously in the background.
    - Fixed "Not Responding" state during app launch.

### Fixes
- **Playlist Sorting**: Fixed non-continuous and disordered playlist numbers in the Videos table. Videos are now consistently sorted by their associated Playlist Index.
- **Data Consistency**: ensured `playlistIndex` mapping uses the global playlist list (Source of Truth) rather than just the visible page, preventing "renumbering" glitches when navigating pages.

### Technical Improvements
- **Startup Checks**: Implemented API key validation on startup with visual feedback (Search button color: Green/Orange/Red).
- **Performance**: Optimized playlist scanning (`VideoPlaylistScanner`) using channel-based batching to significantly reduce API calls.
- **Stability**: Fixed history loss and lag when switching between Videos and Playlists modes.
- **AI Protocols**: Added rigorous AI implementation rules to `project_rules.md`.

## 2025-12-21 (v1.1.1)

### Improvements

- **Search Consistency**: Updated search results popup to clarify that large result counts (e.g., 1,000,000) are API estimates, reducing confusion when actual exportable results are fewer.
  - Code: `src/pages/main/main_page.py`

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
