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
        self._last_folder = None
        self._folders = set()
        self._results = []
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
        self.explore_btn = ttk.Button(btn_frame, text="Explore Downloaded", command=self.show_results_popup)
        try:
            self.explore_btn["state"] = "disabled"
        except Exception:
            pass
        self.explore_btn.pack(side="left", padx=5)
        self.cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.cancel_download)
        self.cancel_btn.pack(side="left", padx=5)
        
        self.cancelled = False

    def start(self):
        try:
            if self.download_folder:
                os.makedirs(self.download_folder, exist_ok=True)
        except Exception:
            pass
        self.download_thread = threading.Thread(target=self.download_videos)
        self.download_thread.start()

    def download_videos(self):
        total_videos = len(self.videos)
        self.total_progress["maximum"] = total_videos
        
        fmt = self.options.get('quality') if isinstance(self.options, dict) else None
        if not fmt:
            fmt = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        ffmpeg_ok = bool(shutil.which('ffmpeg'))
        if not ffmpeg_ok:
            fmt = 'b[ext=mp4]/b'
        base_opts = {
            'format': fmt,
            'progress_hooks': [self.progress_hook],
            'concurrent_fragment_downloads': 8,
            'http_chunk_size': 1048576,
            'ignoreerrors': True,
        }
        if ffmpeg_ok:
            base_opts['merge_output_format'] = 'mp4'

        downloaded_count = 0
        last_error = ''
        def _target_folder(v):
            try:
                if self.download_folder:
                    return self.download_folder
                vid = v.get('videoId')
                pid = None
                try:
                    pid = self.parent.video_playlist_cache.get(vid)
                except Exception:
                    pid = v.get('playlistId')
                if not pid:
                    try:
                        pi = v.get('playlistIndex')
                        if pi:
                            rev = {idx: pid2 for pid2, idx in getattr(self.parent, 'playlist_index_map', {}).items()}
                            pid = rev.get(pi)
                    except Exception:
                        pid = None
                if pid:
                    try:
                        ttl = ''
                        try:
                            if self.parent.playlist.playlist_tree.exists(pid):
                                vals = self.parent.playlist.playlist_tree.item(pid).get('values', [])
                                ttl = vals[1] if len(vals) > 1 else ''
                        except Exception:
                            ttl = ''
                        folder = os.path.join(self.parent.controller.default_folder, f"Playlist - {ttl or pid}")
                        return folder
                    except Exception:
                        pass
                q = getattr(self.parent, 'video_search_query', '') or 'Misc'
                return os.path.join(self.parent.controller.default_folder, f"Videos - {q}")
            except Exception:
                return self.parent.controller.default_folder

        for i, video in enumerate(self.videos, 1):
            if self.cancelled:
                break
                
            self.current_label["text"] = f"Downloading: {video['title']}"
            self.status_label["text"] = f"Video {i} of {total_videos}"
            
            try:
                folder = _target_folder(video)
                try:
                    os.makedirs(folder, exist_ok=True)
                except Exception:
                    pass
                try:
                    self._last_folder = folder
                except Exception:
                    pass
                try:
                    self._folders.add(folder)
                except Exception:
                    pass
                ydl_opts = dict(base_opts)
                ydl_opts['outtmpl'] = os.path.join(folder, '%(title)s.%(ext)s')
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([f"https://www.youtube.com/watch?v={video['videoId']}" ])
                self.total_progress["value"] = i
                downloaded_count += 1
                try:
                    pl_title = ''
                    pid = video.get('playlistId')
                    if not pid:
                        try:
                            pid = self.parent.video_playlist_cache.get(video.get('videoId'))
                        except Exception:
                            pid = None
                    if pid:
                        try:
                            if self.parent.playlist.playlist_tree.exists(pid):
                                vals = self.parent.playlist.playlist_tree.item(pid).get('values', [])
                                pl_title = vals[1] if len(vals) > 1 else ''
                            else:
                                pl_title = pid
                        except Exception:
                            pl_title = pid or ''
                    else:
                        try:
                            q = getattr(self.parent, 'video_search_query', '')
                            pl_title = q or ''
                        except Exception:
                            pl_title = ''
                    fpath = self._find_downloaded_file(folder, video.get('title',''))
                    self._results.append({'title': video.get('title',''), 'playlist': pl_title or '', 'folder': folder, 'file': fpath})
                except Exception:
                    pass
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
                base = self._last_folder or self.download_folder or ''
                files = [f for f in os.listdir(base) if os.path.isfile(os.path.join(base, f))]
            except Exception:
                files = []
            if downloaded_count > 0 or files:
                self.status_label["text"] = f"Download complete ({downloaded_count} files)!"
                try:
                    self.open_btn["state"] = "normal"
                    if len(self._folders) > 1:
                        try:
                            self.open_btn.configure(state="disabled")
                            self.explore_btn.configure(state="normal")
                        except Exception:
                            pass
                    else:
                        try:
                            self.explore_btn.configure(state="disabled")
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    self.parent.after(0, lambda: self.parent.refresh_video_statuses())
                except Exception:
                    pass
                try:
                    self.parent.after(0, lambda: self.parent.playlist.refresh_all_statuses())
                except Exception:
                    pass
            else:
                msg = last_error or "No files downloaded"
                self.status_label["text"] = f"Completed with issues: {msg}"
        self.cancel_btn["text"] = "Close"

    def open_folder(self):
        p = self._last_folder or self.download_folder
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

    def _find_downloaded_file(self, folder, title):
        try:
            name = str(title or '').strip()
            if not folder or not name:
                return None
            exts = ('.mp4', '.webm', '.mkv')
            candidates = []
            for f in os.listdir(folder):
                try:
                    if any(f.lower().endswith(e) for e in exts) and f.lower().startswith(name.lower()[:50]):
                        candidates.append(os.path.join(folder, f))
                except Exception:
                    pass
            if not candidates:
                return None
            try:
                candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            except Exception:
                pass
            return candidates[0]
        except Exception:
            return None

    def show_results_popup(self):
        try:
            try:
                from src.ui.table_panel import TablePanel
            except ModuleNotFoundError:
                from ui.table_panel import TablePanel
            win = tk.Toplevel(self.window)
            win.title("Downloaded Videos")
            win.geometry("720x440")
            panel = TablePanel(win, columns=("Playlist","Title","Actions"), show_page_size=False, size_label="Rows:")
            tv = panel.tree
            tv.column("Playlist", width=240, anchor="w")
            tv.column("Title", width=420, anchor="w")
            tv.column("Actions", width=100, anchor="center")
            for r in list(self._results or []):
                tv.insert('', 'end', values=(r.get('playlist',''), r.get('title',''), "📁  ▶"))
            tip = tk.Toplevel(win)
            tip.wm_overrideredirect(True)
            tip.withdraw()
            tip_label = ttk.Label(tip, background="#ffffe0", relief="solid", borderwidth=1)
            tip_label.pack(ipadx=4, ipady=2)
            def _show_tip(text, xr, yr):
                try:
                    tip_label.configure(text=text)
                    tip.geometry(f"+{xr+12}+{yr+12}")
                    tip.deiconify()
                except Exception:
                    pass
            def _hide_tip():
                try:
                    tip.withdraw()
                except Exception:
                    pass
            def _get_sel():
                try:
                    sel = tv.selection()
                    if not sel:
                        return None
                    idx = tv.index(sel[0])
                    return (self._results[idx] if idx < len(self._results) else None)
                except Exception:
                    return None
            def _open_sel_folder():
                r = _get_sel()
                if not r:
                    return
                p = r.get('folder')
                try:
                    if p and os.path.exists(p):
                        if os.name == "nt":
                            os.startfile(p)
                        elif sys.platform == "darwin":
                            subprocess.run(["open", p])
                        else:
                            subprocess.run(["xdg-open", p])
                except Exception:
                    pass
            def _play_sel_file():
                r = _get_sel()
                if not r:
                    return
                fp = r.get('file')
                if not fp:
                    _open_sel_folder()
                    return
                try:
                    if os.name == "nt":
                        os.startfile(fp)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", fp])
                    else:
                        subprocess.run(["xdg-open", fp])
                except Exception:
                    pass
            tv.bind("<Double-1>", lambda e: _play_sel_file())
            def _on_click(e):
                try:
                    iid = tv.identify_row(e.y)
                    col = tv.identify_column(e.x)
                    if iid:
                        tv.selection_set(iid)
                        if col == "#3":
                            try:
                                x, y, w, h = tv.bbox(iid, "#3")
                            except Exception:
                                x, w = 0, 0
                            if w:
                                if e.x < x + (w // 2):
                                    _open_sel_folder()
                                else:
                                    _play_sel_file()
                except Exception:
                    pass
            def _on_motion(e):
                try:
                    if tv.identify_region(e.x, e.y) == 'heading':
                        _hide_tip()
                        return
                    iid = tv.identify_row(e.y)
                    if not iid:
                        _hide_tip()
                        return
                    col = tv.identify_column(e.x)
                    if str(col) == "#3":
                        try:
                            x, y, w, h = tv.bbox(iid, "#3")
                        except Exception:
                            x, w = 0, 0
                        if w and e.x < x + (w // 2):
                            _show_tip("Open folder", e.x_root, e.y_root)
                        else:
                            _show_tip("Play video", e.x_root, e.y_root)
                    else:
                        _hide_tip()
                except Exception:
                    pass
            tv.bind("<Button-1>", _on_click)
            tv.bind("<Motion>", _on_motion)
            tv.bind("<Leave>", lambda e: _hide_tip())
            btns = ttk.Frame(win)
            btns.pack(fill="x", pady=6)
            ttk.Button(btns, text="Open Folder", command=_open_sel_folder).pack(side="left", padx=6)
            ttk.Button(btns, text="Play Video", command=_play_sel_file).pack(side="left", padx=6)
        except Exception:
            pass

    def cancel_download(self):
        if self.cancel_btn["text"] == "Close":
            self.window.destroy()
        else:
            self.cancelled = True
            self.status_label["text"] = "Cancelling..." 
