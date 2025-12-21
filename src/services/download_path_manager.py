import os
import shutil
import re
from src.config_manager import ConfigManager

class DownloadPathManager:
    """
    Manages download paths and folder organization to keep the app root clean.
    """
    
    @staticmethod
    def get_default_download_folder():
        """Returns the configured download folder or a sensible default."""
        cfg = ConfigManager.load_config()
        folder = cfg.get("default_folder")
        if folder and os.path.isdir(folder):
            return folder
        
        # Default to user's Downloads/YoutubeDownloader
        home = os.path.expanduser("~")
        default = os.path.join(home, "Downloads", "YoutubeDownloader")
        try:
            os.makedirs(default, exist_ok=True)
        except Exception:
            pass
        return default

    @staticmethod
    def get_video_target_folder(video_info, download_opts=None):
        """
        Determines the target folder for a video download.
        Ensures folders are created inside the default download directory.
        """
        base_folder = DownloadPathManager.get_default_download_folder()
        
        # Logic to determine subfolder name
        subfolder_name = "Misc"
        
        try:
            # 1. Playlist-based
            pid = video_info.get('playlistId')
            if pid:
                # We might need the title, passed in video_info ideally
                # If not, fallback to ID or "Unknown"
                # Ideally caller passes resolved playlist title in video_info or we lookup?
                # For now, let's assume we want a clean name.
                p_title = video_info.get('playlist_title') # Hypothetical field
                if not p_title and 'playlist_tree_lookup' in video_info:
                     # Caller might inject a lookup helper/value
                     p_title = video_info['playlist_tree_lookup']
                
                if p_title:
                    subfolder_name = f"Playlist - {p_title}"
                else:
                     subfolder_name = "Playlist - Unknown"
            
            # 2. Fallback / Search based
            elif download_opts and download_opts.get('fallback_videos', True):
                use_ct = download_opts.get('use_channel_title_fallback', True)
                if use_ct:
                    ct = str(video_info.get('channelTitle', '')).strip()
                    if ct:
                        subfolder_name = f"Channel - {ct}"
                    else:
                        subfolder_name = f"Videos - {download_opts.get('query', 'Misc')}"
                else:
                    subfolder_name = f"Videos - {download_opts.get('query', 'Misc')}"
            
        except Exception:
            pass

        # Sanitize folder name
        subfolder_name = re.sub(r'[<>:"/\\|?*]', '_', subfolder_name).strip()
        
        return os.path.join(base_folder, subfolder_name)

    @staticmethod
    def cleanup_app_root(app_root):
        """
        Moves clutter folders (Videos - *, Playlist - *) from app root to a 'Legacy_Downloads' folder.
        """
        legacy_dir = os.path.join(app_root, "Legacy_Downloads")
        
        moved_count = 0
        
        try:
            for item in os.listdir(app_root):
                full_path = os.path.join(app_root, item)
                if not os.path.isdir(full_path):
                    continue
                
                # Check patterns
                if item.startswith("Videos - ") or item.startswith("Playlist - "):
                    if not os.path.exists(legacy_dir):
                        os.makedirs(legacy_dir)
                    
                    target_path = os.path.join(legacy_dir, item)
                    try:
                        shutil.move(full_path, target_path)
                        moved_count += 1
                    except Exception:
                        pass
        except Exception:
            pass
        return moved_count
