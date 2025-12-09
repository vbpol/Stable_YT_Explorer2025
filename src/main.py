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
        try:
            import importlib
            import sys as _sys
            def _alias(name, target):
                try:
                    m = importlib.import_module(target)
                    _sys.modules[name] = m
                except Exception:
                    pass
            _alias('pages', 'src.pages')
            _alias('pages.main', 'src.pages.main')
            _alias('services', 'src.services')
            _alias('data', 'src.data')
            _alias('ui', 'src.ui')
            _alias('config_manager', 'src.config_manager')
            _alias('playlist', 'src.playlist')
        except Exception:
            pass
        from src.youtube_app import YouTubeApp
        import tkinter as tk
        root = tk.Tk()
        try:
            root.deiconify()
            root.lift()
        except Exception:
            pass
        YouTubeApp(root)
        try:
            root.mainloop()
        except KeyboardInterrupt:
            try:
                root.destroy()
            except Exception:
                pass
    except Exception as e:
        try:
            import traceback
            base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            logd = os.path.join(base, "logs")
            os.makedirs(logd, exist_ok=True)
            lp = os.path.join(logd, "launcher.log")
            with open(lp, "a", encoding="utf-8") as f:
                f.write("\n[error] " + str(e) + "\n")
                f.write(traceback.format_exc())
        except Exception:
            pass
        try:
            if sys.platform == "win32":
                import ctypes
                try:
                    ctypes.windll.user32.MessageBoxW(0, f"Failed to start: {e}", "YouTubePlaylistExplorer", 0x10)
                except Exception:
                    pass
        except Exception:
            pass

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
            YouTubeApp(root)
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
