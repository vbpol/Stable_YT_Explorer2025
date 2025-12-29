import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox

class BuildHandler:
    """Handles EXE and Portable building logic for the MainPage."""
    
    def __init__(self, main_page):
        self.main_page = main_page

    def build_exe_windows(self):
        """Build a single EXE file using PyInstaller."""
        mp = self.main_page
        try:
            base_src = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            root_dir = os.path.dirname(base_src)
            cand_root = os.path.join(root_dir, "scripts", "build_exe.ps1")
            cand_src = os.path.join(base_src, "scripts", "build_exe.ps1")
            script_path = cand_root if os.path.exists(cand_root) else cand_src
            
            if not os.path.exists(script_path):
                messagebox.showerror("Error", f"Build script not found: {script_path}")
                return
                
            project_root = os.path.dirname(os.path.dirname(script_path))
            dist_dir = os.path.join(project_root, "dist")
            
            top = tk.Toplevel(mp)
            top.title("Building EXE")
            frm = ttk.Frame(top)
            frm.pack(fill="both", expand=True, padx=10, pady=10)
            
            lbl = ttk.Label(frm, text="Building packaged EXE...")
            lbl.pack(anchor="w")
            
            pb = ttk.Progressbar(frm, mode="indeterminate", length=320)
            pb.pack(fill="x", pady=6)
            pb.start(10)
            
            txt = tk.Text(frm, height=18, width=80)
            sb = ttk.Scrollbar(frm, orient="vertical", command=txt.yview)
            txt.configure(yscrollcommand=sb.set)
            txt.pack(side="left", fill="both", expand=True)
            sb.pack(side="right", fill="y")
            
            # Disable Search during build
            mp._build_in_progress = True
            try:
                mp.search.search_button.configure(state="disabled")
                mp.status_bar.configure(text="Build in progress... Search disabled.")
            except Exception: pass

            btns = ttk.Frame(frm)
            btns.pack(fill="x", pady=8)
            run_btn = ttk.Button(btns, text="Run EXE")
            run_btn.pack(side="left")
            open_btn = ttk.Button(btns, text="Open EXE Folder")
            open_btn.pack(side="left", padx=6)
            close_btn = ttk.Button(btns, text="Close", command=top.destroy)
            close_btn.pack(side="right")
            
            open_btn.configure(state="disabled")
            run_btn.configure(state="disabled")
            
            def _open_dist():
                try:
                    if sys.platform == "win32":
                        os.startfile(dist_dir)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", dist_dir])
                    else:
                        subprocess.run(["xdg-open", dist_dir])
                except Exception: pass
                
            open_btn.configure(command=_open_dist)
            
            def _run_exe():
                try:
                    exe_path_local = os.path.join(dist_dir, "YouTubePlaylistExplorer.exe")
                    if sys.platform == "win32":
                        os.startfile(exe_path_local)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", exe_path_local])
                    else:
                        subprocess.run([exe_path_local])
                except Exception: pass
                
            run_btn.configure(command=_run_exe)
            
            def _append(s):
                try:
                    txt.insert("end", s)
                    txt.see("end")
                except Exception: pass
                
            def _done(ok):
                try:
                    pb.stop()
                    lbl.configure(text=("Build completed" if ok else "Build failed"))
                    if ok:
                        open_btn.configure(state="normal")
                        run_btn.configure(state="normal")
                    
                    # Re-enable Search after build
                    mp._build_in_progress = False
                    try:
                        mp.search.search_button.configure(state="normal")
                        mp.status_bar.configure(text="Build " + ("completed" if ok else "failed"))
                    except Exception: pass
                except Exception: pass
                
            def _worker():
                ok = False
                try:
                    venv_dir = os.path.join(project_root, ".venv")
                    if not os.path.exists(venv_dir):
                        subprocess.run([sys.executable, "-m", "venv", venv_dir], cwd=project_root, check=True)
                    vpy = os.path.join(venv_dir, "Scripts", "python.exe")
                    if not os.path.exists(vpy):
                        vpy = os.path.join(venv_dir, "bin", "python")
                        
                    def runp(args):
                        p = subprocess.run(args, cwd=project_root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                        mp.after(0, lambda s=p.stdout: _append(s))
                        return p.returncode
                        
                    runp([vpy, "-m", "pip", "install", "--upgrade", "pip"])
                    runp([vpy, "-m", "pip", "install", "pyinstaller"])
                    req_path = os.path.join(project_root, "requirements.txt")
                    if os.path.exists(req_path):
                        runp([vpy, "-m", "pip", "install", "-r", req_path])
                        
                    entry = os.path.join(project_root, "src", "main.py")
                    dist = os.path.join(project_root, "dist")
                    work = os.path.join(project_root, "build")
                    os.makedirs(dist, exist_ok=True)
                    os.makedirs(work, exist_ok=True)
                    
                    args = [
                        vpy, "-m", "PyInstaller",
                        "--onefile", "--windowed",
                        "--name", "YouTubePlaylistExplorer",
                        "--distpath", dist, "--workpath", work,
                        "--hidden-import", "googleapiclient.discovery",
                        "--hidden-import", "googleapiclient.errors",
                        "--hidden-import", "isodate",
                        "--hidden-import", "vlc",
                        "--hidden-import", "yt_dlp",
                        entry
                    ]
                    r = subprocess.run(args, cwd=project_root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                    mp.after(0, lambda s=r.stdout: _append(s))
                    exe = os.path.join(dist, "YouTubePlaylistExplorer.exe")
                    ok = os.path.exists(exe)
                    if ok:
                        try:
                            run_cmd = os.path.join(dist, "Run-YouTubePlaylistExplorer.cmd")
                            with open(run_cmd, "w", encoding="ascii") as f:
                                f.write("@echo off\r\n")
                                f.write("setlocal\r\n")
                                for env in ("PYTHONHOME","PYTHONPATH","PYTHONUSERBASE","SSL_CERT_FILE","REQUESTS_CA_BUNDLE"):
                                    f.write(f"set {env}=\r\n")
                                f.write("set PYTHONUTF8=1\r\n")
                                f.write("start \"\" \"%~dp0YouTubePlaylistExplorer.exe\"\r\n")
                        except Exception: pass
                except Exception as e:
                    err_msg = str(e)
                    mp.after(0, lambda s=err_msg: _append(s + "\n"))
                    ok = False
                finally:
                    mp.after(0, lambda: _done(ok))
                    
            threading.Thread(target=_worker, daemon=True).start()
        except Exception: pass

    def build_portable_windows(self):
        """Build a portable folder using PyInstaller."""
        mp = self.main_page
        try:
            base_src = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            root_dir = os.path.dirname(base_src)
            cand_root = os.path.join(root_dir, "scripts", "build_exe.ps1")
            cand_src = os.path.join(base_src, "scripts", "build_exe.ps1")
            script_path = cand_root if os.path.exists(cand_root) else cand_src
            
            if not os.path.exists(script_path):
                messagebox.showerror("Error", f"Build script not found: {script_path}")
                return
                
            project_root = os.path.dirname(os.path.dirname(script_path))
            dist_dir = os.path.join(project_root, "dist", "YouTubePlaylistExplorer")
            
            top = tk.Toplevel(mp)
            top.title("Building Portable")
            frm = ttk.Frame(top)
            frm.pack(fill="both", expand=True, padx=10, pady=10)
            
            lbl = ttk.Label(frm, text="Building portable folder...")
            lbl.pack(anchor="w")
            
            pb = ttk.Progressbar(frm, mode="indeterminate", length=320)
            pb.pack(fill="x", pady=6)
            pb.start(10)
            
            txt = tk.Text(frm, height=18, width=80)
            sb = ttk.Scrollbar(frm, orient="vertical", command=txt.yview)
            txt.configure(yscrollcommand=sb.set)
            txt.pack(side="left", fill="both", expand=True)
            sb.pack(side="right", fill="y")

            # Disable Search during build
            mp._build_in_progress = True
            try:
                mp.search.search_button.configure(state="disabled")
                mp.status_bar.configure(text="Build in progress... Search disabled.")
            except Exception: pass

            btns = ttk.Frame(frm)
            btns.pack(fill="x", pady=8)
            run_btn = ttk.Button(btns, text="Run EXE")
            run_btn.pack(side="left")
            open_btn = ttk.Button(btns, text="Open EXE Folder")
            open_btn.pack(side="left", padx=6)
            close_btn = ttk.Button(btns, text="Close", command=top.destroy)
            close_btn.pack(side="right")
            
            open_btn.configure(state="disabled")
            run_btn.configure(state="disabled")
            
            def _open_dist():
                try:
                    if sys.platform == "win32":
                        os.startfile(dist_dir)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", dist_dir])
                    else:
                        subprocess.run(["xdg-open", dist_dir])
                except Exception: pass
                
            open_btn.configure(command=_open_dist)
            
            def _run_exe():
                try:
                    exe_path = os.path.join(dist_dir, "YouTubePlaylistExplorer.exe")
                    if sys.platform == "win32":
                        os.startfile(exe_path)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", exe_path])
                    else:
                        subprocess.run([exe_path])
                except Exception: pass
                
            run_btn.configure(command=_run_exe)
            
            def _append(s):
                try:
                    txt.insert("end", s)
                    txt.see("end")
                except Exception: pass
                
            def _done(ok):
                try:
                    pb.stop()
                    lbl.configure(text=("Build completed" if ok else "Build failed"))
                    if ok:
                        open_btn.configure(state="normal")
                        run_btn.configure(state="normal")

                    # Re-enable Search after build
                    mp._build_in_progress = False
                    try:
                        mp.search.search_button.configure(state="normal")
                        mp.status_bar.configure(text="Build " + ("completed" if ok else "failed"))
                    except Exception: pass
                except Exception: pass
                
            def _worker():
                try:
                    ok = False
                    venv_dir = os.path.join(project_root, ".venv")
                    if not os.path.exists(venv_dir):
                        subprocess.run([sys.executable, "-m", "venv", venv_dir], cwd=project_root, check=True)
                    vpy = os.path.join(venv_dir, "Scripts", "python.exe")
                    if not os.path.exists(vpy):
                        vpy = os.path.join(venv_dir, "bin", "python")
                        
                    def runp(args):
                        p = subprocess.run(args, cwd=project_root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                        mp.after(0, lambda s=p.stdout: _append(s))
                        return p.returncode
                        
                    runp([vpy, "-m", "pip", "install", "--upgrade", "pip"])
                    runp([vpy, "-m", "pip", "install", "pyinstaller"])
                    req_path = os.path.join(project_root, "requirements.txt")
                    if os.path.exists(req_path):
                        runp([vpy, "-m", "pip", "install", "-r", req_path])
                        
                    entry = os.path.join(project_root, "src", "main.py")
                    dist = os.path.join(project_root, "dist")
                    work = os.path.join(project_root, "build")
                    os.makedirs(dist, exist_ok=True)
                    os.makedirs(work, exist_ok=True)
                    
                    args = [
                        vpy, "-m", "PyInstaller",
                        "--onedir", "--windowed",
                        "--name", "YouTubePlaylistExplorer",
                        "--distpath", dist, "--workpath", work,
                        "--hidden-import", "googleapiclient.discovery",
                        "--hidden-import", "googleapiclient.errors",
                        "--hidden-import", "isodate",
                        "--hidden-import", "vlc",
                        "--hidden-import", "yt_dlp",
                        entry
                    ]
                    r = subprocess.run(args, cwd=project_root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                    mp.after(0, lambda s=r.stdout: _append(s))
                    target_dir = os.path.join(dist, "YouTubePlaylistExplorer")
                    ok = os.path.isdir(target_dir)
                    if ok:
                        try:
                            run_cmd = os.path.join(target_dir, "Run-App.cmd")
                            with open(run_cmd, "w", encoding="ascii") as f:
                                f.write("@echo off\r\n")
                                f.write("setlocal\r\n")
                                for env in ("PYTHONHOME","PYTHONPATH","PYTHONUSERBASE","SSL_CERT_FILE","REQUESTS_CA_BUNDLE"):
                                    f.write(f"set {env}=\r\n")
                                f.write("set PYTHONUTF8=1\r\n")
                                f.write("start \"\" \"%~dp0YouTubePlaylistExplorer.exe\"\r\n")
                        except Exception: pass
                except Exception as exc:
                    err_msg = str(exc)
                    mp.after(0, lambda s=err_msg: _append(s + "\n"))
                    ok = False
                finally:
                    mp.after(0, lambda: _done(ok))
                    
            threading.Thread(target=_worker, daemon=True).start()
        except Exception: pass
