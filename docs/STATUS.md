# App Status

## Current
- Videos mode restores last query (logged) and loads videos/playlists immediately.
- Playlists in Videos mode populated from caches/store and refined by background mapping.
- Numbering is contiguous in Videos table and mirrored in Playlists table.
- Tooltip on videos shows playlist ID/title.
- Robust logging added to show_playlist_videos and dataset build.
- SSL/cipher errors handled without crashing; datastore/search fallbacks used.

## Remaining Issues
- Last keyword restore in some scenarios still intermittent; verify both modes after cold start.
- Occasional KeyboardInterrupt when showing message dialogs; continue hardening to avoid blocking UI.
- Speed: add limited parallel membership checks and TTL cache for reuse.
- Ensure playlists seeding always includes titles/channels (lazy fetch if missing).
- Add status bar summary on mode switch and mapping completion across all flows.

## Next Steps
- Implement parallel checks (small thread pool) with UI-safe updates.
- Persist membership cache with TTL in datastore.
- Add more logs for keyword restoration and seeding decisions.
