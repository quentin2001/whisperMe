import os
import zipfile
import pytest

def mock_unix_archive_logic(app_dir_unix, app_zip_unix):
    with zipfile.ZipFile(app_zip_unix, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(app_dir_unix):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, app_dir_unix)
                if file.endswith('.sh'):
                    zinfo = zipfile.ZipInfo.from_file(file_path, arcname)
                    zinfo.external_attr = 0o755 << 16
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    # Ensure LF line endings in release package
                    content = content.replace(b'\r\n', b'\n')
                    zf.writestr(zinfo, content)
                else:
                    zf.write(file_path, arcname)

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
    mock_unix_archive_logic(str(src_dir), str(zip_path))
    
    # Verify the contents of the generated ZIP file
    assert zip_path.exists()
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Check test_crlf.sh (should be converted to LF)
        assert "test_crlf.sh" in zf.namelist()
        info = zf.getinfo("test_crlf.sh")
        assert info.external_attr == (0o755 << 16)
        content = zf.read("test_crlf.sh")
        assert b"\r\n" not in content
        assert content == b"#!/bin/bash\necho 'hello'\n"
        
        # Check test_lf.sh (should remain LF)
        assert "test_lf.sh" in zf.namelist()
        info = zf.getinfo("test_lf.sh")
        assert info.external_attr == (0o755 << 16)
        content = zf.read("test_lf.sh")
        assert b"\r\n" not in content
        assert content == b"#!/bin/bash\necho 'world'\n"
        
        # Check test.txt (should retain CRLF)
        assert "test.txt" in zf.namelist()
        content = zf.read("test.txt")
        assert b"\r\n" in content
        assert content == b"some text\r\nother text\r\n"
