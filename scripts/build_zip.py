import os
import zipfile
import shutil
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
RELEASE_DIR = PROJECT_DIR / "release"
VERSION_FILE = PROJECT_DIR / "VERSION"

# Ensure release directory exists
RELEASE_DIR.mkdir(exist_ok=True)

# Read version
if VERSION_FILE.exists():
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
else:
    version = "1.0.1"

zip_name = f"whisperMe-v{version}.zip"
zip_path = RELEASE_DIR / zip_name

print(f"Starting packaging for whisperMe v{version}...")
print(f"Target: {zip_path}")

# White-list of directories and files to include
INCLUDES = {
    "backend": True,  # Keep entire backend dir
    "frontend/dist": True,  # Keep compiled frontend only
    "scripts": True,  # Keep scripts dir
    "assets": True,  # Keep assets dir
    "docs": True,  # Keep docs dir
    "config.example.json": False,
    "prompt.json": False,
    "start.bat": False,
    "stop.bat": False,
    "VERSION": False,
    "README.md": False,
    "AGENT.md": False,
}

# Exclude list for subfolders/files
EXCLUDE_PATTERNS = [
    "__pycache__",
    ".pytest_cache",
    ".git",
    "venv",
    "node_modules",
]

def should_exclude(path_str):
    for pattern in EXCLUDE_PATTERNS:
        if pattern in path_str.split(os.sep) or pattern in path_str.split("/"):
            return True
    return False

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
    # 1. Add individual files
    for name, is_dir in INCLUDES.items():
        src_path = PROJECT_DIR / name
        if not src_path.exists():
            print(f"Warning: {name} does not exist, skipping.")
            continue
            
        if not is_dir:
            # It's a file
            zipf.write(src_path, name)
            print(f"Added file: {name}")
        else:
            # It's a directory
            for root, dirs, files in os.walk(src_path):
                # Filter out excluded directories in-place
                dirs[:] = [d for d in dirs if not should_exclude(d)]
                
                for file in files:
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(PROJECT_DIR)
                    if should_exclude(str(rel_path)):
                        continue
                    zipf.write(file_path, rel_path)
            print(f"Added directory: {name}")

print(f"Successfully packaged whisperMe into {zip_path} ({os.path.getsize(zip_path) / (1024*1024):.2f} MB)")
