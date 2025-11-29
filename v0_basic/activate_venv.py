import os
import sys

def activate_venv():
    """Activate virtual environment and return the activated environment variables."""
    # Get absolute paths
    app_root = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(app_root, 'venv')
    
    if not os.path.exists(venv_dir):
        print(f"Virtual environment not found at: {venv_dir}")
        sys.exit(1)

    # Set up environment variables for virtual environment
    env = os.environ.copy()
    env['VIRTUAL_ENV'] = venv_dir
    env['PATH'] = os.path.join(venv_dir, 'Scripts') + os.pathsep + env['PATH']
    
    # Remove PYTHONHOME if set
    if 'PYTHONHOME' in env:
        del env['PYTHONHOME']
    
    return env, venv_dir

if __name__ == "__main__":
    env, venv_dir = activate_venv()
    print(f"Virtual environment activated at: {venv_dir}")