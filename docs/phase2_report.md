# Phase 2 Migration Report — Django ORM Data Layer (SQLite Backend)

## Overview

- Goal: Introduce a Django ORM implementation of the data layer that can be swapped in without changing the UI. Keep SQLite as the backing store, no web server, no migrations required.
- Outcome: The app dynamically selects `DjangoStore` when Django is available, otherwise falls back to `SqliteStore`. UI behavior remains identical.

## Architecture Changes

- Before (Phase 1): UI → `DataStore` → `SqliteStore` → SQLite file
- After (Phase 2): UI → `DataStore` → `DjangoStore` (if available) → same SQLite file

```
[Search UI + MainPage] ──► [DataStore API] ──► (DjangoStore │ SqliteStore)
                                               │
                                               └── app.sqlite3 (shared)
```

- Selection logic: Try importing Django and construct `DjangoStore`; if unavailable, use `SqliteStore` transparently.

## File Structure Updates

- New:
  - `backend/__init__.py`
  - `backend/media/__init__.py`
  - `backend/media/models.py` — ORM models mapped to existing SQLite tables
  - `src/data/django_store.py` — `DataStore` implementation using Django ORM
  - `src/data/factory.py` — Store selection (Django preferred, SQLite fallback)
- Existing (Phase 1):
  - `src/data/datastore.py` — interface
  - `src/data/sqlite_store.py` — SQLite implementation
  - `src/data/app.sqlite3` — database file

## Models (Django)

- All models use `managed=False` and `db_table` to point at Phase 1 tables.
- Files:
  - `backend/media/models.py:1-61`
    - `Playlist` → `playlists`
    - `Video` → `videos`
    - `PlaylistVideo` → `playlist_videos` (with `unique_together` on playlist/video)
    - `LastResult` → `last_results`
    - `LastResultVideo` → `last_result_videos`
    - `LastResultPlaylist` → `last_result_playlists`

## Store Selection

- `src/data/factory.py:1-8`
  - Tries to import Django; if successful, returns `DjangoStore`.
  - On failure, returns `SqliteStore`.

## Django Store Implementation

- `src/data/django_store.py:1-108`
  - Configures Django in-process:
    - `DATABASES` → sqlite3, pointing to `src/data/app.sqlite3`
    - `INSTALLED_APPS` → `backend.media` plus minimal core
  - Exposes same `DataStore`-style methods:
    - `upsert_playlist`, `upsert_video`, `link_video_to_playlist`
    - `save_last_videos_result`, `load_last_videos_result`
    - `save_last_playlists_result`, `load_last_playlists_result`
  - Uses `update_or_create` to keep records in sync with incoming data

## Controller Wiring

- `src/youtube_app.py:7, 23-26`
  - Replaced `SqliteStore` direct wiring with store factory (`get_datastore`) to prefer Django when present.

## UI Integration (unchanged)

- MainPage continues to call the same repository functions as Phase 1:
  - Playlists mode save: `src/pages/main/main_page.py:216-220`
  - Videos mode background save: `src/pages/main/main_page.py:296-304`
  - Videos mode initial save: `src/pages/main/main_page.py:315-321`
  - Back to Results load: `src/pages/main/main_page.py:331-369`

## Side-by-Side Behavior

- Phase 1 (SQLite): data saved/loaded via direct `sqlite3` calls.
- Phase 2 (Django): identical data saved/loaded via ORM calls.
- UI behavior: identical; no changes required in views or event handlers.

## Infograph

```
-----------------------------+         +------------------+
|         MainPage/UI         |  calls  |    DataStore     |
|  Search, paging, status     | ───────►|  API (common)    |
-----------------------------+         +------------------+
                                              │
                     prefers DjangoStore ─────┤───── falls back SqliteStore
                                              │
                                       +------------------------+
                                       |  SQLite DB (app.sqlite3)|
                                       +------------------------+
```

## Testing

- Compilation checks:
  - `py -3 -m py_compile backend/media/models.py src/data/django_store.py src/data/factory.py src/youtube_app.py`
- Manual validation:
  - Search in Videos/Playlists modes
  - Open playlist, navigate pages, Back to Results
  - Observe highlights, pin/bring‑to‑top, numbering, and status messages
  - Behavior identical whether Django is installed or not
  - Logs: confirm store selection (`DjangoStore` or `SqliteStore`) and restore paths in `logs/app.log`

## Constraints

- `managed=False`: models do not create or alter tables; they operate on existing Phase 1 schema.
- In-process configuration only; no web server, migrations, or admin UI.
- If Django import fails, the app runs on SQLite store automatically.

## Rollback

- To disable Django usage: uninstall or remove Django from the venv. The app will keep using `SqliteStore`.

## What’s Next (optional, not required for Phase 2)

- If you later want deeper persistence (e.g., historical searches), add tables and set `managed=True` with migrations. The UI can remain unchanged due to the stable `DataStore` API.