from tkinter import LabelFrame

class BaseSection(LabelFrame):
    def __init__(self, main_page, text=""):
        super().__init__(main_page, text=text)
        self.main_page = main_page
        self.controller = main_page.controller
        self.setup_gui()

    def setup_gui(self):
        """Override this method in child classes"""
        pass 