import tkinter as tk
from tkinter import ttk
try:
    from src.config_manager import ConfigManager
except ModuleNotFoundError:
    from config_manager import ConfigManager

class DownloadOptionsDialog:
    def __init__(self, parent):
        print("Initializing DownloadOptionsDialog")  # Debug print
        self.window = tk.Toplevel(parent)
        self.window.title("Download Options")
        self.window.geometry("360x280")
        self.result = None
        
        print("Setting up dialog components")  # Debug print
        # Quality selection
        ttk.Label(self.window, text="Video Quality:").pack(pady=5)
        self.quality_var = tk.StringVar(value="bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best")
        quality_frame = ttk.Frame(self.window)
        quality_frame.pack(pady=5)
        
        qualities = [
            ("Best", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"),
            ("720p", "bestvideo[ext=mp4][height>=720]+bestaudio[ext=m4a]/best[ext=mp4]/best"),
            ("480p", "bestvideo[ext=mp4][height>=480]+bestaudio[ext=m4a]/best[ext=mp4]/best"),
            ("360p", "bestvideo[ext=mp4][height>=360]+bestaudio[ext=m4a]/best[ext=mp4]/best")
        ]
        
        for text, value in qualities:
            ttk.Radiobutton(quality_frame, text=text, value=value, 
                          variable=self.quality_var).pack(side=tk.LEFT, padx=5)
        ttk.Label(self.window, text="Cookies:").pack(pady=5)
        self.cookies_var = tk.StringVar(value=ConfigManager.get_cookie_source())
        cookies_frame = ttk.Frame(self.window)
        cookies_frame.pack(pady=5)
        for text, value in [("None","none"),("Edge","edge"),("Chrome","chrome"),("Firefox","firefox"),("File","cookiefile")]:
            ttk.Radiobutton(cookies_frame, text=text, value=value, variable=self.cookies_var).pack(side=tk.LEFT, padx=5)
        file_frame = ttk.Frame(self.window)
        file_frame.pack(fill="x", padx=8)
        self.cookie_file_var = tk.StringVar(value="")
        ttk.Entry(file_frame, textvariable=self.cookie_file_var).pack(side=tk.LEFT, fill="x", expand=True)
        ttk.Button(file_frame, text="Browse", command=self._browse_cookiefile).pack(side=tk.LEFT, padx=5)
        self.fallback_videos_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.window, text="Fallback to 'Videos - {query}' when playlist unknown", variable=self.fallback_videos_var).pack(pady=6)
        self.use_channel_title_var = tk.BooleanVar(value=ConfigManager.get_use_channel_title_fallback())
        ttk.Checkbutton(self.window, text="Prefer channel title for 'Videos - {...}'", variable=self.use_channel_title_var).pack(pady=4)
        
        # Buttons
        button_frame = ttk.Frame(self.window)
        button_frame.pack(side=tk.BOTTOM, pady=10)
        
        ttk.Button(button_frame, text="Start Download", 
                  command=self.start_download).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        print("Setting dialog properties")  # Debug print
        self.window.transient(parent)
        self.window.grab_set()
        print("Waiting for dialog response")  # Debug print
        parent.wait_window(self.window)
        print("Dialog closed")  # Debug print

    def start_download(self):
        print("Start download clicked")  # Debug print
        self.result = {
            'quality': self.quality_var.get(),
            'cookies_source': self.cookies_var.get(),
            'cookie_file': self.cookie_file_var.get().strip(),
            'fallback_videos': bool(self.fallback_videos_var.get()),
            'use_channel_title_fallback': bool(self.use_channel_title_var.get()),
        }
        print(f"Selected quality: {self.result}")  # Debug print
        try:
            ConfigManager.set_cookie_source(self.cookies_var.get())
        except Exception:
            pass
        try:
            ConfigManager.set_use_channel_title_fallback(bool(self.use_channel_title_var.get()))
        except Exception:
            pass
        self.window.destroy()

    def cancel(self):
        print("Download cancelled")  # Debug print
        self.window.destroy() 

    def _browse_cookiefile(self):
        try:
            import tkinter.filedialog as fd
            p = fd.askopenfilename(title="Select cookies.txt", filetypes=[["Text","*.txt"],["All","*.*"]])
            if p:
                self.cookie_file_var.set(p)
        except Exception:
            pass
