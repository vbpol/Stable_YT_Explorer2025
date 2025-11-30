import tkinter as tk
from tkinter import ttk
import threading
import yt_dlp
import os

class DownloadManager:
    def __init__(self, parent, videos, download_folder, options):
        self.parent = parent
        self.videos = videos
        self.download_folder = download_folder
        self.options = options
        self.setup_progress_window()

    def setup_progress_window(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("Download Progress")
        self.window.geometry("400x300")
        
        # Overall progress
        ttk.Label(self.window, text="Overall Progress:").pack(pady=5)
        self.total_progress = ttk.Progressbar(self.window, length=300, mode='determinate')
        self.total_progress.pack(pady=5)
        
        # Current video progress
        ttk.Label(self.window, text="Current Video:").pack(pady=5)
        self.current_label = ttk.Label(self.window, text="")
        self.current_label.pack()
        self.video_progress = ttk.Progressbar(self.window, length=300, mode='determinate')
        self.video_progress.pack(pady=5)
        
        # Status
        self.status_label = ttk.Label(self.window, text="Preparing...")
        self.status_label.pack(pady=10)
        
        # Cancel button
        self.cancel_btn = ttk.Button(self.window, text="Cancel", command=self.cancel_download)
        self.cancel_btn.pack(pady=5)
        
        self.cancelled = False

    def start(self):
        self.download_thread = threading.Thread(target=self.download_videos)
        self.download_thread.start()

    def download_videos(self):
        total_videos = len(self.videos)
        self.total_progress["maximum"] = total_videos
        
        ydl_opts = {
            'format': self.options['quality'],
            'outtmpl': os.path.join(self.download_folder, '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
        }
        
        for i, video in enumerate(self.videos, 1):
            if self.cancelled:
                break
                
            self.current_label["text"] = f"Downloading: {video['title']}"
            self.status_label["text"] = f"Video {i} of {total_videos}"
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([f"https://www.youtube.com/watch?v={video['videoId']}"])
                self.total_progress["value"] = i
            except Exception as e:
                self.status_label["text"] = f"Error: {str(e)}"
                continue
        
        if not self.cancelled:
            self.status_label["text"] = "Download complete!"
        self.cancel_btn["text"] = "Close"

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            # Update video progress
            total = d.get('total_bytes')
            downloaded = d.get('downloaded_bytes')
            if total:
                percentage = (downloaded / total) * 100
                self.video_progress["value"] = percentage

    def cancel_download(self):
        if self.cancel_btn["text"] == "Close":
            self.window.destroy()
        else:
            self.cancelled = True
            self.status_label["text"] = "Cancelling..." 