from tkinter import Label
import tkinter as tk
from tkinter import ttk

class StatusBar(Label):
    def __init__(self, main_page):
        super().__init__(main_page)
        self.main_page = main_page
        self.controller = main_page.controller
        self.setup_gui()
        try:
            self._pb = ttk.Progressbar(self.master, orient="horizontal", length=160, mode="determinate")
            self._pb.pack(side=tk.RIGHT, padx=6)
        except Exception:
            self._pb = None

    def setup_gui(self):
        self.configure(text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)

    def set_progress_ratio(self, done: int, total: int):
        try:
            if not self._pb:
                return
            total = int(total or 0)
            done = int(done or 0)
            percent = 0 if total <= 0 else max(0, min(100, int(done * 100 / total)))
            self._pb['value'] = percent
            self.update_idletasks()
        except Exception:
            pass

    def reset_progress(self):
        try:
            if self._pb:
                self._pb['value'] = 0
        except Exception:
            pass
