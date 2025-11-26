# Upgrade-Without-Regressions System Prompt & Dev Workflow

## System Prompt (Use for feature updates and migrations)

- Preserve existing behavior unless the change explicitly requires it.
- Maintain a single interface contract for data access (`DataStore`) with identical shapes across implementations.
- Stage changes behind a switch (config or menu). Keep the legacy path available until full parity is verified.
- Reuse existing restore functions (do not duplicate UI logic). Videos radio toggle must call the same function as Back to Results.
- Log key events: store selection, searches, saves/loads, tokens, item counts, query, restore calls.
- On any network or external error, show the last saved results via the datastore rather than leaving the view empty.
- Do not remove legacy files or paths until new behavior passes parity checks and is documented.
- Tests and manual checks are mandatory: startup restore, radio toggles, Back to Results, pagination state, highlights, search input.
- Document changes: architecture, file structure, coding updates, and new features with code references.
- Provide an immediate rollback plan (toggle setting, or fallback to legacy store) and record it in logs/docs.

## Dev Workflow

- Baseline & Branching
  - Tag the current stable state (e.g., `vX.Y.Z-stable`) and create a feature branch.
  - Snapshot last-results files if applicable.

- Design & Contracts
  - Define exact data shapes to return from the datastore.
  - List integration points that consume the datastore (restore functions, searches, pagination).

- Implementation
  - Add a new store behind `DataStore` without changing UI logic.
  - Introduce a config/menu toggle to switch stores.
  - Implement graceful fallback to last results on external errors.

- Verification
  - Logs: verify store selection and restore paths.
  - Manual checklist: startup restore, radio toggles, Back to Results, pagination, highlights, search input content.
  - Optional tests: unit and smoke scripts for save/load parity.

- Documentation
  - Update README and phase reports to include logging, store selection, and restore behavior.
  - Add change log entries with file paths and line references.

- Rollback
  - Flip the toggle back to legacy store or remove new store selection.
  - Confirm logs show the reverted store and restore functions behave identically.

## Templates

- PR Checklist
  - Interface shapes unchanged and documented
  - Toggle wired and default behavior preserved
  - Restore functions reused (no duplicates)
  - Logs added for store selection and restore calls
  - Manual verification steps completed
  - Docs updated with code references

- Commit Message
  - Scope: feature/migration
  - Summary: what changed and why
  - Behavior: how legacy behavior is preserved
  - Verification: logs/tests run and outcomes

- Test Checklist
  - Startup restore (Playlists)
  - Videos restore via Back to Results
  - Radio toggle restore (Videos)
  - Pagination tokens states correct
  - Highlights remain
  - Search box query restored

- Migration Plan
  - New store adapter ready and returns identical shapes
  - Toggle added and defaults to legacy behavior
  - Fallback shows last results on errors
  - Documentation and change log updated