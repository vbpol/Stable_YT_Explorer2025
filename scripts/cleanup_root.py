import os
import shutil

def cleanup():
    app_root = os.getcwd()
    legacy_dir = os.path.join(app_root, "Legacy_Downloads")
    
    print(f"Cleaning up app root: {app_root}")
    print(f"Target directory: {legacy_dir}")
    
    if not os.path.exists(legacy_dir):
        os.makedirs(legacy_dir)
        
    count = 0
    for item in os.listdir(app_root):
        full_path = os.path.join(app_root, item)
        if not os.path.isdir(full_path):
            continue
            
        if item.startswith("Videos - ") or item.startswith("Playlist - "):
            target_path = os.path.join(legacy_dir, item)
            try:
                print(f"Moving {item}...")
                shutil.move(full_path, target_path)
                count += 1
            except Exception as e:
                print(f"Failed to move {item}: {e}")
                
    print(f"Done. Moved {count} folders to {legacy_dir}")

if __name__ == "__main__":
    cleanup()
