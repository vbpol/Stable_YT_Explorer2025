try:
    from src.config_manager import ConfigManager
    from src.data.json_store import JsonStore
except ModuleNotFoundError:
    from config_manager import ConfigManager
    from data.json_store import JsonStore

class SearchPersistenceHandler:
    def __init__(self, main_page):
        self.main_page = main_page

    def persist_last_videos_result(self):
        """Saves current video search results to disk unless in preview mode."""
        mp = self.main_page
        try:
            if getattr(mp, '_preview_active', False):
                return
            
            vids = list(mp.current_videos or [])
            pls = list(mp.collected_playlists or [])
            nxt = getattr(mp, 'video_next_page_token', None)
            prv = getattr(mp, 'video_prev_page_token', None)
            v_ids = list(getattr(mp, 'video_search_ids', set()) or [])
            
            pages = {
                pid: {'pages': cache.get('pages', {}), 'tokens': cache.get('tokens', {})} 
                for pid, cache in (mp.playlist_videos_cache or {}).items()
            }
            pids_map = {
                pid: list(mp.playlist_video_ids.get(pid, set())) 
                for pid in (mp.playlist_video_ids or {}).keys()
            }
            
            ConfigManager.save_json(ConfigManager.get_last_search_path('videos'), {
                'query': getattr(mp, 'video_search_query', ''),
                'videos': vids,
                'playlists': pls,
                'nextPageToken': nxt,
                'prevPageToken': prv,
                'videoIds': v_ids,
                'playlistPages': pages,
                'playlistIds': pids_map
            })
        except Exception as e:
            print(f"[SearchPersistenceHandler] Error persisting results: {e}")

    def save_media_index_snapshot(self):
        """Saves a snapshot of the media index."""
        mp = self.main_page
        try:
            if not mp.media_index:
                return
            vids = {}
            pls = {}
            try:
                for vid, vm in (mp.media_index.videos or {}).items():
                    vids[vid] = {
                        'videoId': vm.videoId,
                        'title': vm.title,
                        'channelTitle': vm.channelTitle,
                        'channelId': vm.channelId,
                        'duration': vm.duration,
                        'published': vm.published,
                        'views': vm.views,
                        'playlistId': vm.playlistId,
                        'playlistIndex': vm.playlistIndex,
                    }
            except Exception:
                pass
            try:
                for pid, pm in (mp.media_index.playlists or {}).items():
                    pls[pid] = {
                        'playlistId': pm.playlistId,
                        'title': pm.title,
                        'channelTitle': pm.channelTitle,
                        'video_count': pm.video_count,
                        'video_ids': list(pm.video_ids or set()),
                    }
            except Exception:
                pass
            JsonStore().save_media_index_snapshot(vids, pls)
        except Exception as e:
            print(f"[SearchPersistenceHandler] Error saving media index: {e}")

    def load_media_index_snapshot(self):
        """Loads the media index from disk."""
        mp = self.main_page
        try:
            snap = JsonStore().load_media_index_snapshot() or {}
            vids = snap.get('videos') or {}
            pls = snap.get('playlists') or {}
            
            if not mp.media_index:
                try:
                    from src.services.media_index import MediaIndex
                except ModuleNotFoundError:
                    from services.media_index import MediaIndex
                mp.media_index = MediaIndex()
                
            try:
                mp.media_index.add_playlists(list(pls.values()))
            except Exception:
                pass
            try:
                mp.media_index.add_videos(list(vids.values()))
            except Exception:
                pass
            for pid, pinfo in pls.items():
                try:
                    for vid in list(pinfo.get('video_ids') or []):
                        mp.media_index.link_video_to_playlist(pid, vid)
                except Exception:
                    pass
        except Exception as e:
            print(f"[SearchPersistenceHandler] Error loading media index: {e}")
