import os

def create_project_structure():
    # Define the project structure
    structure = {
        'src': {
            'models': {},
            'views': {},
            'controllers': {},
            'config_manager.py': '',
            'main.py': ''
        },
        'tests': {},
        'docs': {},
        'requirements.txt': '',
        'README.md': '',
        'manage.py': ''
    }

    # Create the directories and files
    for folder, subfolders in structure.items():
        if isinstance(subfolders, dict):
            os.makedirs(folder, exist_ok=True)
            for subfolder in subfolders:
                if isinstance(subfolders[subfolder], dict):
                    os.makedirs(os.path.join(folder, subfolder), exist_ok=True)
                else:
                    open(os.path.join(folder, subfolder), 'w').close()
        else:
            open(folder, 'w').close()

    # Create __init__.py files for modules
    init_files = [
        'src/models/__init__.py',
        'src/views/__init__.py',
        'src/controllers/__init__.py',
    ]
    
    for init_file in init_files:
        os.makedirs(os.path.dirname(init_file), exist_ok=True)
        open(init_file, 'w').close()

    print("Project structure created successfully.")

if __name__ == "__main__":
    create_project_structure()