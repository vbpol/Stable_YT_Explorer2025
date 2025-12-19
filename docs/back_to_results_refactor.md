# Back to Results Refactoring and Pagination Fix

## Overview
This document details the refactoring of the `back_to_video_results` feature and the resolution of pagination issues in the YouTube Downloader application.

## Changes

### 1. Pagination Logic Isolation
- **Module:** `src/ui/pagination_bar.py`
- **Description:** The pagination logic was extracted from `TablePanel` and `VideoSection` into a dedicated `PaginationBar` class. This ensures a Single Source of Truth (SSOT) for pagination state and UI updates.
- **Key Methods:**
  - `set_page_info(index, has_prev, has_next, total_items)`: Centralized method to update the pagination indicator, buttons, and visibility.
  - `bind_prev(callback)`, `bind_next(callback)`: Methods to bind navigation events.

### 2. Pagination Indicator Fix
- **Issue:** The "Page x of pages" indicator was static ("Page 1 of") and did not update on navigation.
- **Fix:**
  - Added explicit calculation of `total_pages` using `math.ceil(total_items / page_size)` in `PaginationBar`.
  - Updated `main_page.py` to calculate an estimated `total_items` for Videos search (since API token pagination doesn't provide total count) using `page_size * current_index + (page_size if has_next else 0)`.
  - Ensured `set_page_info` is called with the correct `index`, `has_prev`, `has_next`, and `total_items` after every search and navigation event.

### 3. Back to Results Refactoring
- **File:** `src/pages/main/main_page.py`
- **Description:** The `back_to_video_results` method was monolithic and difficult to maintain. It has been refactored into smaller, single-responsibility helper methods:
  - `_load_last_results_data()`: Handles loading data from the Datastore or ConfigManager.
  - `_restore_search_state(data)`: Restores internal state (MediaIndex, caches, query, IDs).
  - `_restore_ui_state(videos, playlists, data)`: Updates the UI components (VideoTree, PlaylistTree, PaginationBar, Buttons).
  - `_async_recollect_playlists()`: Handles the background task of re-collecting playlists if needed.
  - `_insert_video_chunk(videos, start_index)`: Handles recursive chunk insertion of videos into the treeview to prevent UI freezing.

### 4. Integration
- **VideoSection:** Updated to route Previous/Next buttons to the correct handler based on the active mode (Videos vs. Playlists).
- **MainPage:** Wired the refactored `back_to_video_results` into the application flow, ensuring all state is correctly restored and the UI is updated consistent with the new pagination logic.

## Validation
- **Pagination:** Verified that the page indicator updates correctly (e.g., "Page 2 of 3") when navigating.
- **Back to Results:** Confirmed that clicking "Back to Results" restores the previous search state, including the correct page number and indicator text.
- **Refactoring:** The code is now more modular, easier to read, and follows the Single Responsibility Principle.
