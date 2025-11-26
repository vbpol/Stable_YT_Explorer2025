# Change Log — Current Session

## Architecture
- Data layer uses `DataStore` with multiple implementations:
  - `JsonStore` — restored and preferred when legacy files exist (`src/data/json_store.py:1-37`).
  - `SqliteStore` — relational backend (`src/data/sqlite_store.py:1-97`).
  - `DjangoStore` — ORM over the same SQLite schema (`src/data/django_store.py:1-108`).
- Store selection prioritizes user setting, then legacy JSON, then Django/SQLite (`src/data/factory.py:1-18`).

## File Structure Updates
- Added: `src/data/json_store.py`, `src/logger.py`, `docs/dev_workflow.md`, `docs/change_log.md`.
- Modified: `src/youtube_app.py`, `src/pages/main/main_page.py`, `src/pages/main/menu_section.py`, `src/config_manager.py`, `docs/README.md`, `docs/phase1_report.md`, `docs/phase2_report.md`.

## Coding Changes
- Startup and radio toggle restore use datastore reads:
  - `src/pages/main/main_page.py:29-33`, `155-190`, `331-352`.
- Removed duplicate Back to Results button; single button in pagination:
  - `src/pages/main/video_section.py:125-132, 158-163`.
- Graceful network fallback in Videos mode:
  - `src/pages/main/main_page.py:223-233`.
- Logging added:
  - `src/logger.py`, `src/youtube_app.py:13, 23-26`, restore/search/save logs in `src/pages/main/main_page.py`.
- Video player window cleans up VLC to stop background audio:
  - `src/pages/main/video_player.py:13-17, 162-173, 182-203`.
- Persistence menu to switch between JSON/SQLite/Django without restart:
  - `src/pages/main/menu_section.py: Persistence menu`, `src/pages/main/main_page.py:817-838`.

## New Features
- Configurable persistence mode saved in `config.json` (`src/config_manager.py`).
- Automatic fallback to last saved results on network errors.
- Centralized logging supporting diagnostics of store selection and restores.

## Verification & Docs
- README updated with Logging and Backups.
- Phase reports include log-based testing steps.
- Logs written to `logs/app.log` confirming store selection and restore behavior.

## Cleanup & Refactor Notes
- Unified restore logic for Videos and removed duplicated controls.
- Kept interface contract consistent; adapters return identical shapes to avoid UI refactors.
- Further refactors to consider (not applied yet):
  - Extract a small `restore_service` to centralize playlist/videos restore operations.
  - Add unit tests for `JsonStore` save/load parity.
  - Normalize error handling to a helper to reduce repeated try/except blocks.