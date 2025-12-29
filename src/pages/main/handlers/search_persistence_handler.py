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
            
            # Map caches
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

    def load_and_restore_search(self, mode_display):
        """
        Loads the last search results and restores the UI state.
        This consolidates logic from MainPage._load_last_search.
        """
        mp = self.main_page
        mode = (mode_display or '').strip().lower()
        if mode not in ('playlists', 'videos'):
            mode = 'playlists'
            
        try:
            if mode == 'playlists':
                self._restore_playlists_mode()
            else:
                self._restore_videos_mode()
        except Exception as e:
            print(f"[SearchPersistenceHandler] Error in load_and_restore_search: {e}")

    def _restore_playlists_mode(self):
        mp = self.main_page
        path = ConfigManager.get_last_search_path('playlists')
        raw = ConfigManager.load_json(path)
        data_list = []
        q = ''
        try:
            if isinstance(raw, dict):
                data_list = raw.get('playlists', [])
                q = raw.get('query', '')
            else:
                data_list = raw or []
        except Exception:
            data_list = raw or []
            
        try:
            mp.search.search_entry.delete(0, 'end')
            if q:
                mp.search.search_entry.insert(0, q)
        except Exception: pass
        
        for pl in data_list:
            mp.playlist.update_playlist(pl)
            
        try:
            mp.video.update_back_button_state(False)
        except Exception: pass

    def _restore_videos_mode(self):
        mp = self.main_page
        try:
            mp.video._panel.pagination.set_visible(False)
        except Exception: pass
        
        path = ConfigManager.get_last_search_path('videos')
        data = ConfigManager.load_json(path) or {}
        videos = data.get('videos', [])
        playlists = data.get('playlists', [])
        q = data.get('query', '')
        
        try:
            mp.video_prev_page_token = data.get('prevPageToken')
            mp.video_next_page_token = data.get('nextPageToken')
        except Exception: pass
        
        try:
            ids = data.get('videoIds') or []
            v_ids = set([i for i in ids if i])
            mp.video_search_ids = v_ids
            mp.video_results_ids = v_ids  # Sync results IDs for intersection logic
        except Exception:
            mp.video_search_ids = set()
            mp.video_results_ids = set()
            
        try:
            mp.search.search_entry.delete(0, 'end')
            if q:
                mp.search.search_entry.insert(0, q)
            mp.video_search_query = q or mp.video_search_query
        except Exception: pass
        
        # Restore Media Index contexts
        try:
            self.load_media_index_snapshot()
        except Exception: pass

        # Restore caches if present
        try:
            if 'playlistPages' in data:
                mp.playlist_videos_cache.update(data['playlistPages'])
            if 'playlistIds' in data:
                for pid, vids in data['playlistIds'].items():
                    mp.playlist_video_ids[pid] = set(vids)
        except Exception: pass

        # CRITICAL: Rebuild playlist_index_map from saved video data BEFORE rendering
        try:
            for v in videos:
                pi = v.get('playlistIndex')
                pid = v.get('playlistId')
                if pi and pid and pid not in mp.playlist_index_map:
                    mp.playlist_index_map[pid] = pi
        except Exception: pass
        
        # RECOVERY: Update playlist table and map videos to restore intersection marks (bullets)
        mp.collected_playlists = playlists
        for pl in playlists:
            mp.playlist.update_playlist(pl)
            
        # Call mapping to restore "Intersecting: X" counts in playlist table
        try:
            mp.playlist_ui_handler.map_videos_to_playlists(videos, skip_render=True)
        except Exception: pass
        
        # RECOVERY: Use VideoUIHandler to render videos to ensure stars/tags/indices are applied
        mp.current_videos = videos
        mp.video_ui_handler.render_videos(videos, mp.video_search_ids, q)
        
        try:
            mp._preview_active = False
            mp.video.update_back_button_state(False)
            mp.video.set_pagination_visible(False)
            mp.video.prev_page_btn.configure(command=lambda: mp.action_handler.show_videos_search_page(mp.video_prev_page_token))
            mp.video.next_page_btn.configure(command=lambda: mp.action_handler.show_videos_search_page(mp.video_next_page_token))
            mp.video.prev_page_btn["state"] = "normal" if mp.video_prev_page_token else "disabled"
            mp.video.next_page_btn["state"] = "normal" if mp.video_next_page_token else "disabled"
        except Exception: pass

    def load_last_search_from_config(self, kind='videos'):
        """Loads last search from config for a given kind."""
        try:
            path = ConfigManager.get_last_search_path(kind)
            return ConfigManager.load_json(path)
        except Exception as e:
            print(f"[SearchPersistenceHandler] Error loading last search from config: {e}")
            return None

    def save_media_index_snapshot(self):
        """Saves a snapshot of the media index with thread safety."""
        mp = self.main_page
        try:
            if not mp.media_index:
                return
            vids = {}
            pls = {}
            
            # Use the MediaIndex lock to iterate safely
            with mp.media_index._lock:
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
                except Exception as e:
                    logger.error(f"Error snapshotting videos: {e}")
                
                try:
                    for pid, pm in (mp.media_index.playlists or {}).items():
                        pls[pid] = {
                            'playlistId': pm.playlistId,
                            'title': pm.title,
                            'channelTitle': pm.channelTitle,
                            'video_count': pm.video_count,
                            'video_ids': list(pm.video_ids or set()),
                        }
                except Exception as e:
                    logger.error(f"Error snapshotting playlists: {e}")
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
