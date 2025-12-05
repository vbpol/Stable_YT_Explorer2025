import tkinter as tk
from tkinter import ttk

class DownloadOptionsDialog:
    def __init__(self, parent):
        print("Initializing DownloadOptionsDialog")  # Debug print
        self.window = tk.Toplevel(parent)
        self.window.title("Download Options")
        self.window.geometry("300x200")
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
            'quality': self.quality_var.get()
        }
        print(f"Selected quality: {self.result}")  # Debug print
        self.window.destroy()

    def cancel(self):
        print("Download cancelled")  # Debug print
        self.window.destroy() 
