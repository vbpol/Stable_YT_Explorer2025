# Feature Dependencies

## Summary Table
| Feature | Layer | Primary Components | External Libs |
|---|---|---|---|
| Playlists search | Domain/UI | `Playlist.search_playlists` (`src/playlist.py:10`), `MainPage.execute_search` (`src/pages/main/main_page.py:311`) | `google-api-python-client` |
| Playlist details | Domain/UI | `Playlist.get_details` (`src/playlist.py:31`), `MainPage.execute_search` enrich step | `google-api-python-client` |
| Videos search | Domain/UI | `Playlist.search_videos` (`src/playlist.py:59`), `MainPage.execute_search` videos branch | `google-api-python-client`, `isodate` |
| Playlist videos | Domain/UI | `Playlist.get_videos` (`src/playlist.py:90`), `MainPage.show_playlist_videos` (`src/pages/main/main_page.py:899`) | `google-api-python-client`, `isodate` |
| Data persistence | Persistence | `JsonStore` (`src/data/json_store.py:7`), `ConfigManager` (`src/config_manager.py:12`) | `json` |
| HD download | UI | `YouTubeApp.download_video` (`src/youtube_app.py:75`) | `yt-dlp`, `ffmpeg` |
| Security tagging | Runtime | `security.apply_security_tag` (`src/security.py:11`), invocation in `src/main.py:15` | None |

## Component Dependencies
| Component | Depends On | Purpose |
|---|---|---|
| `MainPage` (`src/pages/main/main_page.py:23`) | `SearchSection`, `PlaylistSection`, `VideoSection`, `StatusBar`, `Playlist` | UI orchestration, state and caching |
| `YouTubeApp` (`src/youtube_app.py:8`) | `ConfigManager`, `Playlist`, Tkinter | App init, page routing |
| `Playlist` (`src/playlist.py:6`) | Google API Client, `isodate`, `datetime` | API calls, durations, details |
| `ConfigManager` (`src/config_manager.py:12`) | `dotenv`, `settings.py`, filesystem | API keys, last search, mode |
| `JsonStore` (`src/data/json_store.py:7`) | `ConfigManager` | Persist last search results |

## Testing and Usage
- Unit tests: `tests/test_back_to_video_results.py:39`, `tests/test_security_tag.py:1`.
- Run: `python -m unittest discover -s tests -p "test_*.py"`.
- Typical integration:
  - UI calls domain methods; responses are rendered and persisted.
  - Security tags propagate across modules/classes/functions at import.

