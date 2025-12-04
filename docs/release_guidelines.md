# Release Guidelines — Stable Version Workflow

## Branching & Tags
- Main branches: `main` (stable), `develop` (integration).
- Feature branches: `feature/<short-scope>` off `develop`.
- Release branch: `release/vX.Y.Z` cut from `develop`.
- Tags: `vX.Y.Z` on `main` after successful release.

## Checklists
### PR Checklist
- Interface shapes unchanged and documented
- Toggle wired and default behavior preserved
- Restore functions reused (no duplicates)
- Logs for store selection and restore calls
- Manual verification steps completed
- Docs updated with code references

### Pre-Release Checklist
- Manual verification:
  - Startup loads last-mode and last results (`src/main.py:65-77`).
  - Videos search saves playlists and shows progress; popup closes at 100% (`src/pages/main/main_page.py:341-353`, `346-364`, `373-386`).
  - Back to Results loads playlists before videos (`src/pages/main/main_page.py:482-496`).
  - Playlist No restarts from 1 on new search (`src/pages/main/main_page.py:144-151`).
  - Playlists mode saves/loads query and results (`src/pages/main/main_page.py:110-133`, `167-174`).
- Sanity checks:
  - Confirm persistence mode selection resolves to the intended store (`src/data/factory.py:1-32`).
  - Ensure `.env` or `config.json` provided for API keys and folder.

## Commands
- Prepare release branch:
  - `git checkout -b release/vX.Y.Z develop`
  - Update `docs/change_log.md` and `README.md` as needed
- Verify:
- `python scripts/pre_release_check.py`
  - `python -m unittest -v`
- Verify UI flows:
    - Videos search → playlist open (cache-first)
    - Concurrent opens are queued with status messages
    - Highlight scanning shows progress and resets
    - Network errors fall back to highlighting without dialogs
    - Download Progress window shows speed/ETA, indeterminate bar on unknown sizes
    - Open Folder button is enabled only when files exist
    - Folder is auto-created before downloads start
    - Status shows "Completed with issues" when nothing was saved
- Finalize:
  - `git checkout main`
  - `git merge --no-ff release/vX.Y.Z`
  - `git tag vX.Y.Z`
  - `git checkout develop && git merge --no-ff main`

## Rollback
- If issues arise post-tag:
  - `git revert <bad-commit>` on `main` or
  - `git checkout vX.Y.Z-stable` and hotfix
- App-level toggle:
  - Switch persistence to JSON in menu or set `persistence=json` in `config.json`

## Notes
- Do not commit `src/data/app.sqlite3`, `data/*.json`, or logs — see `.gitignore`.
- Build steps are project-specific; validate binaries separately if applicable.
- Django integration is optional; keep JSON/SQLite as defaults until ORM parity passes.
 - Video downloads (yt-dlp) quality mappings:
   - Best: `bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best`
   - 720p: `bestvideo[ext=mp4][height>=720]+bestaudio[ext=m4a]/best[ext=mp4]/best`
   - These constraints ensure audio is present and merged cleanly to MP4 when ffmpeg is available; otherwise single MP4 streams are chosen.
 - ffmpeg recommended and should be available on `PATH` for HD merges.

