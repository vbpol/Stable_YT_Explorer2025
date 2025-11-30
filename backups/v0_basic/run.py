import os
import subprocess
import sys

def activate_and_run():
    venv_dir = 'venv'
    project_root = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(project_root, 'src')

    if not os.path.exists(venv_dir):
        print(f"Virtual environment not found: {venv_dir}")
        sys.exit(1)

    if not os.path.exists(src_dir):
        print(f"Source directory not found: {src_dir}")
        sys.exit(1)

    env = os.environ.copy()
    env['PYTHONPATH'] = project_root

    try:
        if sys.platform == 'win32':
            cmd = f"cmd /c \"call {os.path.join(venv_dir, 'Scripts', 'activate.bat')} && python -m src.main\""
            subprocess.check_call(cmd, env=env, cwd=project_root, shell=True)
        else:
            cmd = f"bash -c 'source {os.path.join(venv_dir, 'bin', 'activate')} && python -m src.main'"
            subprocess.check_call(cmd, env=env, cwd=project_root, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running the application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    activate_and_run()