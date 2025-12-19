def search_enriched_playlists(handler, query, max_results=None):
    pls = handler.search_playlists(query) if max_results is None else handler.search_playlists(query, max_results=max_results)
    if not pls:
        return []

    # Collect IDs for batch processing
    pids = [p.get("playlistId") for p in pls if p.get("playlistId")]
    
    # Batch fetch details (1 unit for up to 50 playlists)
    try:
        details_map = handler.get_playlists_details(pids)
    except Exception:
        details_map = {}

    enriched = []
    for p in pls:
        pid = p.get("playlistId")
        vc = details_map.get(pid, "N/A")
        try:
            p["video_count"] = vc
        except Exception:
            pass
        enriched.append(p)
    return enriched

