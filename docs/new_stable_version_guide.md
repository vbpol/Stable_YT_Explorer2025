# New Stable Version Documentation

## Overview

This document provides a comprehensive guide to the new stable version features, including implementation details, integration steps, validation, and testing procedures. It serves as a reference for developers and testers to ensure the stability and quality of the release.

## New Features

### 1. Channel Title Folder Naming & Fallback

**Description:**
Non-playlist video downloads now organize files into folders named `Videos - {Channel Title}`. If the channel title is unavailable, it falls back to `Videos - {Search Query}`. A user preference toggles this behavior.

**Implementation:**
- **Logic:** `src/pages/main/download_manager.py` (`_target_folder`) and `src/pages/main/main_page.py` (`_video_target_folder`).
- **Config:** `src/config_manager.py` adds `use_channel_title_fallback` (boolean).
- **UI:** `DownloadOptionsDialog` includes a checkbox "Prefer channel title for 'Videos - {...}'".

**Integration:**
- Wired into the download flow (`DownloadManager.start`) and status refresh (`refresh_video_statuses`).
- Persisted in `config.json` under `ui.use_channel_title_fallback`.

**Validation:**
- [x] Verify non-playlist video download creates `Videos - {Channel Title}`.
- [x] Verify fallback to `Videos - {Query}` when channel title is missing or toggle is off.
- [x] Verify playlist downloads remain `Playlist - {Title}`.

**Testing:**
- **Unit:** Mock `v['channelTitle']` and assert folder path.
- **Manual:** Toggle option in Download Options, download a video, check folder name.

### 2. Simplified Video Filenames

**Description:**
Downloaded video files now use the format `{Title}.{ext}` instead of `{ID} - {Title}.{ext}`.

**Implementation:**
- **Logic:** `src/pages/main/download_manager.py` updates `ydl_opts['outtmpl']` to `os.path.join(folder, '%(title)s.%(ext)s')`.

**Integration:**
- Affects all downloads (playlist and non-playlist).
- Status checks (`_find_downloaded_file`) already match by title, ensuring compatibility.

**Validation:**
- [x] Verify downloaded file name matches video title exactly.
- [x] Verify refresh status correctly identifies the file.

**Testing:**
- **Manual:** Download a video, inspect file explorer for name format.

### 3. Downloaded Videos Popup Enhancements

**Description:**
The "Downloaded Videos" popup now displays the folder name (Playlist or Channel folder) in the first column and supports sorting and opening the specific folder.

**Implementation:**
- **UI:** `src/pages/main/download_manager.py` (`show_results_popup`).
- **Column:** Renamed "Playlist" to "Playlist / Video Folder".
- **Data:** Populates with `os.path.basename(folder)` for non-playlist videos.

**Integration:**
- Triggered via "Show Results" after download or manually.
- Connects "Open Folder" and "Play Video" actions to the correct paths.

**Validation:**
- [x] Verify first column shows Playlist title for playlists.
- [x] Verify first column shows `Videos - {Channel}` for non-playlists.
- [x] Verify "Open Folder" opens the specific subfolder.

**Testing:**
- **Manual:** Complete a mixed download batch, open popup, check column values and button actions.

### 4. UI Thread Safety Fixes

**Description:**
Fixed `AttributeError: 'MainPage' object has no attribute '_safe_ui'` by initializing the thread-safe UI helper at class construction.

**Implementation:**
- **Logic:** `src/pages/main/main_page.py` defines `_safe_ui` method in `__init__` (or class body) instead of lazy local assignment.

**Integration:**
- Used by background threads (`_fetch_playlists`, etc.) to update UI without crashing.

**Validation:**
- [x] Verify no `AttributeError` during playlist mapping or background scans.

**Testing:**
- **Manual:** Run "Map Playlists" or heavy search tasks that trigger background threads.

## Implementation Order (Logical Flow)

1.  **Coding (Implementation):**
    *   Update `download_manager.py` for folder naming and filenames.
    *   Update `config_manager.py` for persistence.
    *   Update `download_options_dialog.py` for UI controls.
    *   Fix `main_page.py` for thread safety and status logic.

2.  **Integration:**
    *   Connect config to UI state.
    *   Ensure `DownloadManager` uses `MainPage` logic for consistency.
    *   Verify persistence across restarts.

3.  **Validation (Pre-Commit):**
    *   Run "Visual Tests" (UI checks).
    *   Verify folder creation and file naming on disk.
    *   Check console for thread errors.

4.  **Testing (Post-Merge):**
    *   Full regression test (Search -> Download -> Play -> Refresh).
    *   Verify backward compatibility (existing downloads detected).

## Validation Checklist

*   [ ] **Feature 1:** Channel Title Fallback works (On/Off).
*   [ ] **Feature 2:** Filenames are clean (`{Title}.mp4`).
*   [ ] **Feature 3:** Popup shows correct folder names and opens them.
*   [ ] **Feature 4:** No background thread crashes (`_safe_ui`).
*   [ ] **General:** App starts, searches, and plays videos correctly.

## Git Merge Strategy

1.  Commit all changes to current branch (`production-2025-12-05` or similar).
2.  Push to origin.
3.  Checkout `main`.
4.  Merge `production-2025-12-05` into `main`.
5.  Push `main` to origin.
