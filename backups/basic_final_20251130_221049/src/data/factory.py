def get_datastore():
    try:
        try:
            from src.config_manager import ConfigManager
        except ModuleNotFoundError:
            from config_manager import ConfigManager
        mode = ConfigManager.get_persistence_mode()
        if mode == 'json':
            from .json_store import JsonStore
            return JsonStore()
        if mode == 'django':
            from .django_store import DjangoStore
            return DjangoStore()
        if mode == 'sqlite':
            from .sqlite_store import SqliteStore
            return SqliteStore()
    except Exception:
        pass
    try:
        try:
            from src.config_manager import ConfigManager
        except ModuleNotFoundError:
            from config_manager import ConfigManager
        vp = ConfigManager.get_last_search_path('videos')
        pp = ConfigManager.get_last_search_path('playlists')
        import os
        if os.path.exists(vp) or os.path.exists(pp):
            from .json_store import JsonStore
            return JsonStore()
    except Exception:
        pass
    try:
        import django  # noqa: F401
        from .django_store import DjangoStore
        return DjangoStore()
    except Exception:
        from .sqlite_store import SqliteStore
        return SqliteStore()
