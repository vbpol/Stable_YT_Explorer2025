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
        self.setup_gui()

    def setup_gui(self):
        """Set up the GUI components for the setup page."""
        self._create_api_key_section()
        self._create_folder_section()
        self._create_save_button()
        self._create_help_section()

    def _create_api_key_section(self):
        tk.Label(self, text="Select or Enter Your YouTube API Key").pack(pady=10)
        
        frame = ttk.Frame(self)
        frame.pack(pady=5)
        
        # KEY SELECTION COMBOBOX
        self.api_key_var = tk.StringVar(value=self.controller.api_key)
        self.keys = ConfigManager.get_available_api_keys()
        
        self.api_key_combo = ttk.Combobox(frame, textvariable=self.api_key_var, values=self.keys, width=47)
        self.api_key_combo.pack(side="left", padx=5)
        # Bind select event to auto-check status? Or purely manual?
        # Let's simple bind changes to reset status or check on button
        
        # STATUS INDICATOR (Circle)
        self.status_canvas = tk.Canvas(frame, width=20, height=20, highlightthickness=0)
        self.status_canvas.pack(side="left", padx=5)
        self.status_circle = self.status_canvas.create_oval(2, 2, 18, 18, fill="gray", outline="")

        # Action Buttons Frame
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="Validate Key", command=self.validate_api_key).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Add to List", command=self.add_key_to_list).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Auto Select Valid Key", command=self.auto_select_key).pack(side="left", padx=5)

        ttk.Label(self, text="(New keys are saved to your list automatically when you Save Settings)", 
                  foreground="gray", font=("Arial", 8)).pack(pady=2)

    def add_key_to_list(self):
        """Manually add the current key to the .env list."""
        key = self.api_key_var.get().strip()
        if not key:
            messagebox.showerror("Error", "Please enter a key to add.")
            return
        
        ConfigManager.add_to_env_keys(key)
        self.keys = ConfigManager.get_available_api_keys()
        self.api_key_combo['values'] = self.keys
        messagebox.showinfo("Success", "Key added to your available list.")

    def _create_folder_section(self):
        """Create the folder selection section."""
        tk.Label(self, text="Select Default Download Folder").pack(pady=10)
        self.folder_var = tk.StringVar(value=self.controller.default_folder)
        tk.Entry(self, textvariable=self.folder_var, width=50, state="readonly").pack(pady=5)
        tk.Button(self, text="Browse", command=self.browse_folder).pack(pady=5)

    def _create_save_button(self):
        """Create the save settings button."""
        tk.Button(self, text="Save Settings", command=self.save_settings).pack(pady=10)

    def browse_folder(self):
        """Browse and select a default download folder."""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)

    def save_settings(self):
        """Save API key and default download folder."""
        api_key = self.api_key_var.get().strip()
        default_folder = self.folder_var.get().strip()
        
        if not api_key:
            messagebox.showerror("Error", "Please enter a YouTube API key.")
            return
            
        if not default_folder:
            messagebox.showerror("Error", "Please select a download folder.")
            return
            
        # Add to .env if new
        ConfigManager.add_to_env_keys(api_key)
        
        # Validate status for the message
        status = ConfigManager.validate_api_key(api_key)
        self._update_status_indicator(status)
        
        if status == "INVALID":
             if not messagebox.askyesno("Warning", "This API key appears INVALID. Save anyway?"):
                  return
        elif status == "QUOTA":
             messagebox.showwarning("Warning", "This API key has exceeded its QUOTA. Saving anyway.")
             
        self.controller.update_config(api_key, default_folder)
        
        # Success message with status info
        status_msg = {
            "VALID": "is VALID and ready.",
            "QUOTA": "is valid but QUOTA EXCEEDED.",
            "INVALID": "appears INVALID.",
            "ERROR": "had a network error during validation."
        }.get(status, "status is unknown.")
        
        messagebox.showinfo("Success", f"Settings saved successfully.\nAPI Key {status_msg}")

        # Navigate back to MainPage
        try:
            from src.pages.main.main_page import MainPage
            self.controller.show_frame(MainPage)
        except Exception as e:
            try:
                from pages.main.main_page import MainPage
                self.controller.show_frame(MainPage)
            except Exception:
                # Last resort: just try to find it in the frames dict
                for page_class in self.controller.frames:
                    if page_class.__name__ == "MainPage":
                        self.controller.show_frame(page_class)
                        break

    def validate_api_key(self):
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter a YouTube API key.")
            self._update_status_indicator("INVALID")
            return
        
        status = ConfigManager.validate_api_key(api_key)
        self._update_status_indicator(status)
        
        if status == "VALID":
            messagebox.showinfo("Success", "API key is VALID and ready.")
        elif status == "QUOTA":
            messagebox.showwarning("Warning", "API key is valid but QUOTA EXCEEDED.")
        elif status == "INVALID":
            messagebox.showerror("Error", "API key is INVALID.")
        else:
            messagebox.showerror("Error", "Network ERROR during validation.")

    def auto_select_key(self):
        """Iterates through known keys to find a valid one."""
        keys = ConfigManager.get_available_api_keys()
        found_valid = False
        messagebox.showinfo("Auto Select", "Checking available keys... This might take a moment.")
        
        for k in keys:
            if not k:
                continue
            res = ConfigManager.validate_api_key(k)
            if res == "VALID":
                self.api_key_var.set(k)
                self._update_status_indicator("VALID")
                messagebox.showinfo("Success", f"Found valid key: ...{k[-4:]}")
                found_valid = True
                break
            elif res == "QUOTA":
                # Keep looking but maybe remember this one?
                pass
        
        if not found_valid:
            messagebox.showwarning("Result", "No VALID keys found with available quota.")
            self._update_status_indicator("INVALID")

    def _update_status_indicator(self, status):
        color = "gray"
        if status == "VALID":
            color = "green"
        elif status == "QUOTA":
            color = "orange"
        elif status == "INVALID":
            color = "red"
        elif status == "ERROR":
            color = "red"
        self.status_canvas.itemconfig(self.status_circle, fill=color)

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
