# Phase 1 Migration Report — SQLite Data Layer (Django‑Ready)

## Overview

- Goal: Replace local JSON persistence with a simple, robust SQLite repository while keeping all UI flows unchanged and preparing for a later Django ORM swap.
- Outcome: The app now stores “last results” (Videos/Playlists) and entities (videos/playlists, links) in `src/data/app.sqlite3` via a small OOP layer. UI behavior, performance, and background threading are preserved.

## Architecture Changes

- Before:
  - UI → `ConfigManager.save_json/load_json` → JSON files under `data/`
- After:
  - UI → `DataStore` interface → `SqliteStore` → SQLite DB (`src/data/app.sqlite3`)

```
[Search UI + MainPage] ──► [DataStore API] ──► [SqliteStore] ──► [SQLite file]
      │                                 │
      └── status updates, pagination ───┘
```

- Future (Phase 2): Swap `SqliteStore` with `DjangoStore` using the same `DataStore` methods (no UI changes).

## File Structure Updates

- New:
  - `src/data/datastore.py` — DataStore interface
  - `src/data/sqlite_store.py` — SQLite implementation and schema
  - `src/data/app.sqlite3` — SQLite database file (auto‑created)
  - `docs/persistence_plan.md` — Technical plan
- Modified:
  - `src/youtube_app.py` — Wire `SqliteStore` into the app controller
  - `src/pages/main/main_page.py` — Use the datastore for saving/loading last results

## Code References (key integration points)

- App wiring:
  - `src/youtube_app.py:18-22` initialize GUI, then `self.datastore = SqliteStore()` is set; held on the controller for pages to use

- Playlists mode save (JSON → SQLite):
  - `src/pages/main/main_page.py:216` replaced with `self.controller.datastore.save_last_playlists_result(query, enriched)` to persist last playlists search results

- Videos mode background save (JSON → SQLite):
  - `src/pages/main/main_page.py:296-304` replaced with `save_last_videos_result` to persist videos, collected playlists, and tokens

- Videos mode initial save (JSON → SQLite):
  - `src/pages/main/main_page.py:315-321` replaced with `save_last_videos_result` (videos only and tokens) so Back to Results can restore immediately

- Back to Results (load last videos result from SQLite):
  - `src/pages/main/main_page.py:331-369` loads via `self.controller.datastore.load_last_videos_result()`, then repopulates the Videos and Playlists panels and restores tokens/page indicator

## Data Model (SQLite)

- `playlists(playlist_id PK, title, channel_title, video_count, created_at)`
- `videos(video_id PK, title, channel_title, duration, published, views)`
- `playlist_videos(playlist_id, video_id, position, PK(playlist_id, video_id))`
- `last_results(id PK, mode, query, saved_at, next_page_token, prev_page_token)`
- `last_result_videos(last_id FK, video_id FK)`
- `last_result_playlists(last_id FK, playlist_id FK)`

## Repository API

- `DataStore.save_last_videos_result(query, videos, playlists, next_token, prev_token, video_ids)`
- `DataStore.load_last_videos_result() -> {videos, playlists, nextPageToken, prevPageToken}`
- `DataStore.save_last_playlists_result(query, playlists)`
- `DataStore.load_last_playlists_result() -> [playlists]`
- `SqliteStore.upsert_playlist(pl)`, `upsert_video(v)`, `link_video_to_playlist(playlist_id, video_id, position=None)`

## UI Behavior Preservation

- Search, pagination, status updates, pin/bring‑to‑top, playlist numbering, and highlight logic remain unchanged.
- Background threads continue to update the UI via `after()`; persistence runs off the main loop to avoid freezes.

## Side‑by‑Side Comparison

- Old save (Videos):
  - `ConfigManager.save_json(get_last_search_path('videos'), {videos, playlists, nextPageToken, prevPageToken})`
- New save (Videos):
  - `self.controller.datastore.save_last_videos_result(query, videos, playlists, next, prev, video_ids)`

- Old load (Back to Results):
  - `ConfigManager.load_json(path)`
- New load (Back to Results):
  - `self.controller.datastore.load_last_videos_result()`

## Testing Performed

- Compilation sanity:
  - `py -3 -m py_compile src/youtube_app.py src/pages/main/main_page.py` and `src/data/*.py`
- Manual flows:
  - Videos mode search, open playlist, pagination, Back to Results — state restored correctly (items count, page indicator, tokens)
  - Playlists mode search — last playlists results saved
  - Status bar messages display as before
  - Highlights in playlist view still visible
  - Logs: verify `logs/app.log` entries for searches, saves, loads, and restores

## Known Constraints

- Persistence focuses on “last results” parity and entity upserts; deep playlist mapping remains best‑effort by design to keep the UI responsive.
- If `SqliteStore` initialization fails, the UI continues to run; persistence falls back safely without breaking flows.

## Next (Phase 2 — Django ORM)

- Mirror the SQLite schema as Django models, implement `DjangoStore` with the same `DataStore` methods, and switch by factory without touching UI code.