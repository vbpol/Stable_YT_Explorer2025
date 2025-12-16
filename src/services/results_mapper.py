def build_index_map(videos, playlists, current_map=None):
    try:
        idx_map = dict(current_map or {})
    except Exception:
        idx_map = {}
    try:
        rev = {}
        for v in (videos or []):
            pi = v.get('playlistIndex')
            pid = v.get('playlistId')
            if pid and isinstance(pi, int):
                idx_map[pid] = pi
                rev[pi] = pid
    except Exception:
        pass
    try:
        n = max([int(x) for x in list(idx_map.values()) if isinstance(x, int)] or [0])
    except Exception:
        n = 0
    try:
        for p in (playlists or []):
            pid = p.get('playlistId') or p.get('id') or p.get('playlist_id')
            if not pid:
                continue
            if pid not in idx_map:
                n += 1
                idx_map[pid] = n
    except Exception:
        pass
    return idx_map

def rebuild_video_playlist_cache(videos, index_map=None):
    cache = {}
    try:
        rev = {idx: pid for pid, idx in (index_map or {}).items()}
    except Exception:
        rev = {}
    for v in (videos or []):
        try:
            vid = v.get('videoId')
            if not vid:
                continue
            pid = v.get('playlistId')
            if not pid:
                pi = v.get('playlistIndex')
                pid = rev.get(pi)
            if pid:
                cache[vid] = pid
        except Exception:
            pass
    return cache

def link_media_index(media_index, pids_map):
    try:
        if media_index and isinstance(pids_map, dict):
            for pid, vids in pids_map.items():
                try:
                    media_index.bulk_link_playlist_videos(pid, vids or [])
                except Exception:
                    pass
    except Exception:
        pass
