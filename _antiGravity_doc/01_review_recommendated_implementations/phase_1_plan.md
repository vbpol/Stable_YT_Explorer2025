# Phase 1: Foundation (Logging & Type Hinting)

## Goal
Establish a solid foundation for the application by implementing a centralized logging system and enforcing strict type hinting. This will improve debugging capabilities and code reliability.

## Steps

### Step 1.1: Centralized Logging (Completed)
- **Objective**: Replace scattered `print` statements and silent `pass` blocks with a unified logging mechanism.
- **Implementation**:
    - Create `src/logger.py`.
    - Integrate logger into `src/main.py`, `src/config_manager.py`, `src/playlist.py`, and `src/pages/main/main_page.py`.
- **Validation**: Verify logs are written to `logs/app.log`.

### Step 1.2: Strict Type Hinting (Completed)
- **Objective**: Improve code quality and catch potential errors early using static analysis.
- **Implementation**:
    - Create `mypy.ini` configuration.
    - Add type hints to `src/config_manager.py` and `src/playlist.py`.
- **Validation**: Run `mypy` (or verify code syntax if environment issues persist).

### Step 1.3: Fix "Back to Results" Logic (Completed)
- **Objective**: Ensure "Back to Results" button in Videos mode correctly restores the search results instead of showing the last viewed playlist.
- **Implementation**:
    - Modify `src/pages/main/main_page.py` to prevent `populate_videos_table_preview` from persisting state to `last_videos_search.json`.
- **Validation**: Verify "Back to Results" restores the video list.

### Step 1.4: Fix Playlist Mapping Persistence (Completed)
- **Objective**: Ensure that when "Back to Results" is clicked (or app is restarted), the "Playlist" column in the Videos table correctly shows the mapped playlist numbers.
- **Implementation**:
    - Modify `back_to_video_results` in `src/pages/main/main_page.py` to process playlists and normalize indices *before* rendering videos.
- **Validation**: Verify "Playlist" column shows numbers after "Back to Results".

### Step 1.5: Fix Video Preview & Highlighting (New)
- **Objective**: Restore the "Mark Video" (highlighting) feature and ensure "Populate Videos Table" correctly displays videos.
- **Implementation**:
    - **Refactor `highlight_videos_for_playlist`**:
        - Ensure it robustly identifies video intersections between the playlist and current search results.
        - Fix potential issues with `video_results_ids` or `_pl_hits_cache` being empty.
    - **Fix `populate_videos_table_preview` & `_render_playlist_videos`**:
        - Add error handling for API quota limits (e.g., if `get_videos` fails).
        - Implement fallback to display "No videos found (or API quota exceeded)" if `current_videos` is empty.
        - Ensure `_preview_only_hits` logic doesn't incorrectly hide all videos when previewing a playlist.
- **Validation**:
    1.  Select a playlist -> "Populate Videos Table". Verify videos are shown (or error message if quota exceeded).
    2.  Select a playlist -> "Highlight Related Videos". Verify matching videos in the search results are highlighted with a star.
