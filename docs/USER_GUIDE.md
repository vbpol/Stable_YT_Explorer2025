# YouTube Playlist Explorer — User Guide

## Overview
- Explore YouTube playlists and videos, highlight matches, and download in HD.
- Two modes: `Playlists` browsing and `Videos` search with playlist intersection.

## Installation
- Ensure Python 3.10+ is installed.
- Install dependencies: `pip install -r requirements.txt`.
- Optional: create `.env` with `YOUTUBE_API_KEY` or `YOUTUBE_API_KEYS`.

## First Run
- Start the app: `python run.py` or `python -m src.main`.
- Provide your API key and default download folder in the setup page.

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
- UI not responding: avoid blocking operations; the app uses background threads.

---

## Quick Reference
- App entry: `src/main.py`.
- GUI root: `src/youtube_app.py`.
- Core page: `src/pages/main/main_page.py`.
- API layer: `src/playlist.py`.
- Persistence: `src/data/*.py`.

