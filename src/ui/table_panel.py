import tkinter as tk
from tkinter import ttk
from .pagination_bar import PaginationBar
try:
    from src.config_manager import ConfigManager
except ModuleNotFoundError:
    from config_manager import ConfigManager

class TablePanel(ttk.Frame):
    def __init__(self, parent, columns, show_page_size=True, size_label="Rows per page:"):
        super().__init__(parent)
        self.pack(fill="both", expand=True)
        self.pagination = PaginationBar(self, show_page_size=show_page_size, size_label=size_label)
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(frame, columns=tuple(columns), show="headings")
        for c in columns:
            self.tree.heading(c, text=c)
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def update_visibility(self, row_count: int):
        try:
            thr = int(ConfigManager.get_ui_pagination_min_rows())
        except Exception:
            thr = 10
        try:
            self.pagination.set_visible((int(row_count or 0) > thr))
        except Exception:
            pass

    def update_pages(self, index: int, has_prev: bool, has_next: bool, total_items: int, row_count: int = None):
        try:
            self.pagination.set_page_info(index, has_prev, has_next, total_items)
        except Exception:
            pass
        try:
            rc = int(row_count) if row_count is not None else len(self.tree.get_children())
        except Exception:
            rc = 0
        try:
            thr = int(ConfigManager.get_ui_pagination_min_rows())
        except Exception:
            thr = 10
        try:
            should_show = (rc > thr) or (has_prev or has_next)
            self.pagination.set_visible(should_show)
        except Exception:
            pass
