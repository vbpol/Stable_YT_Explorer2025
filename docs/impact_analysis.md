# Impact Analysis: Root Cleanup, API Caching, and Refactoring

## 1. Problem Statement
The user reported three main issues:
1. **App Root Clutter:** "Video - *" and "Playlist - *" folders appearing in the application root.
2. **API Token Exhaustion:** Rapid consumption of YouTube API quota.
3. **Code Quality:** Need for refactoring into separate files, cleaning dead code, and avoiding duplicates.

## 2. Implemented Solutions

### 2.1. App Root Cleanup
- **Solution:** Centralized path management logic into a new service `DownloadPathManager`.
- **Mechanism:** 
  - `src/services/download_path_manager.py` resolves target directories based on video metadata (Playlist title, Channel title, or Search query).
  - All downloads now default to structured subfolders within the user's configured Download Folder, never the App Root.
  - A cleanup script `scripts/cleanup_root.py` was executed to move existing legacy folders to `Legacy_Downloads`.
- **Impact:** App root is clean. Future downloads are organized.

### 2.2. API Token Optimization
- **Solution:** Implemented persistent SQLite-based caching for YouTube API responses.
- **Mechanism:**
  - `src/services/cache_manager.py` handles storage of JSON responses with a 7-day TTL (Time To Live).
  - `src/playlist.py` wraps all API calls (search, playlist details, video details) with `_execute_with_cache`.
  - `VideoPlaylistScanner` updated to respect caching and threading safety.
- **Impact:** 
  - Repeated queries (e.g., re-scanning the same video list) cost 0 tokens.
  - "Playlist contains video" checks are cached, significantly reducing overhead for the "Map Playlists" feature.

### 2.3. Refactoring & Cleanup
- **Solution:** Modularized code and removed dead files.
- **Mechanism:**
  - `CacheManager` and `DownloadPathManager` isolated in `src/services/`.
  - `VideoPlaylistScanner` refactored for thread safety and caching integration.
  - Deleted unused file `src/youtube_app.pre_v1_0_0.py`.
- **Impact:** Better separation of concerns (UI vs. Service vs. Data), easier maintenance, and improved stability.

## 3. Risk Assessment

| Risk | Probability | Mitigation |
|------|-------------|------------|
| **Cache Staleness** | Low | Default TTL is 7 days. Can be cleared by deleting `src/data/api_cache.sqlite3`. |
| **File Locking (Windows)** | Medium | `CacheManager` uses short-lived connections. Tests updated with retry logic. |
| **Migration Issues** | Low | `cleanup_root.py` is non-destructive (moves, doesn't delete). |
| **Thread Safety** | Medium | `VideoPlaylistScanner` updated with explicit locks for shared state. |

## 4. Verification Plan
- **Unit Tests:** `tests/test_download_path_manager.py` and `tests/test_cache_manager.py` pass.
- **Manual Check:** Verify `api_cache.sqlite3` grows during use. Verify no new folders in root during download.
