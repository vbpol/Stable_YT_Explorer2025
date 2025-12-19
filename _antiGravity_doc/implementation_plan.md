# Goal Description
Review the codebase to identify and fix incoherences, missing input validations, inconsistent error handling, and dead code. Ensure all features are properly validated and secure.

## Proposed Changes
---
### Config Management
#### [MODIFY] [config_manager.py](file:///d:/Py_2025/12-2025/youtube_downloaderV2_CURSOR_OK1_dev_multi_OK07-04-25/src/config_manager.py)
- Add proper validation for `api_key` and `default_folder` inputs.
- Raise descriptive exceptions instead of silently passing.
- Ensure `save_config` writes the provided `api_key` correctly (currently overwrites with empty string).
- Refactor to use a single point for loading JSON with error handling.

---
### Security Module
#### [MODIFY] [security.py](file:///d:/Py_2025/12-2025/youtube_downloaderV2_CURSOR_OK1_dev_multi_OK07-04-25/src/security.py)
- Ensure `apply_security_tag` validates module paths and raises if module cannot be imported.
- Add docstrings and type hints.
- Remove dead code paths.

---
### Playlist Handling
#### [MODIFY] [playlist.py](file:///d:/Py_2025/12-2025/youtube_downloaderV2_CURSOR_OK1_dev_multi_OK07-04-25/src/playlist.py)
- Validate playlist IDs and video IDs before processing.
- Consistent error handling with custom `PlaylistError`.

---
### UI Pages
#### [MODIFY] [main_page.py](file:///d:/Py_2025/12-2025/youtube_downloaderV2_CURSOR_OK1_dev_multi_OK07-04-25/src/pages/main/main_page.py)
- Add input validation for user‑provided search queries.
- Ensure UI callbacks handle exceptions and display user‑friendly messages.

---
### Tests
#### [ADD] [test_config_validation.py](file:///d:/Py_2025/12-2025/youtube_downloaderV2_CURSOR_OK1_dev_multi_OK07-04-25/tests/test_config_validation.py)
- New unit tests covering `ConfigManager.load_config`, `save_config`, and validation edge cases.

---
## Verification Plan
### Automated Tests
- Run existing test suite: `pytest -q` (covers security tags, back‑to‑results, etc.).
- Run new `test_config_validation.py` to ensure config validation works.
- Ensure coverage > 85% for modified modules.

### Manual Verification
- Start the application (`python run.py`) and attempt to load a malformed `.env` file; verify error messages appear.
- Use the UI to trigger a search with an empty query; confirm graceful handling.
- Verify that after fixing `save_config`, the API key persists across restarts.
