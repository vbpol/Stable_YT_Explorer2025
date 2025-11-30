import tkinter as tk
from tkinter import filedialog, messagebox
from .base_section import BaseSection
from src.pages.setup_page import SetupPage

class MenuSection(BaseSection):
    def setup_gui(self):
        menubar = tk.Menu(self.controller.root)
        self.controller.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        try:
            file_menu.add_command(label="Change Download Folder", command=self.main_page.change_download_folder)
        except Exception:
            def _fallback_change_folder():
                try:
                    new_folder = filedialog.askdirectory()
                    if new_folder:
                        try:
                            self.controller.update_config(self.controller.api_key, new_folder)
                        except Exception:
                            try:
                                from src.config_manager import ConfigManager
                                ConfigManager.save_config(self.controller.api_key, new_folder)
                            except Exception:
                                pass
                        try:
                            messagebox.showinfo("Success", f"Download folder updated to {new_folder}")
                        except Exception:
                            pass
                except Exception:
                    pass
            file_menu.add_command(label="Change Download Folder", command=_fallback_change_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Settings", command=lambda: self.controller.show_frame(SetupPage))
        file_menu.add_separator()
        try:
            file_menu.add_command(label="Export Playlist (CSV)", command=self.main_page.export_playlist_csv)
        except Exception:
            def _export_csv_fallback():
                try:
                    mpi = getattr(self.main_page, 'current_playlist_info', None)
                    vids = getattr(self.main_page, 'current_videos', [])
                    if not mpi or not vids:
                        messagebox.showerror("Error", "No playlist selected or no videos found.")
                        return
                    import csv, os
                    fp = os.path.join(self.controller.default_folder, f"{mpi['title']}.csv")
                    with open(fp, 'w', newline='', encoding='utf-8') as csvfile:
                        w = csv.writer(csvfile)
                        w.writerow(['Title', 'Video ID', 'URL', 'Duration'])
                        for v in vids:
                            w.writerow([v.get('title',''), v.get('videoId',''), f"https://www.youtube.com/watch?v={v.get('videoId','')}", v.get('duration','')])
                    messagebox.showinfo("Success", f"Playlist exported to {fp}")
                except Exception:
                    pass
            file_menu.add_command(label="Export Playlist (CSV)", command=_export_csv_fallback)
        try:
            file_menu.add_command(label="Export Playlist (TXT)", command=self.main_page.export_playlist_txt)
        except Exception:
            def _export_txt_fallback():
                try:
                    mpi = getattr(self.main_page, 'current_playlist_info', None)
                    vids = getattr(self.main_page, 'current_videos', [])
                    if not mpi or not vids:
                        messagebox.showerror("Error", "No playlist selected or no videos found.")
                        return
                    import os
                    fp = os.path.join(self.controller.default_folder, f"{mpi['title']}_export.txt")
                    with open(fp, 'w', encoding='utf-8') as txtfile:
                        txtfile.write(f"Playlist: {mpi['title']}\n")
                        txtfile.write(f"Channel: {mpi['channel']}\n")
                        txtfile.write(f"Total Videos: {len(vids)}\n\n")
                        for i, video in enumerate(vids, 1):
                            txtfile.write(f"{i}. {video.get('title','')} ({video.get('duration','')})\n")
                            txtfile.write(f"   https://www.youtube.com/watch?v={video.get('videoId','')}\n\n")
                    messagebox.showinfo("Success", f"Playlist exported to {fp}")
                except Exception:
                    pass
            file_menu.add_command(label="Export Playlist (TXT)", command=_export_txt_fallback)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.controller.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Sort by Name", command=lambda: self.main_page._sort_playlists("Name"))
        view_menu.add_command(label="Sort by Channel", command=lambda: self.main_page._sort_playlists("Channel"))
        view_menu.add_command(label="Sort by Videos", command=lambda: self.main_page._sort_playlists("Videos"))
        menubar.add_cascade(label="View", menu=view_menu)

        download_menu = tk.Menu(menubar, tearoff=0)
        quality_menu = tk.Menu(download_menu, tearoff=0)
        quality_menu.add_command(label="Best", command=lambda: self.main_page.set_preferred_quality("best"))
        quality_menu.add_command(label="720p", command=lambda: self.main_page.set_preferred_quality("best[height<=720]"))
        quality_menu.add_command(label="480p", command=lambda: self.main_page.set_preferred_quality("best[height<=480]"))
        quality_menu.add_command(label="360p", command=lambda: self.main_page.set_preferred_quality("best[height<=360]"))
        download_menu.add_cascade(label="Preferred Quality", menu=quality_menu)

        fragments_menu = tk.Menu(download_menu, tearoff=0)
        fragments_menu.add_command(label="1", command=lambda: self.main_page.set_concurrent_fragments(1))
        fragments_menu.add_command(label="2", command=lambda: self.main_page.set_concurrent_fragments(2))
        fragments_menu.add_command(label="4", command=lambda: self.main_page.set_concurrent_fragments(4))
        fragments_menu.add_command(label="8", command=lambda: self.main_page.set_concurrent_fragments(8))
        download_menu.add_cascade(label="Concurrent Fragments", menu=fragments_menu)

        try:
            download_menu.add_checkbutton(label="Post-Processing (merge to mp4)", onvalue=1, offvalue=0, command=self.main_page.toggle_post_processing)
        except Exception:
            def _toggle_pp_fallback():
                try:
                    cur = getattr(self.main_page, 'post_processing_enabled', False)
                    setattr(self.main_page, 'post_processing_enabled', not cur)
                    try:
                        from tkinter import messagebox
                        messagebox.showinfo("Info", f"Post-processing: {'ON' if not cur else 'OFF'}")
                    except Exception:
                        pass
                except Exception:
                    pass
            download_menu.add_checkbutton(label="Post-Processing (merge to mp4)", onvalue=1, offvalue=0, command=_toggle_pp_fallback)
        menubar.add_cascade(label="Download", menu=download_menu)
