import os
import sys
import shutil
import subprocess
import urllib.request
import zipfile
import io
import glob
import tarfile

def run_cmd(cmd, cwd=None):
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True, shell=True)

def ignore_files(dir, contents):
    ignored = []
    for item in contents:
        if item in ['__pycache__', '.pytest_cache', 'venv', 'tests']:
            ignored.append(item)
        if item.startswith('whisperme.db'):
            ignored.append(item)
    return ignored

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    release_dir = os.path.join(base_dir, 'release')
    
    app_dir_win = os.path.join(release_dir, 'whisperMe_Windows')
    app_dir_unix = os.path.join(release_dir, 'whisperMe_Unix')
    
    # Clean release dir
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(app_dir_win, exist_ok=True)
    os.makedirs(app_dir_unix, exist_ok=True)
    
    # Build frontend
    frontend_dir = os.path.join(base_dir, 'frontend')
    print("Building frontend...")
    run_cmd(['npm', 'install'], cwd=frontend_dir)
    run_cmd(['npm', 'run', 'build'], cwd=frontend_dir)
    
    print("Copying common files...")
    for app_dir in [app_dir_win, app_dir_unix]:
        shutil.copytree(os.path.join(base_dir, 'backend'), os.path.join(app_dir, 'backend'), ignore=ignore_files)
        shutil.copytree(os.path.join(base_dir, 'frontend', 'dist'), os.path.join(app_dir, 'frontend', 'dist'))
        shutil.copytree(os.path.join(base_dir, 'scripts'), os.path.join(app_dir, 'scripts'), ignore=ignore_files)
        shutil.copy2(os.path.join(base_dir, 'README.md'), app_dir)
    
    # Windows specific
    shutil.copy2(os.path.join(base_dir, 'start.bat'), app_dir_win)
    
    # Unix specific
    shutil.copy2(os.path.join(base_dir, 'start.sh'), app_dir_unix)
    
    # Download Python embed for Windows
    pyver = "3.12.4"
    py_url = f"https://www.python.org/ftp/python/{pyver}/python-{pyver}-embed-amd64.zip"
    py_dest = os.path.join(app_dir_win, 'python')
    os.makedirs(py_dest, exist_ok=True)
    
    print(f"Downloading Python embed from {py_url}...")
    req = urllib.request.Request(py_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as r:
        data = r.read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(py_dest)
        
    # Modify ._pth
    pth_files = glob.glob(os.path.join(py_dest, "*._pth"))
    if pth_files:
        with open(pth_files[0], 'r', encoding='utf-8') as f:
            content = f.read()
        content = content.replace('#import site', 'import site')
        with open(pth_files[0], 'w', encoding='utf-8') as f:
            f.write(content)
            
    # Install dependencies
    temp_deps = os.path.join(base_dir, 'temp_deps')
    site_packages = os.path.join(temp_deps, 'site-packages')
    if os.path.exists(temp_deps):
        shutil.rmtree(temp_deps)
    os.makedirs(site_packages, exist_ok=True)
    
    print("Installing backend dependencies...")
    req_file = os.path.join(base_dir, 'backend', 'requirements.txt')
    run_cmd([sys.executable, '-m', 'pip', 'install', '-r', req_file, '-t', site_packages])
    
    # Prune dependencies
    print("Pruning dependencies...")
    shutil.rmtree(os.path.join(site_packages, 'torch', 'include'), ignore_errors=True)
    shutil.rmtree(os.path.join(site_packages, 'torch', 'test'), ignore_errors=True)
    shutil.rmtree(os.path.join(site_packages, 'numpy', 'tests'), ignore_errors=True)
    for lib_file in glob.glob(os.path.join(site_packages, 'torch', 'lib', '*.lib')):
        try:
            os.remove(lib_file)
        except OSError:
            pass
            
    for p in glob.glob(os.path.join(site_packages, '**', '__pycache__'), recursive=True):
        shutil.rmtree(p, ignore_errors=True)
        
    # Archive dependencies to deps/Dependencies.tar.gz for Windows
    deps_dir = os.path.join(app_dir_win, 'deps')
    os.makedirs(deps_dir, exist_ok=True)
    deps_tar = os.path.join(deps_dir, 'Dependencies.tar.gz')
    print(f"Archiving dependencies to {deps_tar}...")
    with tarfile.open(deps_tar, 'w:gz') as tar:
        tar.add(site_packages, arcname='site-packages')
        
    # Archive whisperMe Windows
    app_zip_win = os.path.join(release_dir, 'whisperMe-Windows.zip')
    print(f"Archiving app to {app_zip_win}...")
    with zipfile.ZipFile(app_zip_win, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(app_dir_win):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, app_dir_win)
                zf.write(file_path, arcname)
                
    # Archive whisperMe Unix
    app_zip_unix = os.path.join(release_dir, 'whisperMe-macOS-Linux.zip')
    print(f"Archiving app to {app_zip_unix}...")
    with zipfile.ZipFile(app_zip_unix, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(app_dir_unix):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, app_dir_unix)
                if file.endswith('.sh'):
                    zinfo = zipfile.ZipInfo.from_file(file_path, arcname)
                    zinfo.external_attr = 0o755 << 16
                    with open(file_path, 'rb') as f:
                        zf.writestr(zinfo, f.read())
                else:
                    zf.write(file_path, arcname)

    # Clean up temp_deps and intermediate folders
    shutil.rmtree(temp_deps, ignore_errors=True)
    shutil.rmtree(app_dir_win, ignore_errors=True)
    shutil.rmtree(app_dir_unix, ignore_errors=True)
    print("Build and release completed successfully!")

if __name__ == "__main__":
    main()
