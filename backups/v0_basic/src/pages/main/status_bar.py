from tkinter import Label
import tkinter as tk

class StatusBar(Label):
    def __init__(self, main_page):
        super().__init__(main_page)
        self.main_page = main_page
        self.controller = main_page.controller
        self.setup_gui()

    def setup_gui(self):
        self.configure(text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W) 