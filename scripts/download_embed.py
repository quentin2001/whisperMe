import urllib.request
import zipfile
import io
import os
import glob
import sys

def main():
    pyver = "3.12.4"
    url = f"https://www.python.org/ftp/python/{pyver}/python-{pyver}-embed-amd64.zip"
    dest = "release/whisperMe/python"
    
    print(f"Creating directory: {dest}")
    os.makedirs(dest, exist_ok=True)
    
    print(f"Downloading Python embed from: {url}")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            data = r.read()
    except Exception as e:
        print(f"Error downloading Python: {e}")
        sys.exit(1)
        
    print("Extracting ZIP file...")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            z.extractall(dest)
    except Exception as e:
        print(f"Error extracting ZIP: {e}")
        sys.exit(1)
        
    print("Enabling site-packages...")
    pth_files = glob.glob(os.path.join(dest, "*._pth"))
    if pth_files:
        pth_file = pth_files[0]
        try:
            with open(pth_file, 'r', encoding='utf-8') as f:
                content = f.read()
            content = content.replace('#import site', 'import site')
            with open(pth_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Successfully modified: {pth_file}")
        except Exception as e:
            print(f"Error modifying ._pth file: {e}")
            sys.exit(1)
    else:
        print("Warning: No ._pth file found!")
        
    print("Python embed setup completed successfully!")

if __name__ == "__main__":
    main()
