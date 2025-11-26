import tkinter as tk
from tkinter import ttk
from .config_manager import ConfigManager
from .pages.setup_page import SetupPage
from .pages.main.main_page import MainPage
from .playlist import Playlist
from .data.factory import get_datastore
from .logger import get_logger
import yt_dlp  # Import yt-dlp for downloading videos

class YouTubeApp:
    def __init__(self, root):
        self.root = root
        self.log = get_logger('app')
        self.config = ConfigManager.load_config()
        self.api_key = self.config.get("api_key", "")
        self.default_folder = self.config.get("default_folder", "")
        self.playlist_handler = Playlist(self.api_key)
        self._initialize_gui()

    def _initialize_gui(self):
        """Initialize the GUI components and window properties."""
        self.setup_window()
        self.setup_gui()
        try:
            self.datastore = get_datastore()
            try:
                self.log.info(f"datastore={type(self.datastore).__name__}")
            except Exception:
                pass
        except Exception:
            self.datastore = None

    def setup_window(self):
        """Configure the main window properties."""
        self.root.title("YouTube Playlist Explorer")
        self.root.geometry("900x600")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.after(800, lambda: self.root.attributes('-topmost', False))
            self.root.focus_force()
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
        else:
            self.show_frame(SetupPage)

    def show_frame(self, page_class):
        """Show the selected frame."""
        frame = self.frames[page_class]
        frame.tkraise()

    def update_config(self, api_key, default_folder):
        """Update application configuration."""
        self.api_key = api_key
        self.default_folder = default_folder
        ConfigManager.save_config(api_key, default_folder)
        self.playlist_handler = Playlist(api_key)

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

        self.progress_bar = ttk.Progressbar(self.progress_window, orient="horizontal", length=280, mode="determinate")
        self.progress_bar.pack(pady=20)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([video_url])
            except Exception as e:
                print(f"Error downloading video: {e}")
            finally:
                self.progress_window.destroy()  # Close the progress window after download

    def progress_hook(self, d):
        status = d.get('status')
        if status == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                percent = downloaded / total * 100
                if percent < 0:
                    percent = 0
                elif percent > 100:
                    percent = 100
                self.progress_bar['value'] = percent
                self.progress_window.update_idletasks()