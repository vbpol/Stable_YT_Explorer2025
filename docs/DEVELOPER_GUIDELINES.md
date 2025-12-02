# Developer Guidelines

## Architecture
- Layers
  - UI: Tkinter frames under `src/pages/` managed by `src/youtube_app.py`.
  - Domain: `src/playlist.py` wrapping YouTube Data API.
  - Persistence: `src/data/` (`json_store.py`, `sqlite_store.py`, `django_store.py`).
  - Configuration: `src/config_manager.py`.
  - Runtime: launcher `src/main.py`, logging in `src/logger.py`.

## Code Organization
- Packages
  - `src/` root package; `pages` subpackage for UI; `data` subpackage for storage.
- Entry Points
  - Current runtime uses `src/main.py:main`.

## Development Workflow
- Create feature under the appropriate layer and keep UI responsive.
- Use background threads for long I/O; update UI with `after` callbacks.
- Persist last searches via `ConfigManager` to `data/`.
- Prefer dependency injection when unit testing UI widgets.

## Testing
- Unit tests live in `tests/` and use `unittest`.
- Run tests: `python -m unittest discover -s tests -p "test_*.py"`.

## Security Tagging
- Runtime security tagging applies on import to modules, classes, and functions.
- Utility: `src/security.py` with `apply_security_tag` and `is_secure`.
- Invoked at fallback runtime startup from `src/main.py:28` and `src/main.py:40`.

## Environment Variables
- `YOUTUBE_API_KEY` or `YOUTUBE_API_KEYS` (comma-separated).
- `PERSISTENCE_MODE` in `{"json","sqlite","django"}`.

## Guidelines
- Keep UI safe from exceptions; wrap external calls.
- Avoid blocking the main thread; batch UI updates.
- Store only necessary data; avoid secrets in logs.

