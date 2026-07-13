import os
import sys
import tarfile
import urllib.request
import shutil

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    site_packages_dir = os.path.join(base_dir, 'python', 'Lib', 'site-packages')
    torch_dir = os.path.join(site_packages_dir, 'torch')
    
    if os.path.exists(torch_dir):
        print("[INFO] Dependencies already loaded.")
        sys.exit(0)
        
    url = os.environ.get('TEST_DEPS_URL', 'https://github.com/your/repo/releases/download/v1.0.0/whisperMe-Windows-Dependencies.tar.gz')
    
    tar_path = os.path.join(base_dir, 'deps.tar.gz')
    
    if url.startswith('http'):
        print(f"[INFO] Downloading dependencies from {url}...")
        def reporthook(blocknum, blocksize, totalsize):
            readsofar = blocknum * blocksize
            if totalsize > 0:
                percent = readsofar * 1e2 / totalsize
                s = "\r%5.1f%% %*d / %d" % (
                    percent, len(str(totalsize)), readsofar, totalsize)
                sys.stderr.write(s)
                if readsofar >= totalsize:
                    sys.stderr.write("\n")
        
        try:
            urllib.request.urlretrieve(url, tar_path, reporthook)
        except Exception as e:
            print(f"[ERROR] Failed to download dependencies: {e}")
            sys.exit(1)
    else:
        print(f"[INFO] Using local dependencies archive: {url}")
        try:
            shutil.copy(url, tar_path)
        except Exception as e:
            print(f"[ERROR] Failed to copy local dependencies: {e}")
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
    except OSError:
        pass

if __name__ == "__main__":
    main()
