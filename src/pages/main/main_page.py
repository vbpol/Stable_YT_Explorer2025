import tkinter as tk
from tkinter import messagebox, filedialog
import webbrowser
import os
import csv
import sys
import subprocess
import threading  # Add this for download threading
import json
from src.config_manager import ConfigManager
from .menu_section import MenuSection
from .search_section import SearchSection
from .playlist_section import PlaylistSection
from .video_section import VideoSection
from .status_bar import StatusBar
from .video_player import VideoPlayer
from .download_options_dialog import DownloadOptionsDialog
from .download_manager import DownloadManager

class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_videos = []
        self.current_playlist_info = {}
        self.current_page_token = None
        self._initialize_components()

    def _initialize_components(self):
        """Initialize and pack GUI components."""
        self._create_sections()
        self._pack_sections()

    def _create_sections(self):
        """Create sections for the main page."""
        self.menu = MenuSection(self)
        self.search = SearchSection(self)
        self.playlist = PlaylistSection(self)
        self.video = VideoSection(self)
        self.status_bar = StatusBar(self)
        self.search_mode = 'playlists'
        self.current_videos = []
        self.current_playlist_info = None
        self.prev_page_token = None
        self.current_page_token = None

    def _pack_sections(self):
        """Pack sections into the main page."""
        self.search.pack(fill="x", padx=10, pady=5)
        self.playlist.pack(fill="both", expand=True, padx=10, pady=5)
        self.video.pack(fill="both", expand=True, padx=10, pady=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def clear_panels(self):
        try:
            self.playlist.playlist_tree.delete(*self.playlist.playlist_tree.get_children())
        except Exception:
            pass
        try:
            self.video.video_tree.delete(*self.video.video_tree.get_children())
        except Exception:
            pass
        self.current_videos = []
        self.current_playlist_info = None
        self.prev_page_token = None
        self.current_page_token = None

    def set_search_mode(self, mode_display):
        mode = (mode_display or '').strip().lower()
        if mode not in ('playlists', 'videos'):
            mode = 'playlists'
        if mode != self.search_mode:
            self.search_mode = mode
            self.clear_panels()
            try:
                if mode == 'playlists':
                    path = ConfigManager.get_last_search_path('playlists')
                    data = ConfigManager.load_json(path) or []
                    for pl in data:
                        self.playlist.update_playlist(pl)
                else:
                    path = ConfigManager.get_last_search_path('videos')
                    data = ConfigManager.load_json(path) or {}
                    videos = data.get('videos', [])
                    playlists = data.get('playlists', [])
                    for v in videos:
                        self.video.video_tree.insert('', 'end', values=(v.get('title', ''), v.get('duration', 'N/A')))
                    for pl in playlists:
                        self.playlist.update_playlist(pl)
                    self.current_videos = videos
            except Exception:
                pass

    def execute_search(self, query, mode_display):
        query = (query or '').strip()
        if not query:
            messagebox.showerror("Error", "Please enter a keyword.")
            return
        mode = (mode_display or '').strip().lower()
        if mode not in ('playlists', 'videos'):
            mode = 'playlists'
        self.search_mode = mode
        self.clear_panels()
        if mode == 'playlists':
            try:
                playlists = self.controller.playlist_handler.search_playlists(query)
                enriched = []
                for playlist in playlists:
                    try:
                        video_count = self.controller.playlist_handler.get_details(playlist["playlistId"])
                        playlist["video_count"] = video_count
                    except Exception:
                        playlist["video_count"] = "N/A"
                    self.playlist.update_playlist(playlist)
                    enriched.append(playlist)
                ConfigManager.save_json(ConfigManager.get_last_search_path('playlists'), enriched)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to fetch playlists: {e}")
        else:
            try:
                videos = self.controller.playlist_handler.search_videos(query)
                self.current_videos = videos
                for v in videos:
                    self.video.video_tree.insert('', 'end', values=(v.get('title', ''), v.get('duration', 'N/A')))

                seen_channels = set()
                collected_playlists = []
                for v in videos:
                    cid = v.get('channelId')
                    if cid and cid not in seen_channels:
                        seen_channels.add(cid)
                        try:
                            ch_playlists = self.controller.playlist_handler.get_channel_playlists(cid)
                            for pl in ch_playlists:
                                if not any(p['playlistId'] == pl['playlistId'] for p in collected_playlists):
                                    self.playlist.update_playlist(pl)
                                    collected_playlists.append(pl)
                        except Exception:
                            continue
                ConfigManager.save_json(ConfigManager.get_last_search_path('videos'), {
                    'videos': videos,
                    'playlists': collected_playlists
                })
            except Exception as e:
                messagebox.showerror("Error", f"Failed to fetch videos: {e}")

    # Core functionality methods
    def search_playlists(self):
        """Search for playlists based on the keyword."""
        query = self.search.search_entry.get()
        if not query:
            messagebox.showerror("Error", "Please enter a keyword.")
            return

        try:
            # Clear existing items
            self.playlist.playlist_tree.delete(
                *self.playlist.playlist_tree.get_children()
            )

            # Search for playlists
            playlists = self.controller.playlist_handler.search_playlists(query)
            
            # Update each playlist with video count and status
            for playlist in playlists:
                try:
                    video_count = self.controller.playlist_handler.get_details(
                        playlist["playlistId"]
                    )
                    playlist["video_count"] = video_count
                except Exception as e:
                    # If we can't get details, just use the playlist without video count
                    print(f"Note: Could not get details for playlist {playlist['title']}")
                    playlist["video_count"] = "N/A"
                
                self.playlist.update_playlist(playlist)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch playlists: {e}")

    def show_playlist_videos(self, event=None, page_token=None):
        """Show videos in the selected playlist with pagination."""
        print("Starting show_playlist_videos")  # Debug print
        
        if event:
            selected_item = self.playlist.get_selected_playlist()
        else:
            selected_item = self.playlist.playlist_tree.selection()[0]

        print(f"Selected playlist ID: {selected_item}")  # Debug print
        
        if not selected_item:
            print("No playlist selected")  # Debug print
            return

        playlist_id = selected_item
        playlist_values = self.playlist.playlist_tree.item(selected_item)["values"]
        print(f"Playlist values: {playlist_values}")  # Debug print
        
        playlist_title = playlist_values[0]
        channel_title = playlist_values[1]
        total_videos = int(playlist_values[2])
        
        self.current_playlist_info = {
            "title": playlist_title,
            "channel": channel_title,
            "id": playlist_id
        }

        try:
            # Get selected page size
            max_results = int(self.video.page_size_var.get())
            print(f"Fetching {max_results} videos")  # Debug print
            
            # Get videos for current page
            response = self.controller.playlist_handler.get_videos(
                playlist_id, 
                page_token,
                max_results=max_results
            )
            print(f"API Response: {response}")  # Debug print
            
            self.current_videos = response["videos"]
            self.current_page_token = response.get("nextPageToken")
            self.prev_page_token = response.get("prevPageToken")

            # Update video tree
            self.video.video_tree.delete(*self.video.video_tree.get_children())
            print(f"Loading {len(self.current_videos)} videos into tree")  # Debug print
            
            for video in self.current_videos:
                self.video.video_tree.insert(
                    "", "end",
                    values=(video["title"], video["duration"])
                )

            # Update pagination info
            total_pages = (total_videos + max_results - 1) // max_results
            if not hasattr(self, 'current_page') or page_token is None:
                self.current_page = 1
            elif page_token == self.current_page_token:
                self.current_page = min(self.current_page + 1, total_pages)
            elif page_token == self.prev_page_token:
                self.current_page = max(1, self.current_page - 1)
            
            self.video.total_label["text"] = f"Total videos: {total_videos}"
            self.video.page_indicator["text"] = f"Page {self.current_page} of {total_pages}"
            
            # Update pagination buttons
            self.video.next_page_btn["state"] = "normal" if self.current_page_token else "disabled"
            self.video.prev_page_btn["state"] = "normal" if self.prev_page_token else "disabled"

        except Exception as e:
            print(f"Error fetching videos: {str(e)}")  # Debug print
            messagebox.showerror("Error", f"Failed to fetch videos: {e}")

    def open_playlist(self, event):
        """Open the selected playlist in YouTube."""
        selected_item = self.playlist.playlist_tree.focus()
        if not selected_item:
            return

        playlist_id = selected_item
        playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
        webbrowser.open(playlist_url)

    def open_video(self, event):
        """Open the selected video in YouTube."""
        selected_item = self.video.video_tree.selection()
        if not selected_item:
            return

        selected_index = self.video.video_tree.index(selected_item[0])
        video = self.current_videos[selected_index]
        video_url = f"https://www.youtube.com/watch?v={video['videoId']}"
        webbrowser.open(video_url)

    def save_playlist(self):
        """Save the selected playlist details to a file."""
        if not self.current_playlist_info or not self.current_videos:
            messagebox.showerror("Error", "No playlist selected or no videos found.")
            return

        playlist_title = self.current_playlist_info["title"]
        channel_title = self.current_playlist_info["channel"]

        try:
            file_path = os.path.join(
                self.controller.default_folder,
                f"{playlist_title}.txt"
            )
            
            with open(file_path, 'w', encoding='utf-8') as txtfile:
                txtfile.write(f"Playlist: {playlist_title}\n")
                txtfile.write(f"Channel: {channel_title}\n")
                txtfile.write("\nVideos:\n")
                for i, video in enumerate(self.current_videos, 1):
                    txtfile.write(f"\n{i}. {video['title']}\n")
                    txtfile.write(f"   URL: https://www.youtube.com/watch?v={video['videoId']}\n")

            messagebox.showinfo("Success", f"Playlist saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save playlist: {str(e)}")

    def export_playlist_csv(self):
        """Export the current playlist to a CSV file."""
        if not self.current_playlist_info or not self.current_videos:
            messagebox.showerror("Error", "No playlist selected or no videos found.")
            return

        try:
            file_path = os.path.join(
                self.controller.default_folder,
                f"{self.current_playlist_info['title']}.csv"
            )
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Title', 'Video ID', 'URL', 'Duration'])
                for video in self.current_videos:
                    writer.writerow([
                        video['title'],
                        video['videoId'],
                        f"https://www.youtube.com/watch?v={video['videoId']}",
                        video['duration']
                    ])

            messagebox.showinfo("Success", f"Playlist exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export playlist: {str(e)}")

    def export_playlist_txt(self):
        """Export the current playlist to a text file."""
        if not self.current_playlist_info or not self.current_videos:
            messagebox.showerror("Error", "No playlist selected or no videos found.")
            return

        try:
            file_path = os.path.join(
                self.controller.default_folder,
                f"{self.current_playlist_info['title']}_export.txt"
            )
            
            with open(file_path, 'w', encoding='utf-8') as txtfile:
                txtfile.write(f"Playlist: {self.current_playlist_info['title']}\n")
                txtfile.write(f"Channel: {self.current_playlist_info['channel']}\n")
                txtfile.write(f"Total Videos: {len(self.current_videos)}\n\n")
                
                for i, video in enumerate(self.current_videos, 1):
                    txtfile.write(f"{i}. {video['title']} ({video['duration']})\n")
                    txtfile.write(f"   https://www.youtube.com/watch?v={video['videoId']}\n\n")

            messagebox.showinfo("Success", f"Playlist exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export playlist: {str(e)}")

    def change_download_folder(self):
        """Allow the user to change the default download folder."""
        new_folder = filedialog.askdirectory()
        if new_folder:
            self.controller.update_config(self.controller.api_key, new_folder)
            messagebox.showinfo("Success", f"Download folder updated to {new_folder}")

    def open_download_folder(self):
        """Open the download folder in file explorer."""
        if not self.current_playlist_info:
            return

        folder_path = os.path.join(
            self.controller.default_folder,
            f"Playlist - {self.current_playlist_info['title']}"
        )
        
        if os.path.exists(folder_path):
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder_path])
            else:
                subprocess.run(["xdg-open", folder_path])

    def view_downloaded_videos(self):
        """Open a window to view downloaded videos."""
        if not self.current_playlist_info:
            messagebox.showerror("Error", "No playlist selected.")
            return

        playlist_folder = os.path.join(
            self.controller.default_folder,
            f"Playlist - {self.current_playlist_info['title']}"
        )

        if not os.path.exists(playlist_folder):
            messagebox.showerror("Error", "No downloaded videos found for this playlist.")
            return

        # Create video player window
        player = VideoPlayer(self, playlist_folder)
        
        # Populate video list
        videos = [f for f in os.listdir(playlist_folder) if f.endswith('.mp4')]
        for video in videos:
            player.video_listbox.insert(tk.END, video)

    def download_playlist_videos(self):
        """Download videos from the current playlist."""
        print("\nStarting download process...")  # Debug print
        
        # First check if a playlist is selected
        selected_playlist = self.playlist.get_selected_playlist()
        if not selected_playlist:
            messagebox.showerror("Error", "Please select a playlist first.")
            return
        
        # Then check if videos are loaded
        if not self.current_videos:
            # Try to load videos if not already loaded
            self.show_playlist_videos()
            if not self.current_videos:
                messagebox.showerror("Error", "No videos found in the selected playlist.")
                return

        try:
            # Create download folder
            playlist_folder = os.path.join(
                self.controller.default_folder,
                f"Playlist - {self.current_playlist_info['title']}"
            )
            os.makedirs(playlist_folder, exist_ok=True)
            print(f"Created folder: {playlist_folder}")  # Debug print

            # Show download options dialog
            print("Creating download options dialog...")  # Debug print
            try:
                download_options = DownloadOptionsDialog(self)
                print(f"Dialog result: {download_options.result}")  # Debug print
            except Exception as dialog_error:
                print(f"Error creating dialog: {str(dialog_error)}")  # Debug print
                raise

            if not download_options.result:
                print("Download cancelled by user")  # Debug print
                return

            # Start download with progress tracking
            print("Creating download manager...")  # Debug print
            download_manager = DownloadManager(
                self, 
                self.current_videos,
                playlist_folder,
                download_options.result
            )
            print("Starting download manager...")  # Debug print
            download_manager.start()
            
        except Exception as e:
            print(f"Error in download process: {str(e)}")  # Debug print
            import traceback
            traceback.print_exc()  # Print full error traceback
            messagebox.showerror("Error", f"Download failed: {str(e)}")

    # ... (to be continued with more methods)