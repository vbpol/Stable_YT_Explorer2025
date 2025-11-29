import os
import subprocess
import sys
import venv
import json
import importlib
import re

# Ensure required packages are installed before importing them
def ensure_package_installed(package_name):
    """Install a package if it is not already installed."""
    try:
        importlib.import_module(package_name)
    except ImportError:
        print(f"Package '{package_name}' not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"Package '{package_name}' installed successfully.")

# Ensure pandas is installed
ensure_package_installed("pandas")

# Now import pandas and other modules
import pandas as pd

def validate_dependencies():
    """Validate that all required packages are installed."""
    try:
        # Read required packages from requirements.txt
        with open("requirements.txt", "r") as f:
            required_packages = {
                re.split(r"[=<>]", line.strip())[0].lower()
                for line in f if line.strip() and not line.startswith("#")
            }
        
        # Get installed packages from pip freeze
        installed_packages = {
            re.split(r"[=<>]", line.strip())[0].lower()
            for line in subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True).stdout.splitlines()
        }
        
        # Identify missing packages
        missing_packages = required_packages - installed_packages
        if missing_packages:
            print(f"Missing required packages: {', '.join(missing_packages)}")
            print("Please run: pip install -r requirements.txt")
            sys.exit(1)
    except Exception as e:
        print(f"Error validating dependencies: {e}")
        sys.exit(1)

# Validate dependencies before running the rest of the script
validate_dependencies()

REQUIRED_PACKAGES = {
    'yt_dlp': 'yt-dlp',
    'google_api_python_client': 'google-api-python-client',
    'python_vlc': 'python-vlc',
    'isodate': 'isodate',
    'pandas': 'pandas'
}

def validate_requirements_file():
    """Validate requirements.txt exists and contains all required packages."""
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read().splitlines()
        
        # Clean requirements list (remove comments and empty lines)
        requirements = [
            r.split('#')[0].strip() 
            for r in requirements 
            if r.strip() and not r.strip().startswith('#')
        ]
        
        # Convert requirements to a standardized format for comparison
        req_dict = {}
        for req in requirements:
            match = re.match(r'^([a-zA-Z0-9-_.]+)(?:[=<>]+.*)?$', req)
            if match:
                req_dict[match.group(1).lower()] = req

        # Check for missing required packages
        missing_packages = []
        for import_name, pkg_name in REQUIRED_PACKAGES.items():
            if pkg_name.lower() not in req_dict:
                missing_packages.append(pkg_name)

        if missing_packages:
            print("Missing required packages in requirements.txt:", ', '.join(missing_packages))
            print("Adding missing packages to requirements.txt...")
            with open('requirements.txt', 'a') as f:
                for pkg in missing_packages:
                    f.write(f"{pkg}\n")
            print("Updated requirements.txt. Please re-run the script.")
            sys.exit(1)

        return True

    except FileNotFoundError:
        print("requirements.txt not found. Creating a new one...")
        with open('requirements.txt', 'w') as f:
            for pkg in REQUIRED_PACKAGES.values():
                f.write(f"{pkg}\n")
        print("requirements.txt created. Please re-run the script.")
        sys.exit(1)

def create_venv():
    """Create a virtual environment in the app root."""
    app_root = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(app_root, 'venv')
    
    print(f"Creating virtual environment in {venv_dir}...")
    venv.create(venv_dir, with_pip=True)
    print("Virtual environment created.")
    return venv_dir

def install_requirements(venv_dir):
    """Install required packages from requirements.txt."""
    print("Installing dependencies...")
    pip_path = os.path.join(venv_dir, 'Scripts', 'pip.exe')
    try:
        subprocess.check_call([pip_path, 'install', '-r', 'requirements.txt'])
        print("Dependencies installed.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

def validate_venv():
    """Validate virtual environment exists and is properly set up."""
    app_root = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(app_root, 'venv')
    
    if not os.path.exists(venv_dir):
        venv_dir = create_venv()
        install_requirements(venv_dir)
    
    # Verify critical venv components
    required_paths = [
        os.path.join(venv_dir, 'Scripts', 'python.exe'),
        os.path.join(venv_dir, 'Scripts', 'activate.bat'),
        os.path.join(venv_dir, 'Scripts', 'pip.exe')
    ]
    
    for path in required_paths:
        if not os.path.exists(path):
            print(f"Invalid virtual environment - missing: {path}")
            sys.exit(1)
    
    validate_dependencies(venv_dir)
    return True

def validate_dependencies(venv_dir):
    """Check if all required packages are installed and importable."""
    missing_packages = []
    for import_name, pkg_name in REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing_packages.append(pkg_name)
    
    if missing_packages:
        print("Missing required packages:", ', '.join(missing_packages))
        print("Installing missing packages...")
        install_requirements(venv_dir)
    
    return True

def validate_api_key():
    """Validate that API key exists and has correct format."""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            
        api_key = config.get('api_key', '').strip()
        if not api_key:
            print("API key not found in config.json")
            sys.exit(1)
            
        # Basic API key format validation
        if not (len(api_key) > 20 and api_key.startswith('AIza')):
            print("Invalid API key format in config.json")
            sys.exit(1)
            
        return True
    except FileNotFoundError:
        print("config.json not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Invalid config.json format")
        sys.exit(1)

def run_app():
    """Run the application using run_app.bat."""
    try:
        app_root = os.path.dirname(os.path.abspath(__file__))
        bat_path = os.path.join(app_root, 'run_app.bat')
        
        if not os.path.exists(bat_path):
            print(f"Batch file not found: {bat_path}")
            sys.exit(1)
            
        subprocess.check_call([bat_path], shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running the application: {e}")
        sys.exit(1)

class TextFileComparator:
    """Class to compare text files and verify content using pandas."""
    
    @staticmethod
    def extract_package_names(file_path):
        """Extract package names from a text file."""
        try:
            with open(file_path, "r") as f:
                return [
                    re.split(r"[=<>]", line.strip())[0].lower()
                    for line in f if line.strip() and not line.startswith("#")
                ]
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            sys.exit(1)

    @staticmethod
    def compare_files(file1, file2):
        """Compare two files and verify if all items in file1 exist in file2 using pandas."""
        file1_packages = TextFileComparator.extract_package_names(file1)
        file2_packages = TextFileComparator.extract_package_names(file2)
        
        # Create pandas DataFrames for comparison
        df1 = pd.DataFrame(file1_packages, columns=["Package"])
        df2 = pd.DataFrame(file2_packages, columns=["Package"])
        
        # Find missing packages
        missing_packages = df1[~df1["Package"].isin(df2["Package"])]
        if not missing_packages.empty:
            print("Missing packages in packages.txt:")
            print(missing_packages.to_string(index=False))
            return False
        print(f"All packages in {file1} are available in {file2}.")
        return True

def main():
    # Validate everything before running
    if all([
        validate_requirements_file(),
        validate_venv(),
        validate_api_key()
    ]):
        run_app()

if __name__ == "__main__":
    main()

    # Example usage of TextFileComparator
    requirements_file = "requirements.txt"
    packages_file = "packages.txt"
    TextFileComparator.compare_files(requirements_file, packages_file)

print("Python executable:", sys.executable)
print("Python path:", sys.path)
