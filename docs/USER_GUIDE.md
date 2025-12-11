# YouTube Playlist Explorer — User Guide

## Overview
- Explore YouTube playlists and videos, highlight matches, and download in HD.
- Two modes: `Playlists` browsing and `Videos` search with playlist intersection.
- Videos mode shows only intersecting playlists with stable numbering; no channel-level scanning.
- Startup performance is guaranteed: heavy operations are deferred until you press Search.

## Installation
- Ensure Python 3.10+ is installed.
- Install dependencies: `pip install -r requirements.txt`.
- Optional: create `.env` with `YOUTUBE_API_KEY` or `YOUTUBE_API_KEYS`.

## First Run
- Start the app: `python -m src.main`.
- The setup page appears if no API key or folder is set.
- Use the inline helper to open the Google Cloud Console and follow steps to obtain a YouTube Data API v3 key, then save settings.
- Startup is instant: the app does not perform network calls on launch and restores the last saved results for the selected mode.

## Key Features
- `Playlists` mode: search playlists, open, paginate videos, highlight query hits.
- `Videos` mode: search videos, collect related playlists, back to results restoration.
- Persistent last searches and mode in `data/`.
- HD download via `yt-dlp` with progress.

## Basic Workflow
- Enter a query and choose mode.
- In `Playlists` mode, select a playlist to view videos; navigate pages.
- In `Videos` mode, browse results; related playlists auto-collect in background.
- Use the status bar for progress and hints.

## Downloading Videos
- From `MainPage`, use download options and confirm.
- Videos save to your configured default folder with MP4 conversion.

## Troubleshooting
- No results: verify API key and network access.
- Rate limits: wait or use multiple keys via `YOUTUBE_API_KEYS`.
- If API quota or errors occur during search, the app automatically loads the last saved Videos results.
- UI not responding: avoid blocking operations; the app uses background threads.
- If packaged EXE fails by double-click, start via `dist/Run-YouTubePlaylistExplorer.cmd` or `dist/YouTubePlaylistExplorer/Run-App.cmd` which clears conflicting environment variables.
- Antivirus blocking PowerShell: builds use Python-only; allow the EXE and launcher via AV exclusions if needed.

---

## Quick Reference
- App entry: `src/main.py`.
- GUI root: `src/youtube_app.py`.
- Core page: `src/pages/main/main_page.py`.
- API layer: `src/playlist.py`.
- Persistence: `src/data/*.py`.
- Tools menu is hidden when `APP_ENV=production`.

## Release Workflow
- Branching scheme:
  - `main`: integrated, reviewed work.
  - `stable-YYYY-MM-DD`: release candidate snapshot.
  - `production-YYYY-MM-DD`: deployed version snapshot.
- Promote a release:
  - From `main`, create `stable-<date>`: `git checkout -b stable-YYYY-MM-DD && git push -u origin stable-YYYY-MM-DD`.
  - Verify on `stable-<date>`; then create `production-<date>`: `git checkout -b production-YYYY-MM-DD && git push -u origin production-YYYY-MM-DD`.
- Hotfix policy:
  - Fix on `main`.
  - Cherry-pick into the current `production-<date>` if needed.
  - Include fix in the next `stable-<date>` cut.
- Production mode:
  - Hide build tools by setting `APP_ENV=production` before launching.
  - Example (PowerShell): `$env:APP_ENV='production'; python -m src.main`.
