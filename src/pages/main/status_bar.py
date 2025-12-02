from tkinter import Label
import tkinter as tk

class StatusBar(Label):
    def __init__(self, main_page):
        super().__init__(main_page)
        self.main_page = main_page
        self.controller = main_page.controller
        self.setup_gui()
        self._job_title = None

    def setup_gui(self):
        self.configure(text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)

    def set_progress_ratio(self, done: int, total: int):
        return

    def reset_progress(self):
        return

    def set_job_title(self, title: str):
        try:
            self._job_title = str(title or '').strip() or None
        except Exception:
            pass

    def clear_job_title(self):
        try:
            self._job_title = None
            self.configure(text="Ready")
        except Exception:
            pass
