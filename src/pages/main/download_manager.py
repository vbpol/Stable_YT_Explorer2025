import tkinter as tk
from tkinter import ttk
import threading
import yt_dlp
import os
import sys
import subprocess
import shutil

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
        
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(pady=5)
        self.open_btn = ttk.Button(btn_frame, text="Open Folder", command=self.open_folder)
        try:
            self.open_btn["state"] = "disabled"
        except Exception:
            pass
        self.open_btn.pack(side="left", padx=5)
        self.cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.cancel_download)
        self.cancel_btn.pack(side="left", padx=5)
        
        self.cancelled = False

    def start(self):
        try:
            os.makedirs(self.download_folder, exist_ok=True)
        except Exception:
            pass
        self.download_thread = threading.Thread(target=self.download_videos)
        self.download_thread.start()

    def download_videos(self):
        total_videos = len(self.videos)
        self.total_progress["maximum"] = total_videos
        
        fmt = self.options['quality']
        ffmpeg_ok = bool(shutil.which('ffmpeg'))
        if not ffmpeg_ok:
            fmt = 'b[ext=mp4]/b'
        ydl_opts = {
            'format': fmt,
            'outtmpl': os.path.join(self.download_folder, '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'concurrent_fragment_downloads': 8,
            'http_chunk_size': 1048576,
            'ignoreerrors': True,
        }
        if ffmpeg_ok:
            ydl_opts['merge_output_format'] = 'mp4'

        downloaded_count = 0
        last_error = ''
        for i, video in enumerate(self.videos, 1):
            if self.cancelled:
                break
                
            self.current_label["text"] = f"Downloading: {video['title']}"
            self.status_label["text"] = f"Video {i} of {total_videos}"
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([f"https://www.youtube.com/watch?v={video['videoId']}"])
                self.total_progress["value"] = i
                downloaded_count += 1
                try:
                    self.open_btn["state"] = "normal"
                except Exception:
                    pass
            except Exception as e:
                last_error = str(e)
                self.status_label["text"] = f"Error: {last_error}"
                continue
        
        if not self.cancelled:
            try:
                files = [f for f in os.listdir(self.download_folder) if os.path.isfile(os.path.join(self.download_folder, f))]
            except Exception:
                files = []
            if downloaded_count > 0 or files:
                self.status_label["text"] = f"Download complete ({downloaded_count} files)!"
                try:
                    self.open_btn["state"] = "normal"
                except Exception:
                    pass
            else:
                msg = last_error or "No files downloaded"
                self.status_label["text"] = f"Completed with issues: {msg}"
        self.cancel_btn["text"] = "Close"

    def open_folder(self):
        p = self.download_folder
        try:
            if not os.path.exists(p):
                return
            if os.name == "nt":
                os.startfile(p)
            elif sys.platform == "darwin":
                subprocess.run(["open", p])
            else:
                subprocess.run(["xdg-open", p])
        except Exception:
            pass

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            # Update video progress
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes') or 0
            if total and total > 0:
                try:
                    self.video_progress.configure(mode='determinate')
                except Exception:
                    pass
                percentage = (downloaded / total) * 100
                self.video_progress["value"] = percentage
            else:
                try:
                    self.video_progress.configure(mode='indeterminate')
                    self.video_progress.start(50)
                except Exception:
                    pass
            try:
                sp = d.get('speed')
                eta = d.get('eta')
                if sp:
                    self.status_label["text"] = f"Speed: {int(sp)} B/s  ETA: {eta or ''}"
            except Exception:
                pass
        elif d['status'] == 'finished':
            try:
                self.video_progress.stop()
                self.video_progress.configure(mode='determinate')
                self.video_progress["value"] = 100
            except Exception:
                pass

    def cancel_download(self):
        if self.cancel_btn["text"] == "Close":
            self.window.destroy()
        else:
            self.cancelled = True
            self.status_label["text"] = "Cancelling..." 
