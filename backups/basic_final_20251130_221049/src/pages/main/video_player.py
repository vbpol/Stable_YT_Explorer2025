import tkinter as tk
from tkinter import ttk
import vlc
import sys
import os

class VideoPlayer:
    def __init__(self, parent, playlist_folder):
        self.window = tk.Toplevel(parent)
        self.window.title("Video Player")
        self.window.geometry("1024x768")
        self.playlist_folder = playlist_folder
        
        # Create VLC instance
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        
        self.setup_gui()
        try:
            self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        except Exception:
            pass
        
    def setup_gui(self):
        # Create main container with paned window
        self.main_pane = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        self.main_pane.pack(fill="both", expand=True)

        # Create video frame
        self.setup_video_frame()
        
        # Create playlist panel
        self.setup_playlist_panel()
        
        # Create controls
        self.setup_controls()

    def setup_video_frame(self):
        video_frame = ttk.Frame(self.main_pane)
        self.main_pane.add(video_frame, weight=3)

        # Create canvas for video
        self.canvas = tk.Canvas(video_frame, background="black")
        self.canvas.pack(fill="both", expand=True)

        # Get handle for video rendering
        if sys.platform == "win32":
            self.player.set_hwnd(self.canvas.winfo_id())
        else:
            self.player.set_xwindow(self.canvas.winfo_id())

    def setup_playlist_panel(self):
        self.video_list_frame = ttk.Frame(self.main_pane, width=300)
        self.main_pane.add(self.video_list_frame, weight=1)

        # Add video list with scrollbar
        list_frame = ttk.Frame(self.video_list_frame)
        list_frame.pack(fill="both", expand=True)
        
        self.video_listbox = tk.Listbox(list_frame, width=50)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.video_listbox.yview)
        self.video_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.video_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.video_listbox.bind('<Double-Button-1>', self.play_selected_video)

    def setup_controls(self):
        control_frame = ttk.Frame(self.window)
        control_frame.pack(fill="x", side="bottom", pady=5)

        # Time slider and label
        self.time_var = tk.StringVar(value="0:00 / 0:00")
        time_label = ttk.Label(control_frame, textvariable=self.time_var)
        time_label.pack(side="top", pady=2)

        self.time_slider = ttk.Scale(control_frame, from_=0, to=100, orient="horizontal")
        self.time_slider.pack(side="top", fill="x", padx=5)
        self.time_slider.bind("<ButtonRelease-1>", self.seek_video)

        # Button frame
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill="x", pady=5)

        # Control buttons
        ttk.Button(button_frame, text="⏮", command=lambda: self.seek(-10)).pack(side="left", padx=2)
        self.play_button = ttk.Button(button_frame, text="Play", command=self.toggle_play)
        self.play_button.pack(side="left", padx=2)
        ttk.Button(button_frame, text="⏹", command=self.stop_video).pack(side="left", padx=2)
        ttk.Button(button_frame, text="⏭", command=lambda: self.seek(10)).pack(side="left", padx=2)

        # Speed control
        self.rate_label = ttk.Label(button_frame, text="Speed: 1.0x")
        self.rate_label.pack(side="left", padx=10)
        
        for rate in [0.5, 1.0, 1.5, 2.0]:
            ttk.Button(button_frame, text=f"{rate}x", 
                      command=lambda r=rate: self.set_rate(r)).pack(side="left", padx=2)

        # Volume control
        self.volume_slider = ttk.Scale(button_frame, from_=0, to=100, orient="horizontal", length=100)
        self.volume_slider.set(100)
        self.volume_slider.pack(side="left", padx=10)
        self.volume_slider.bind("<ButtonRelease-1>", self.set_volume)

        # Panel toggle and fullscreen
        ttk.Button(button_frame, text="Toggle Playlist", 
                  command=self.toggle_playlist_panel).pack(side="right", padx=2)
        ttk.Button(button_frame, text="Fullscreen", 
                  command=self.toggle_fullscreen).pack(side="right", padx=2)

    def play_selected_video(self, event=None):
        selection = self.video_listbox.curselection()
        if selection:
            video_path = os.path.join(self.playlist_folder, self.video_listbox.get(selection[0]))
            media = self.instance.media_new(video_path)
            self.player.set_media(media)
            self.player.play()
            self.update_time_label()

    def toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
            self.play_button["text"] = "Play"
        else:
            self.player.play()
            self.play_button["text"] = "Pause"

    def stop_video(self):
        self.player.stop()
        self.play_button["text"] = "Play"
        self.time_var.set("0:00 / 0:00")
        self.time_slider.set(0)

    def on_close(self):
        try:
            self.stop_video()
        except Exception:
            pass
        try:
            self.player.release()
        except Exception:
            pass
        try:
            self.instance.release()
        except Exception:
            pass
        try:
            self.window.destroy()
        except Exception:
            pass

    def seek_video(self, event):
        if self.player.get_length() > 0:
            pos = self.time_slider.get() / 100
            self.player.set_position(pos)

    def seek(self, seconds):
        current_time = self.player.get_time() + (seconds * 1000)
        self.player.set_time(current_time)

    def set_rate(self, rate):
        self.player.set_rate(rate)
        self.rate_label["text"] = f"Speed: {rate}x"

    def set_volume(self, event):
        self.player.audio_set_volume(int(self.volume_slider.get()))

    def toggle_fullscreen(self):
        self.player.toggle_fullscreen()

    def toggle_playlist_panel(self):
        if self.video_list_frame.winfo_viewable():
            self.main_pane.forget(self.video_list_frame)
        else:
            self.main_pane.add(self.video_list_frame, weight=1)

    def update_time_label(self):
        if self.player.is_playing():
            current = self.player.get_time()
            total = self.player.get_length()
            if total > 0:
                self.time_var.set(f"{self.format_time(current)} / {self.format_time(total)}")
                self.time_slider.set((current / total) * 100)
        self.window.after(1000, self.update_time_label)

    @staticmethod
    def format_time(milliseconds):
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}" 
