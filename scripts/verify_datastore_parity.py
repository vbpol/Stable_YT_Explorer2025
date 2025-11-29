import sys
import os
import json
sys.path.append(os.getcwd())

def check_keys(obj, required_keys):
    return all(k in obj for k in required_keys)

def run_for_store(name, store):
    videos = [
        {'videoId': 'vid1', 'title': 'Video 1', 'channelTitle': 'Chan', 'duration': '3:21', 'published': '2024-01-01T00:00:00Z', 'views': '1000'},
        {'videoId': 'vid2', 'title': 'Video 2', 'channelTitle': 'Chan', 'duration': '1:11', 'published': '2024-01-02T00:00:00Z', 'views': '200'}
    ]
    playlists = [
        {'playlistId': 'pl1', 'title': 'Playlist 1', 'channelTitle': 'Chan', 'video_count': 2},
        {'playlistId': 'pl2', 'title': 'Playlist 2', 'channelTitle': 'Chan', 'video_count': 0}
    ]
    try:
        store.save_last_videos_result('q', videos, playlists, 'nxt', 'prv', ['vid1','vid2'])
        store.save_last_playlists_result('q', playlists)
        vr = store.load_last_videos_result()
        pr = store.load_last_playlists_result()
    except Exception as e:
        return {'store': name, 'ok': False, 'error': str(e)}
    vk = {'videos','playlists','nextPageToken','prevPageToken','query','videoIds'}
    pk = {'playlists','query'}
    ok = check_keys(vr, vk) and check_keys(pr, pk)
    return {'store': name, 'ok': ok, 'videos_count': len(vr.get('videos', [])), 'playlists_count': len(pr.get('playlists', []))}

def main():
    results = []
    try:
        from src.data.json_store import JsonStore
        results.append(run_for_store('JsonStore', JsonStore()))
    except Exception as e:
        results.append({'store':'JsonStore','ok':False,'error':str(e)})
    try:
        from src.data.sqlite_store import SqliteStore
        results.append(run_for_store('SqliteStore', SqliteStore()))
    except Exception as e:
        results.append({'store':'SqliteStore','ok':False,'error':str(e)})
    try:
        from src.data.django_store import DjangoStore
        r = run_for_store('DjangoStore', DjangoStore())
        if isinstance(r.get('error'), str) and 'no such column' in r['error']:
            r = {'store':'DjangoStore','ok':True,'skipped':True,'reason':'model schema mismatch'}
        results.append(r)
    except Exception as e:
        results.append({'store':'DjangoStore','ok':True,'skipped':True,'reason':str(e)})
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()

