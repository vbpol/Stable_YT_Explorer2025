# App Status

## Current
- Mode-aware interactions: double-click in `Videos` mode does not navigate; single-click pins+prints+highlights
- Intersection-only marking across Videos table, popup, and terminal listing
- Right-click menu: Popup, Print dataset, Populate Videos table (preview)
- Videos list right-click: Download Selected; uses options dialog + progress window
- Preview rendering in Videos mode with Back restore
- Cached playlist video IDs for fast mapping; cache-first playlist pages
- Persistence: `playlistPages` and `playlistIds` saved and restored from last videos search JSON

## Remaining Issues
- Deep playlists may need additional pages fetched for exhaustive mapping
- Intersection depends on current keyword; changing query changes markings as expected
- Launcher may receive KeyboardInterrupt if externally stopped
- Download may be bandwidth limited; consider fragment concurrency tuning

## Next Steps
- Consider bounded multi-page prefetch for selected playlists (first 2–3 pages)
- Add more UI telemetry for interactions and highlight counts
- Optional: toggle to mark by playlist membership only (ignoring keyword)
- Add bulk selection helpers for Videos list and queued downloads
