import os
import zipfile
# Ensure project root is in sys.path so we can import scripts
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from scripts.build_release import archive_unix_app

def test_unix_sh_line_ending_conversion(tmp_path):
    # Setup test directories and files
    src_dir = tmp_path / "whisperMe_Unix"
    src_dir.mkdir()
    
    # 1. Shell script with CRLF endings
    sh_crlf = src_dir / "test_crlf.sh"
    sh_crlf.write_bytes(b"#!/bin/bash\r\necho 'hello'\r\n")
    
    # 2. Shell script with LF endings
    sh_lf = src_dir / "test_lf.sh"
    sh_lf.write_bytes(b"#!/bin/bash\necho 'world'\n")
    
    # 3. Non-shell file with CRLF endings (should NOT be converted)
    txt_crlf = src_dir / "test.txt"
    txt_crlf.write_bytes(b"some text\r\nother text\r\n")
    
    zip_path = tmp_path / "whisperMe-macOS.zip"
    
    # Run the archiving logic
    archive_unix_app(str(src_dir), str(zip_path))
    
    # Verify the contents of the generated ZIP file
    assert zip_path.exists()
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Check test_crlf.sh (should be converted to LF)
        assert "test_crlf.sh" in zf.namelist()
        info = zf.getinfo("test_crlf.sh")
        assert info.create_system == 3
        assert info.external_attr == (0o100755 << 16)
        content = zf.read("test_crlf.sh")
        assert b"\r\n" not in content
        assert content == b"#!/bin/bash\necho 'hello'\n"
        
        # Check test_lf.sh (should remain LF)
        assert "test_lf.sh" in zf.namelist()
        info = zf.getinfo("test_lf.sh")
        assert info.create_system == 3
        assert info.external_attr == (0o100755 << 16)
        content = zf.read("test_lf.sh")
        assert b"\r\n" not in content
        assert content == b"#!/bin/bash\necho 'world'\n"
        
        # Check test.txt (should retain CRLF)
        assert "test.txt" in zf.namelist()
        content = zf.read("test.txt")
        assert b"\r\n" in content
        assert content == b"some text\r\nother text\r\n"
