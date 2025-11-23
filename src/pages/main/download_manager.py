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
        self.speed_eta_label = ttk.Label(self.window, text="")
        self.speed_eta_label.pack(pady=5)
        
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
            'concurrent_fragment_downloads': 4,
            'merge_output_format': 'mp4',
        }
        
        for i, video in enumerate(self.videos, 1):
            if self.cancelled:
                break
                
            self.window.after(0, lambda t=video['title']: self.current_label.configure(text=f"Downloading: {t}"))
            self.window.after(0, lambda x=i: self.status_label.configure(text=f"Video {x} of {total_videos}"))
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([f"https://www.youtube.com/watch?v={video['videoId']}"])
                self.window.after(0, lambda v=i: self.total_progress.configure(value=v))
            except Exception as e:
                self.window.after(0, lambda msg=str(e): self.status_label.configure(text=f"Error: {msg}"))
                continue
        
        if not self.cancelled:
            self.window.after(0, lambda: self.status_label.configure(text="Download complete!"))
        self.window.after(0, lambda: self.cancel_btn.configure(text="Close"))

    def progress_hook(self, d):
        status = d.get('status')
        if status == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes') or 0
            if total:
                percentage = downloaded / total * 100
                if percentage < 0:
                    percentage = 0
                elif percentage > 100:
                    percentage = 100
                self.window.after(0, lambda v=percentage: self.video_progress.configure(value=v))
            speed = d.get('speed')
            eta = d.get('eta')
            def _fmt():
                s = f"{speed/1024/1024:.2f} MB/s" if speed else ""
                e = f"ETA {eta}s" if eta else ""
                txt = f"{s} {e}".strip()
                self.speed_eta_label.configure(text=txt)
            self.window.after(0, _fmt)
        elif status == 'finished':
            self.window.after(0, lambda: self.video_progress.configure(value=100))

    def cancel_download(self):
        if self.cancel_btn["text"] == "Close":
            self.window.destroy()
        else:
            self.cancelled = True
            self.status_label["text"] = "Cancelling..."