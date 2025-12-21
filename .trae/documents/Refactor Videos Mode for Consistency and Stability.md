# Refactor Videos Mode for Consistency and Stability

## 1. Analysis of Current Issues
- **Missing Playlist Numbers**: The `playlistIndex` (e.g., "5") is not being assigned to videos during pagination (`show_videos_search_page`) or startup restoration in `VideosModeHandler`. This logic exists in `MainPage` but wasn't fully ported/utilized in the handler.
- **Lost Marks on Pagination**: The "Star" highlighting (visual indication of intersection) is not re-applied after fetching a new page of videos.
- **Pagination Display**: The `totalResults` might be inconsistent (missing in some responses vs others), causing the "Page X of Y" to jump.
- **Startup State**: The `playlist_index_map` (mapping playlist ID to number) might not be fully reconstructed before highlighting is attempted.

## 2. Refactoring Plan
### A. Centralize Video Enrichment
Create a shared `_enrich_videos_with_metadata(videos)` method in `VideosModeHandler` that:
1.  Rebuilds/Updates the `playlist_index_map` from `collected_playlists`.
2.  Iterates through `videos` and assigns `playlistIndex` and `playlistId` if they match known playlists.
3.  Links videos to the `MediaIndex` (for intersection logic).

### B. Standardize Table Population Flow
Refactor `populate_video_table` to be the **single source of truth** for rendering.
The flow for **Search**, **Pagination**, **Startup**, and **Back** will be:
1.  `videos = fetch_or_load()`
2.  `_enrich_videos_with_metadata(videos)`  <-- *Missing link*
3.  `populate_video_table(videos)`
4.  `if pinned_playlist: highlight_videos_for_playlist(pinned_playlist)` <-- *Re-apply marks*

### C. Fix Pagination Logic
- Ensure `totalResults` is persisted in `ConfigManager`.
- Use a robust fallback: if `totalResults` is missing, estimate based on `nextPageToken`.
- Update `PaginationBar` to format large numbers (e.g., "1,000,000") for readability.

## 3. Implementation Steps
1.  **Modify `VideosModeHandler.py`**:
    -   Add `_enrich_videos_with_metadata` method.
    -   Update `show_videos_search_page` to use the standardized flow.
    -   Update `load_last_search` to ensure `playlist_index_map` is built before highlighting.
    -   Update `back_to_video_results` to use the enriched flow.
2.  **Modify `MainPage.py`**:
    -   Ensure `playlist_index_map` is accessible or passed correctly.
3.  **Verify**:
    -   Check that playlist numbers appear after clicking "Next".
    -   Check that "Stars" persist after clicking "Next".
    -   Check that startup restores both numbers and stars.

## 4. Validation Checklist
- [ ] Startup: App opens, last search loads, pinned playlist is selected, stars appear, playlist numbers appear.
- [ ] Pagination: Click "Next", new videos load, playlist numbers appear (if matches exist), stars appear (if intersection exists).
- [ ] Back to Results: Returning from preview mode restores the exact state.
