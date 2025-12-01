# Validation Checklist

## Interaction
- Double-click in `Videos` mode does not navigate; pins, prints, highlights
- Single-click in `Videos` mode pins + prints + highlights; no UI restart
- Right-click shows context menu: Popup, Print, Populate (preview)
- During playlist preview, Playlists table selection is disabled and clicks show reminder popup

## Marking Logic
- Stars mark only intersection of selected playlist videos and current search results
- Popup marks only intersection; non-matching titles have no star
- Terminal listing includes star prefix only for intersection items

## Persistence
- `playlistPages` and `playlistIds` saved in last videos search JSON
- Restore loads pages and ID sets for fast mapping and highlight

## Performance
- Mapping uses cached ID sets; avoids per-video network membership checks
- Preview uses cached first page when available; otherwise minimal fetch

## UI Stability
- No UI restart on playlist interactions in `Videos` mode
- Back button restores search results after preview
- Double-click and single-click event handlers return "break" where needed

## Downloads
- Playlist download opens options dialog and progress window
- Right-click on Videos list shows "Download Selected" and downloads chosen items
- Progress bars update for total and current video; cancel works

## Data Consistency
- Playlist 'Videos' column auto-fills when 'N/A' via async `get_details`

## Error Handling
- Timeout/SSL retry in terminal printing; fallback to highlight when fetch fails
- Missing playlist row is inserted before open

- Videos mode search loads and preserves results
- Double-click first playlist uses cache and prints to terminal
- Double-click while busy queues and runs next open
- Status bar shows progress during highlight scanning
- Network errors fall back to highlighting; no error dialog
- Playlist numbers populate via `assign_playlist_index`
- Video numbering appears in titles consistently
