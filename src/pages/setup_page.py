import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import webbrowser
from googleapiclient.errors import HttpError
try:
    from src.playlist import Playlist
    from src.config_manager import ConfigManager
except ModuleNotFoundError:
    from playlist import Playlist
    from config_manager import ConfigManager

class SetupPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._api_valid = False
        self.setup_gui()

    def setup_gui(self):
        """Set up the GUI components for the setup page."""
        self._create_api_key_section()
        self._create_folder_section()
        self._create_save_button()
        self._create_start_button()
        self._create_help_section()

    def _create_api_key_section(self):
        tk.Label(self, text="Enter Your YouTube API Key").pack(pady=10)
        frame = ttk.Frame(self)
        frame.pack(pady=5)
        self.api_key_entry = tk.Entry(frame, width=50, show="*")
        self.api_key_entry.insert(0, self.controller.api_key)
        self.api_key_entry.pack(side="left", padx=5)
        self.show_var = tk.BooleanVar(value=False)
        tk.Checkbutton(frame, text="Show", variable=self.show_var, command=self._toggle_show).pack(side="left")
        tk.Button(self, text="Validate API Key", command=self.validate_api_key).pack(pady=5)

        keys = ConfigManager.get_available_api_keys()
        if keys:
            tk.Label(self, text="Available API Keys").pack(pady=5)
            self.selected_key = tk.StringVar(value=keys[0])
            ttk.OptionMenu(self, self.selected_key, keys[0], *keys, command=self._apply_selected_key).pack(pady=5)

    def _create_folder_section(self):
        """Create the folder selection section."""
        tk.Label(self, text="Select Default Download Folder").pack(pady=10)
        self.folder_var = tk.StringVar(value=self.controller.default_folder)
        tk.Entry(self, textvariable=self.folder_var, width=50, state="readonly").pack(pady=5)
        tk.Button(self, text="Browse", command=self.browse_folder).pack(pady=5)

    def _create_save_button(self):
        """Create the save settings button."""
        tk.Button(self, text="Save Settings", command=self.save_settings).pack(pady=10)

    def _create_start_button(self):
        """Create the start app button, enabled only when API is validated."""
        self.start_btn = tk.Button(self, text="Start App", state="disabled", command=self.start_app)
        self.start_btn.pack(pady=4)

    def browse_folder(self):
        """Browse and select a default download folder."""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)

    def save_settings(self):
        """Save API key and default download folder."""
        api_key = self.api_key_entry.get().strip()
        default_folder = self.folder_var.get().strip()
        
        if not api_key:
            messagebox.showerror("Error", "Please enter a YouTube API key.")
            return
            
        if not default_folder:
            messagebox.showerror("Error", "Please select a download folder.")
            return
            
        try:
            try:
                Playlist(api_key).search_playlists("test", 1)
            except HttpError as err:
                try:
                    data = json.loads(err.content.decode())
                    reason = data.get("error", {}).get("errors", [{}])[0].get("reason", "unknown")
                    messagebox.showwarning("Warning", f"API validation failed ({reason}). Saving anyway.")
                except Exception:
                    messagebox.showwarning("Warning", "API validation failed. Saving anyway.")
            except Exception:
                messagebox.showwarning("Warning", "Network error during validation. Saving anyway.")
            ConfigManager.save_env_api_keys([api_key])
            self.controller.update_config(api_key, default_folder)
            try:
                from src.pages.main.main_page import MainPage
            except ModuleNotFoundError:
                from pages.main.main_page import MainPage
            messagebox.showinfo("Success", "Settings saved successfully.")
            self.controller.show_frame(MainPage)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")

    def validate_api_key(self):
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter a YouTube API key.")
            return
        try:
            Playlist(api_key).search_playlists("test", 1)
            messagebox.showinfo("Success", "API key is valid.")
            try:
                self._api_valid = True
                if hasattr(self, 'start_btn'):
                    self.start_btn["state"] = "normal"
            except Exception:
                pass
        except HttpError as err:
            try:
                data = json.loads(err.content.decode())
                reason = data.get("error", {}).get("errors", [{}])[0].get("reason", "unknown")
                messagebox.showerror("Error", f"API key invalid or quota issue ({reason}).")
            except Exception:
                messagebox.showerror("Error", "API key invalid or quota exceeded.")
        except Exception:
            messagebox.showerror("Error", "Network error during validation.")

    def start_app(self):
        """Start the main app once API key is validated and folder selected."""
        api_key = self.api_key_entry.get().strip()
        default_folder = self.folder_var.get().strip()
        if not self._api_valid:
            messagebox.showerror("Error", "Please validate the API key first.")
            return
        if not api_key:
            messagebox.showerror("Error", "Please enter a YouTube API key.")
            return
        if not default_folder:
            messagebox.showerror("Error", "Please select a download folder.")
            return
        try:
            ConfigManager.save_env_api_keys([api_key])
        except Exception:
            pass
        try:
            self.controller.update_config(api_key, default_folder)
        except Exception:
            pass
        try:
            from src.pages.main.main_page import MainPage
        except ModuleNotFoundError:
            from pages.main.main_page import MainPage
        try:
            self.controller.show_frame(MainPage)
        except Exception:
            messagebox.showerror("Error", "Failed to start the app.")

    def _apply_selected_key(self, value):
        self.api_key_entry.delete(0, tk.END)
        self.api_key_entry.insert(0, value)

    def _toggle_show(self):
        self.api_key_entry.config(show="" if self.show_var.get() else "*")

    def _create_help_section(self):
        box = ttk.Frame(self)
        box.pack(pady=12)
        ttk.Label(box, text="Need a YouTube API Key?").pack()
        ttk.Button(box, text="Open Step-by-Step Guide", command=self._open_api_key_help).pack(pady=4)
        ttk.Button(box, text="Open Google Cloud Console", command=lambda: webbrowser.open("https://console.cloud.google.com/apis/credentials")).pack(pady=2)

    def _open_api_key_help(self):
        win = tk.Toplevel(self)
        win.title("How to get a YouTube API Key")
        frm = ttk.Frame(win)
        frm.pack(fill="both", expand=True, padx=12, pady=12)
        txt = tk.Text(frm, width=72, height=16)
        txt.pack(fill="both", expand=True)
        steps = (
            "1. Go to Google Cloud Console (opens from the button).\n"
            "2. Create a project or select an existing one.\n"
            "3. Enable the YouTube Data API v3 in the APIs & Services.\n"
            "4. Create credentials: choose API key.\n"
            "5. Copy the key and paste it above.\n"
            "6. Save settings and start using the app.\n"
        )
        txt.insert("end", steps)
        txt.config(state="disabled")
