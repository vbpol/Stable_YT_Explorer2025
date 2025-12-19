import tkinter as tk
import os
from .config_manager import ConfigManager
from .pages.setup_page import SetupPage
from .pages.main.main_page import MainPage
from .playlist import Playlist
import yt_dlp  # Import yt-dlp for downloading videos

class YouTubeApp:
    def __init__(self, root):
        self.root = root
        self.config = ConfigManager.load_config()
        self.api_key = self.config.get("api_key", "")
        self.default_folder = self.config.get("default_folder", "")
        self.playlist_handler = None
        self._initialize_gui()

    def _initialize_gui(self):
        """Initialize the GUI components and window properties."""
        self.setup_window()
        self.setup_gui()

    def setup_window(self):
        """Configure the main window properties."""
        try:
            ver = str(os.getenv("APP_VERSION", "3.0.0.0")).strip()
        except Exception:
            ver = "3.0.0.0"
        try:
            env = str(os.getenv("APP_ENV", "development")).strip().lower()
        except Exception:
            env = "development"
        try:
            env_label = {
                "production": "PROD",
                "prod": "PROD",
                "release": "PROD",
                "stable": "STABLE",
                "development": "DEV",
                "dev": "DEV"
            }.get(env, env.upper() or "DEV")
        except Exception:
            env_label = "DEV"
        try:
            self.root.title(f"YouTube Playlist Explorer (AntiGravity) — v{ver} [{env_label}]")
        except Exception:
            self.root.title("YouTube Playlist Explorer (AntiGravity)")
        try:
            from .config_manager import ConfigManager
            ui_cfg = ConfigManager.load_config().get('ui', {})
            size = str(ui_cfg.get('window_size', '1100x720'))
        except Exception:
            size = '1100x720'
        self.root.geometry(size)
        try:
            w, h = size.split('x')
            self.root.minsize(int(w), int(h))
        except Exception:
            try:
                self.root.minsize(1100, 720)
            except Exception:
                pass
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.after(600, lambda: self.root.attributes("-topmost", False))
        except Exception:
            pass

    def setup_gui(self):
        """Set up the GUI with multipages."""
        self.frames = {}
        self._create_frames()
        self._show_initial_frame()

    def _create_frames(self):
        """Create and initialize all application frames."""
        for F in (SetupPage, MainPage):
            frame = F(self.root, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

    def _show_initial_frame(self):
        """Show the appropriate initial frame based on configuration."""
        if self.api_key and self.default_folder:
            self.show_frame(MainPage)
            try:
                mp = self.frames[MainPage]
                try:
                    from .config_manager import ConfigManager
                    m = (ConfigManager.load_last_mode() or '').strip().lower()
                except Exception:
                    m = ''
                if m not in ('videos', 'playlists'):
                    m = 'videos'
                mp.set_search_mode('Videos' if m == 'videos' else 'Playlists')
            except Exception:
                pass
        else:
            self.show_frame(SetupPage)

    def show_frame(self, page_class):
        """Show the selected frame."""
        if page_class is MainPage:
            self.ensure_playlist_handler()
            if not self.api_key or not self.default_folder or self.playlist_handler is None:
                page_class = SetupPage
        frame = self.frames[page_class]
        frame.tkraise()

    def update_config(self, api_key, default_folder):
        """Update application configuration."""
        self.api_key = api_key
        self.default_folder = default_folder
        ConfigManager.save_config(api_key, default_folder)
        self.playlist_handler = None
        self.ensure_playlist_handler()

    def ensure_playlist_handler(self):
        """Lazily initialize the Playlist handler to avoid startup lag."""
        try:
            if self.playlist_handler is None and self.api_key:
                self.playlist_handler = Playlist(self.api_key)
        except Exception:
            self.playlist_handler = None

    def get_current_config(self):
        """Get current configuration values."""
        return {
            "api_key": self.api_key,
            "default_folder": self.default_folder
        }

    def download_video(self, video_url):
        """Download the specified video in HD format with a progress bar and post-processing."""
        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best',  # Prioritize 1080p, fallback to lower resolutions
            'outtmpl': f"{self.default_folder}/%(title)s.%(ext)s",  # Save to the default folder
            'progress_hooks': [self.progress_hook],  # Add progress hook
            'postprocessors': [{  # Post-processing options
                'key': 'FFmpegVideoConvertor',  # Use FFmpeg for video conversion
                'preferedformat': 'mp4',  # Convert to MP4 format
            }],
            'postprocessor_args': [
                '-crf', '23',  # Set the Constant Rate Factor for quality (lower is better)
                '-preset', 'medium',  # Set the encoding speed/quality trade-off
            ],
        }

        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title("Downloading Video")
        self.progress_window.geometry("300x100")

        self.progress_bar = tk.ttk.Progressbar(self.progress_window, orient="horizontal", length=280, mode="determinate")
        self.progress_bar.pack(pady=20)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([video_url])
            except Exception as e:
                print(f"Error downloading video: {e}")
            finally:
                self.progress_window.destroy()  # Close the progress window after download

    def progress_hook(self, d):
        """Hook to update the progress bar."""
        if d['status'] == 'downloading':
            self.progress_bar['value'] = d['downloaded_bytes'] / d['total_bytes'] * 100
            self.progress_window.update_idletasks()  # Update the GUI
