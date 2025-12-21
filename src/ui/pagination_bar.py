import tkinter as tk
from tkinter import ttk

class PaginationBar(ttk.Frame):
    def __init__(self, parent, show_page_size=True, size_label="Videos per page:", sizes=("5","10","20","50")):
        super().__init__(parent)
        # Start hidden; becomes visible only when total_pages > 1
        self.page_size_var = tk.StringVar(value=sizes[1] if sizes else "10")
        if show_page_size:
            ttk.Label(self, text=size_label).pack(side="left", padx=5)
            cb = ttk.Combobox(self, textvariable=self.page_size_var, values=list(sizes), width=5, state="readonly")
            cb.pack(side="left", padx=5)
            cb.bind('<<ComboboxSelected>>', self._on_size)
        self.prev_btn = ttk.Button(self, text="Previous", state="disabled")
        self.prev_btn.pack(side="left", padx=5)
        self.page_indicator = ttk.Label(self, text="Page 1 of 1")
        self.page_indicator.pack(side="left", padx=10)
        self.next_btn = ttk.Button(self, text="Next", state="disabled")
        self.next_btn.pack(side="left", padx=5)
        self.total_label = ttk.Label(self, text="Total: 0")
        self.total_label.pack(side="left", padx=10)
        self._on_prev = None
        self._on_next = None
        self._on_size_cb = None
        self.prev_btn.configure(command=self._fire_prev)
        self.next_btn.configure(command=self._fire_next)
        self._visible = False
        self._page_index = 1
        self._total_pages = 1
        self._total_items = 0

    def bind_prev(self, fn):
        self._on_prev = fn

    def bind_next(self, fn):
        self._on_next = fn

    def bind_page_size(self, fn):
        self._on_size_cb = fn

    def _fire_prev(self):
        if callable(self._on_prev):
            self._on_prev()

    def _fire_next(self):
        if callable(self._on_next):
            self._on_next()

    def _on_size(self, _):
        if callable(self._on_size_cb):
            try:
                val = int(self.page_size_var.get())
            except Exception:
                val = None
            self._on_size_cb(val)

    def set_page_indicator(self, text):
        self.page_indicator.configure(text=text)

    def set_total_text(self, text):
        self.total_label.configure(text=text)

    def set_prev_enabled(self, enabled: bool):
        self.prev_btn["state"] = "normal" if enabled else "disabled"

    def set_next_enabled(self, enabled: bool):
        self.next_btn["state"] = "normal" if enabled else "disabled"

    def set_visible(self, visible: bool):
        try:
            visible = bool(visible)
            if visible and not self._visible:
                self.pack(fill="x")
            if (not visible) and self._visible:
                self.pack_forget()
            self._visible = visible
        except Exception:
            pass

    def set_page_info(self, index: int, has_prev: bool, has_next: bool, total_items: int):
        try:
            self._page_index = max(int(index or 1), 1)
        except Exception:
            self._page_index = 1
        try:
            self._total_items = max(int(total_items or 0), 0)
        except Exception:
            self._total_items = 0
        try:
            ps = int(self.page_size_var.get())
        except Exception:
            ps = 10
        try:
            total = int(self._total_items or 0)
        except Exception:
            total = 0
        try:
            from math import ceil
            total_pages = max(1, ceil(total / max(ps, 1)))
        except Exception:
            total_pages = 1
        self._total_pages = total_pages
        
        # Use provided flags if available, otherwise fallback to index logic
        enable_prev = has_prev if has_prev is not None else (self._page_index > 1)
        # For next, if has_next is explicit, use it. 
        # Note: sometimes total_pages is an estimate, so has_next is more reliable for APIs.
        enable_next = has_next if has_next is not None else (self._page_index < total_pages)

        try:
            self.set_prev_enabled(enable_prev)
        except Exception:
            pass
        try:
            self.set_next_enabled(enable_next)
        except Exception:
            pass
        try:
            # Format numbers with commas for readability
            total_pages_str = f"{total_pages:,}"
            total_items_str = f"{self._total_items:,}"
            self.page_indicator.configure(text=f"Page {self._page_index} of {total_pages_str}")
        except Exception:
            pass
        try:
            self.total_label.configure(text=f"Total: {total_items_str}")
        except Exception:
            pass
        try:
            self.set_visible(bool(total > max(ps, 1)))
        except Exception:
            pass
