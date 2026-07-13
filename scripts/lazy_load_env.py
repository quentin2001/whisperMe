import os
import sys
import tarfile
import shutil

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    site_packages_dir = os.path.join(base_dir, 'python', 'Lib', 'site-packages')
    torch_dir = os.path.join(site_packages_dir, 'torch')
    
    if os.path.exists(torch_dir):
        print("[INFO] Dependencies already loaded.")
        sys.exit(0)
        
    tar_path = os.path.join(base_dir, 'deps', 'Dependencies.tar.gz')
    
    if not os.path.exists(tar_path):
        print(f"[ERROR] Dependencies archive not found at {tar_path}.")
        sys.exit(1)
            
    print("[INFO] Extracting dependencies...")
    try:
        with tarfile.open(tar_path, 'r:gz') as tar:
            if hasattr(tarfile, 'data_filter'):
                tar.extractall(path=os.path.join(base_dir, 'python', 'Lib'), filter='data')
            else:
                tar.extractall(path=os.path.join(base_dir, 'python', 'Lib'))
    except Exception as e:
        print(f"[ERROR] Failed to extract dependencies: {e}")
        sys.exit(1)
        
    print("[INFO] Extraction complete.")
    try:
        os.remove(tar_path)
        # Optionally remove the deps folder if empty
        os.rmdir(os.path.dirname(tar_path))
    except OSError:
        pass

if __name__ == "__main__":
    main()
