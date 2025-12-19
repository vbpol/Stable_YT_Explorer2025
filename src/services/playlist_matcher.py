from typing import Set, Dict, Optional, Callable, Any

class PlaylistMatcher:
    """
    Service to handle logic for finding intersection between a playlist
    and the current video search results.
    """
    def __init__(self):
        self._hits_cache: Dict[str, Set[str]] = {}

    def invalidate_cache(self):
        self._hits_cache.clear()

    def get_intersection(
        self,
        playlist_id: str,
        current_video_ids: Set[str],
        media_index: Optional[Any], # Type: MediaIndex
        known_playlist_video_ids: Optional[Dict[str, Set[str]]],
        fetch_fallback: Optional[Callable[[str, str], bool]] = None,
        current_videos_list: Optional[list] = None
    ) -> Set[str]:
        """
        Calculate intersection between playlist videos and current search results.
        
        Args:
            playlist_id: The ID of the playlist to check.
            current_video_ids: Set of video IDs currently shown in search results.
            media_index: The MediaIndex instance (optional).
            known_playlist_video_ids: Dictionary mapping playlist_id to set of video_ids (legacy/backup).
            fetch_fallback: Callable(playlist_id, video_id) -> bool. used to check API/remote if local data missing.
            current_videos_list: List of video dicts (needed for fallback optimization to limit checks).
        
        Returns:
            Set of video IDs that are in both the playlist and the current results.
        """
        if not playlist_id:
            return set()

        # 1. Check cache first
        if playlist_id in self._hits_cache:
            return self._hits_cache[playlist_id]

        # 2. Gather known IDs from MediaIndex or legacy dict
        known_ids = set()
        if media_index:
            known_ids = set(media_index.get_playlist_video_ids(playlist_id) or set())
        
        # Merge with legacy dict if provided (for safety/migration)
        if known_playlist_video_ids:
            legacy_ids = known_playlist_video_ids.get(playlist_id)
            if legacy_ids:
                known_ids.update(legacy_ids)

        # 3. Calculate intersection
        hits = current_video_ids.intersection(known_ids)

        # 4. Fallback: If no hits found locally, try fetching for a subset of current videos
        # This addresses the case where we haven't fully loaded the playlist content yet
        if not hits and fetch_fallback and current_videos_list:
            # Optimization: If MediaIndex has all videos for this playlist, skip fallback
            if media_index:
                try:
                    pl = media_index.get_playlist(playlist_id)
                    if pl:
                        vc = pl.video_count
                        if vc != 'N/A':
                            try:
                                if len(pl.video_ids) >= int(vc):
                                    # We have full content, so intersection is complete
                                    self._hits_cache[playlist_id] = hits
                                    return hits
                            except Exception:
                                pass
                except Exception:
                    pass

            # Limit checks to avoid huge API usage
            limit = min(30, len(current_videos_list))
            temp_hits = set()
            
            for i in range(limit):
                try:
                    v = current_videos_list[i]
                    vid = v.get('videoId')
                    if not vid:
                        continue
                    
                    # Avoid redundant API calls if we already know it's not there?
                    # actually fetch_fallback is authoritative.
                    # But we should check if we already checked this VID for this PL? 
                    # For now, relying on the fact that if it was in known_ids, it would be a hit.
                    # So we are checking "unknown" status.
                    
                    if vid not in known_ids:
                        if fetch_fallback(playlist_id, vid):
                            temp_hits.add(vid)
                            # Update known_ids so next time it's fast? 
                            # The caller should probably handle updating the index, 
                            # but we can at least return it in hits.
                except Exception:
                    pass
            
            if temp_hits:
                hits = temp_hits

        # 5. Cache result
        self._hits_cache[playlist_id] = hits
        return hits
