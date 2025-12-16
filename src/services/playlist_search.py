def search_enriched_playlists(handler, query, max_results=None):
    pls = handler.search_playlists(query) if max_results is None else handler.search_playlists(query, max_results=max_results)
    enriched = []
    for p in (pls or []):
        try:
            vc = handler.get_details(p.get("playlistId"))
        except Exception:
            vc = "N/A"
        try:
            p["video_count"] = vc
        except Exception:
            pass
        enriched.append(p)
    return enriched

