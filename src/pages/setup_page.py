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
        self.after(1000, self._auto_select_key_startup)

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
        tk.Button(self, text="Auto Select Valid Key", command=self._auto_select_key_btn).pack(pady=2)

        keys = ConfigManager.get_available_api_keys()
        if keys:
            tk.Label(self, text="Available API Keys").pack(pady=5)
            self.selected_key = tk.StringVar(value=keys[0])
            self.api_keys_menu = ttk.OptionMenu(self, self.selected_key, keys[0], *keys, command=self._apply_selected_key)
            self.api_keys_menu.pack(pady=5)
        else:
            self.selected_key = tk.StringVar(value="")
            self.api_keys_menu = None

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
                self._refresh_api_keys_dropdown()
            except Exception:
                pass
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
        
        is_valid = False
        is_quota_exceeded = False
        
        try:
            # Use cheap validation (1 unit) instead of search (100 units)
            Playlist(api_key).validate_key()
            is_valid = True
        except HttpError as err:
            try:
                data = json.loads(err.content.decode())
                reason = data.get("error", {}).get("errors", [{}])[0].get("reason", "unknown")
                
                if reason == "quotaExceeded":
                    is_valid = True
                    is_quota_exceeded = True
                else:
                    messagebox.showerror("Error", f"API key invalid or error ({reason}).")
                    return
            except Exception:
                messagebox.showerror("Error", "API key invalid or quota exceeded.")
                return
        except Exception:
            messagebox.showerror("Error", "Network error during validation.")
            return

        if is_valid:
            try:
                self._api_valid = True
                if hasattr(self, 'start_btn'):
                    self.start_btn["state"] = "normal"
            except Exception:
                pass
                
            if is_quota_exceeded:
                msg = "API key is VALID, but daily quota is exhausted.\nSave it to .env anyway?"
                title = "Quota Warning"
            else:
                msg = "API key is valid.\nSave it to .env and add to dropdown?"
                title = "Success"
                
            try:
                ask = messagebox.askyesno(title, msg)
            except Exception:
                ask = True
                
            if ask:
                try:
                    ConfigManager.save_env_api_keys([api_key])
                except Exception:
                    pass
                try:
                    self._refresh_api_keys_dropdown()
                except Exception:
                    pass
                try:
                    messagebox.showinfo("Saved", "API key saved to .env and added to list.")
                except Exception:
                    pass

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
            self._refresh_api_keys_dropdown()
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

    def _refresh_api_keys_dropdown(self):
        try:
            keys = ConfigManager.get_available_api_keys()
        except Exception:
            keys = []
        if not keys:
            return
        try:
            if self.selected_key:
                self.selected_key.set(keys[0])
        except Exception:
            pass
        try:
            if self.api_keys_menu:
                m = self.api_keys_menu["menu"]
                m.delete(0, "end")
                for k in keys:
                    m.add_command(label=k, command=lambda v=k: self._apply_selected_key(v))
        except Exception:
            try:
                # fallback: recreate section
                for w in self.winfo_children():
                    if isinstance(w, ttk.OptionMenu):
                        w.destroy()
                self._create_api_key_section()
            except Exception:
                pass

    def _auto_select_key_startup(self):
        """Run auto-select silently on startup."""
        self._run_auto_select(silent=True)

    def _auto_select_key_btn(self):
        """Run auto-select via button."""
        self._run_auto_select(silent=False)

    def _run_auto_select(self, silent=False):
        """
        Iterate through registered API keys and select the first valid one.
        If silent is True, only show warning if no valid keys found.
        """
        keys = ConfigManager.get_available_api_keys()
        if not keys:
            if not silent:
                messagebox.showinfo("Info", "No API keys found in configuration.")
            return

        found_valid_key = None
        fallback_key = None # Valid but quota exhausted
        quota_exhausted_keys = []
        
        for key in keys:
            try:
                Playlist(key).validate_key()
                found_valid_key = key
                break
            except HttpError as err:
                try:
                    data = json.loads(err.content.decode())
                    reason = data.get("error", {}).get("errors", [{}])[0].get("reason", "unknown")
                    if reason == "quotaExceeded":
                        quota_exhausted_keys.append(key)
                        if not fallback_key:
                            fallback_key = key
                except Exception:
                    pass
                continue
            except Exception:
                continue
        
        final_key = found_valid_key or fallback_key
        
        if final_key:
            try:
                self.api_key_entry.delete(0, tk.END)
                self.api_key_entry.insert(0, final_key)
                self._api_valid = True
                if hasattr(self, 'start_btn'):
                    self.start_btn["state"] = "normal"
                
                if hasattr(self, 'selected_key'):
                    self.selected_key.set(final_key)
                
                if not silent:
                    if found_valid_key:
                         messagebox.showinfo("Success", f"Auto-selected valid key: {final_key[:10]}...")
                    else:
                         messagebox.showwarning("Quota Warning", f"Selected fallback key (Quota Exhausted): {final_key[:10]}...\nYou can use the app, but some API features may fail.")
            except Exception as e:
                if not silent:
                    messagebox.showerror("Error", f"Error updating UI: {e}")
        else:
            if quota_exhausted_keys:
                # Should be covered by fallback_key logic, but safe fallback
                msg = f"Checked {len(keys)} keys.\nAll {len(quota_exhausted_keys)} are quota exhausted."
            else:
                msg = "No valid API keys found among registered keys."
            
            if silent:
                 messagebox.showwarning("API Key Check", msg)
            else:
                 messagebox.showerror("Error", msg)
