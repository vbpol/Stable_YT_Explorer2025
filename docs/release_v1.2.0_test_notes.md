# Release Notes - v1.2.0-test (Quota & Stability Update)

## 🚀 Key Features

### 1. API Quota Optimization (Significant Reduction)
We have refactored the application to strictly follow YouTube Data API best practices, reducing quota consumption by **up to 96%** for common operations.

*   **Batching Implemented:**
    *   **Video Details:** Instead of 50 separate calls for a playlist page, we now use **1 call** with 50 IDs.
    *   **Playlist Enrichment:** Playlist video counts are now fetched in batches of 50.
*   **Redundant Calls Removed:** Merged duration, view count, and publication date fetching into single requests.
*   **Cost Impact:**
    *   Loading a 50-video playlist: **~2 units** (was ~51).
    *   Searching playlists: **~2 units** (was ~11).
    *   Validation: **1 unit** (was 100).

### 2. Smart API Key Management (Setup Page)
*   **Auto-Select Button:** Added a button to automatically cycle through all registered keys in `.env` and select the first working one.
*   **Quota Exhaustion Fallback:** The system now intelligently distinguishes between "Invalid" keys and "Quota Exhausted" keys. It will prefer a fully valid key, but accept a quota-exhausted key as a fallback (with a warning) to allow app access.
*   **Startup Check:** Silently ensures a valid key is active on application launch.

### 3. Stability & Bug Fixes
*   **Startup Video Marking:** Fixed an issue where videos in the intersection of the current search and selected playlist were not highlighted on startup.
*   **"Back to Results" Refactoring:** Modularized the logic for returning to search results to ensure UI consistency and prevent freezing.
*   **Playlist Matcher Service:** Centralized the logic for finding video-playlist intersections into `src/services/playlist_matcher.py` to ensure consistent behavior across Search, Startup, and Mode Switching.

## 📂 Changed Files
*   `src/playlist.py`: Core API batching logic.
*   `src/services/playlist_search.py`: Batched playlist enrichment.
*   `src/pages/setup_page.py`: Auto-select key UI and logic.
*   `src/pages/main/main_page.py`: Integration of new services and startup fixes.
*   `src/services/playlist_matcher.py`: New service for intersection logic.

## 🧪 Testing Instructions
1.  **Quota:** Browse large playlists and monitor quota usage in Google Cloud Console. It should be minimal.
2.  **Setup:** Corrupt your active key in the UI, then click "Auto Select". It should find a valid one from `.env`.
3.  **Startup:** Restart the app with a search loaded. Select a playlist. The videos belonging to that playlist should be highlighted immediately.
