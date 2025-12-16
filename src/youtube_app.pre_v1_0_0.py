import tkinter as tk
import os
from .config_manager import ConfigManager
from .pages.setup_page import SetupPage
from .pages.main.main_page import MainPage
from .playlist import Playlist
import yt_dlp

class YouTubeApp:
    def __init__(self, root):
        self.root = root
        self.config = ConfigManager.load_config()
        self.api_key = self.config.get("api_key", "")
        self.default_folder = self.config.get("default_folder", "")
        self.playlist_handler = None
        self._initialize_gui()

    def _initialize_gui(self):
        self.setup_window()
        self.setup_gui()

    def setup_window(self):
        try:
            ver = str(os.getenv("APP_VERSION", "1.0.0")).strip()
        except Exception:
            ver = "1.0.0"
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
            self.root.title(f"YouTube Playlist Explorer — v{ver} [{env_label}]")
        except Exception:
            self.root.title("YouTube Playlist Explorer")

