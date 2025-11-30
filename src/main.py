import os
import sys
import subprocess

def main():
    base = os.path.dirname(__file__)
    backup_root = os.path.abspath(os.path.join(base, "..", "backups", "basic_final_stable"))
    cmd = [sys.executable, "-m", "src.main"]
    try:
        subprocess.check_call(cmd, cwd=backup_root)
    except Exception:
        import tkinter as tk
        from src.youtube_app import YouTubeApp
        root = tk.Tk()
        app = YouTubeApp(root)
        root.mainloop()

if __name__ == "__main__":
    main()
