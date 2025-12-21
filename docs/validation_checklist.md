# Validation Checklist

## 1. File System Structure
- [ ] **App Root Cleanliness**:
    - Ensure no `Video - *` or `Playlist - *` folders exist in the application root directory.
    - Check that `Legacy_Downloads` folder contains previously moved items (if any).
- [ ] **Download Targets**:
    - Perform a download of a video belonging to a playlist.
    - Verify it saves to `[Default_Download_Folder]/Playlist - [Playlist_Title]/`.
    - Perform a download of a video NOT in a playlist.
    - Verify it saves to `[Default_Download_Folder]/Channel - [Channel_Title]/` or `Videos - [Query]/`.

## 2. API Token Usage (Caching)
- [ ] **Cache Creation**:
    - Run a search.
    - Verify `src/data/api_cache.sqlite3` file exists and size > 0.
- [ ] **Quota Savings**:
    - Run the same search term twice.
    - Observe that the second search loads instantly and does not increment API quota (if verifiable via console).
    - Disconnect internet and try to load previously searched term (should work from cache).
- [ ] **Scanner Efficiency**:
    - Run "Map Playlists" on a set of videos.
    - Rerun it. The second run should be much faster and hit the database instead of the API.

## 3. Functionality
- [ ] **Video Scanning**:
    - Ensure `VideoPlaylistScanner` correctly identifies playlists for videos.
    - Verify thread safety: no crashes during rapid scanning.
- [ ] **Playback**:
    - Ensure downloaded videos play correctly (paths are valid).

## 4. Regression Testing
- [ ] **UI Responsiveness**:
    - Ensure UI does not freeze during scanning (threading check).
- [ ] **Startup**:
    - Ensure app starts without errors related to DB locking or missing paths.
