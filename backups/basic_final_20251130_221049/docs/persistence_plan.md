# Persistence Migration Plan — SQLite first, Django-ready

## Objectives

- Replace local JSON persistence with SQLite for videos/playlists while preserving all current UI flows and behavior.
- Introduce a clean OOP data layer so the app can later switch to Django ORM with minimal changes.
- Keep code simple and robust; no new features beyond persistence.

## Approach

- Phase 1 (now): Implement SQLite-backed persistence with a small repository layer. No server, no Django project yet. Focus on replacing the JSON saves/loads used by the app.
- Phase 2 (next): Swap the repository implementation to use Django ORM models that mirror the SQLite schema. Integration remains in-process (no web server required). The UI continues unchanged.

## Data Model (SQLite)

- playlists
  - `playlist_id TEXT PRIMARY KEY`
  - `title TEXT`
  - `channel_title TEXT`
  - `video_count INTEGER NULL`  
  - `created_at DATETIME DEFAULT CURRENT_TIMESTAMP`

- videos
  - `video_id TEXT PRIMARY KEY`
  - `title TEXT`
  - `channel_title TEXT`
  - `duration TEXT NULL`
  - `published TEXT NULL`
  - `views INTEGER NULL`

- playlist_videos
  - `playlist_id TEXT` (FK → playlists)
  - `video_id TEXT` (FK → videos)
  - `position INTEGER NULL`
  - PRIMARY KEY (`playlist_id`, `video_id`)

- last_results
  - `id INTEGER PRIMARY KEY AUTOINCREMENT`
  - `mode TEXT` CHECK (`mode` IN ('videos','playlists'))
  - `query TEXT`
  - `saved_at DATETIME DEFAULT CURRENT_TIMESTAMP`
  - `next_page_token TEXT NULL`
  - `prev_page_token TEXT NULL`

- last_result_videos
  - `last_id INTEGER` (FK → last_results)
  - `video_id TEXT` (FK → videos)

- last_result_playlists
  - `last_id INTEGER` (FK → last_results)
  - `playlist_id TEXT` (FK → playlists)

Notes:
- Tokens are stored for “Videos” search pagination.
- Playlists “No” numbering remains UI-derived and reset per search; not stored globally.

## Repository API (OOP)

- `class DataStore:`  
  Abstract interface; later two impls: `JsonStore` (compat) and `SqliteStore`.

- Core methods:
  - `save_last_videos_result(query, videos, playlists, next_token, prev_token, video_ids)`
  - `load_last_videos_result() -> {videos, playlists, next_token, prev_token, video_ids}`
  - `save_last_playlists_result(query, playlists)`
  - `load_last_playlists_result() -> [playlists]`
  - `upsert_playlist(playlist_dict)`
  - `upsert_video(video_dict)`
  - `link_video_to_playlist(playlist_id, video_id, position=None)`
  - `get_playlist_videos(playlist_id, limit, offset) -> [videos]`

Return shapes mirror existing dicts to avoid UI refactors.

## Integration Points (current JSON touches)

- Save videos results (JSON):
  - `src/pages/main/main_page.py:315-321` and `src/pages/main/main_page.py:297-306`  
  Replace with `DataStore.save_last_videos_result(...)` and background upserts for `videos`/`playlists`.

- Load videos results on Back to Results:
  - `src/pages/main/main_page.py:331-369`  
  Replace with `DataStore.load_last_videos_result()`.

- Save playlists results (JSON):
  - `src/pages/main/main_page.py:216-217` (playlists mode)  
  Replace with `DataStore.save_last_playlists_result(...)`.

- Load playlists last result (if used elsewhere):  
  Add `DataStore.load_last_playlists_result()` consumption where needed.

## Phase 1 Tasks (SQLite)

1) Create `SqliteStore` (no Django)  
   - Location: `src/data/sqlite_store.py`  
   - Responsibilities: DB init, migrations (DDL create-if-not-exists), CRUD.

2) Add `DataStore` interface  
   - Location: `src/data/datastore.py`  
   - Provide the methods listed above.

3) Wire into MainPage  
   - Replace `ConfigManager.save_json/load_json` calls with `DataStore` equivalents in:
     - `src/pages/main/main_page.py:216-321, 331-369, 297-306`
   - Keep UI unchanged.

4) Background upserts  
   - While collecting playlists/videos, upsert entities and links without blocking the UI.

5) Migration from existing JSON  
   - On first run with DB empty, import `data/last_videos_search.json` and `data/last_playlists_search.json` into the DB.

## Phase 2 Tasks (Django ORM)

1) Create Django project in `backend/` using SQLite  
   - Apps: `media` (models for playlists, videos, playlist_videos, last_results).

2) Mirror the SQLite schema as Django models  
   - Migration files under `backend/media/migrations/`.

3) Implement `DjangoStore`  
   - Location: `src/data/django_store.py`  
   - Implements `DataStore` using Django ORM (import settings, setup `django.conf.settings` in-process).

4) Toggle store implementation  
   - Simple factory: `DataStoreFactory.from_env()` returning either `SqliteStore` or `DjangoStore`.

## Testing

- Unit tests: verify save/load parity for last results and entity upserts (videos/playlists/links).
- Manual: perform searches, open playlists, use Back to Results; confirm UI behaves identically.

## Rollback

- If any issue with SQLite, switch `DataStore` back to `JsonStore` while keeping the same method calls.

## Constraints

- Preserve existing UI and features; no new UI surfaces.
- Keep background threads and `after()` updates; do not block the main loop.

## Notes

- No additional recommendations or enhancements beyond persistence migration are included here.