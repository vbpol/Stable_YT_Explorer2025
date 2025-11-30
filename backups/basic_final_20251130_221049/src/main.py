import os
import sys
import subprocess

def main():
    base = os.path.dirname(__file__)
    backup_root = os.path.abspath(os.path.join(base, "..", "backups", "basic_final_stable"))
    cmd = [sys.executable, "-m", "src.main"]
    try:
        print(f"[Launcher] Starting stable runtime at {backup_root}")
        proc = subprocess.Popen(cmd, cwd=backup_root)
        rc = proc.wait()
        print(f"[Launcher] Stable runtime exited with code {rc}")
        if rc != 0:
            try:
                from src.config_manager import ConfigManager
                ConfigManager.save_last_mode('videos')
                try:
                    lm_txt = os.path.join(backup_root, 'data', 'last_mode.txt')
                    with open(lm_txt, 'w', encoding='utf-8') as f:
                        f.write('videos')
                except Exception:
                    pass
            except Exception:
                pass
            import tkinter as tk
            from src.youtube_app import YouTubeApp
            print("[Launcher] Stable runtime crashed; switching to current runtime (Videos mode)")
            root = tk.Tk()
            app = YouTubeApp(root)
            try:
                root.mainloop()
            except KeyboardInterrupt:
                try:
                    root.destroy()
                except Exception:
                    pass
    except Exception as e:
        print(f"[Launcher] Failed to start stable runtime: {e}. Falling back to current runtime.")
        try:
            from src.config_manager import ConfigManager
            ConfigManager.save_last_mode('videos')
            try:
                lm_txt = os.path.join(backup_root, 'data', 'last_mode.txt')
                with open(lm_txt, 'w', encoding='utf-8') as f:
                    f.write('videos')
            except Exception:
                pass
        except Exception:
            pass
        import tkinter as tk
        from src.youtube_app import YouTubeApp
        root = tk.Tk()
        app = YouTubeApp(root)
        try:
            root.mainloop()
        except KeyboardInterrupt:
            try:
                root.destroy()
            except Exception:
                pass

if __name__ == "__main__":
    main()
