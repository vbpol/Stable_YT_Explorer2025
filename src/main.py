import os
import sys
import subprocess
try:
    from .security import apply_security_tag
except Exception:
    def apply_security_tag(*args, **kwargs):
        return None

def _start_current_runtime():
    try:
        from src.youtube_app import YouTubeApp
        import tkinter as tk
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
        print(f"[Launcher] Failed to start current runtime: {e}")

def main():
    base = os.path.dirname(__file__)
    backup_root = os.path.abspath(os.path.join(base, "..", "backups", "basic_final_stable"))
    cmd = [sys.executable, "-m", "src.main"]
    use_stable = str(os.getenv("USE_STABLE_RUNTIME", "0")).strip().lower() not in ("0", "false", "no", "off")
    if not use_stable:
        try:
            apply_security_tag("src")
        except Exception:
            pass
        print("[Launcher] Starting current runtime (stable disabled)")
        _start_current_runtime()
        return
    try:
        print(f"[Launcher] Starting stable runtime at {backup_root}")
        proc = subprocess.Popen(cmd, cwd=backup_root)
        rc = proc.wait()
        print(f"[Launcher] Stable runtime exited with code {rc}")
        if rc != 0:
            try:
                apply_security_tag("src")
            except Exception:
                pass
            import tkinter as tk
            from src.youtube_app import YouTubeApp
            try:
                from src.config_manager import ConfigManager
                m = ConfigManager.load_last_mode() or ''
                print(f"[Launcher] Stable runtime crashed; switching to current runtime (mode: {m or 'auto'})")
            except Exception:
                print("[Launcher] Stable runtime crashed; switching to current runtime")
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
            apply_security_tag("src")
        except Exception:
            pass
        _start_current_runtime()

if __name__ == "__main__":
    main()
