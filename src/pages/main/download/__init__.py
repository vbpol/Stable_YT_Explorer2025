"""
Download Package - Scalable OOP module for video downloads.

Exports:
    DownloadManager: Handles download execution with progress tracking
    DownloadOptionsDialog: Pre-download configuration UI
"""

from .manager import DownloadManager
from .options_dialog import DownloadOptionsDialog

__all__ = ['DownloadManager', 'DownloadOptionsDialog']
