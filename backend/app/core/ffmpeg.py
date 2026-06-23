"""
FFmpeg 自动发现与路径管理模块
提供统一的 FFmpeg 路径发现、版本检测、fallback 逻辑。
所有需要调用 FFmpeg 的模块应通过此模块获取路径，避免重复的 try/fallback 代码。
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path


# 常见 FFmpeg 安装位置扫描列表（按优先级排序）
_COMMON_PATHS = []

if sys.platform == "win32":
    # WinGet
    _COMMON_PATHS.extend([
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages"),
        os.path.expandvars(r"%PROGRAMFILES%\ffmpeg\bin"),
        os.path.expandvars(r"%USERPROFILE%\scoop\shims"),
        os.path.expandvars(r"%USERPROFILE%\scoop\apps\ffmpeg\current\bin"),
        os.path.expandvars(r"%PROGRAMFILES%\Chocolatey\bin"),
    ])
else:
    # macOS / Linux
    _COMMON_PATHS.extend([
        "/opt/homebrew/bin",
        "/usr/local/bin",
        "/usr/bin",
        "/snap/bin",
    ])


def find_ffmpeg() -> str | None:
    """
    自动发现可用的 ffmpeg 可执行文件路径。
    优先级：
      1. 用户在 config.json 中手动指定的路径（存在且可执行）
      2. shutil.which("ffmpeg") — 系统 PATH
      3. 常见安装位置扫描
    Returns:
        ffmpeg 可执行文件的绝对路径，或 None（未找到）
    """
    # 1. 检查 config 中是否有用户手动指定的路径
    try:
        from app.config import config as app_config
        user_path = app_config.get("ffmpeg_path", "").strip()
        if user_path and os.path.isfile(user_path):
            try:
                result = subprocess.run(
                    [user_path, "-version"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    timeout=5,
                    creationflags=0x08000000 if sys.platform == "win32" else 0
                )
                if result.returncode == 0:
                    return user_path
            except Exception:
                pass
    except Exception:
        pass

    # 2. shutil.which — 系统 PATH
    which_path = shutil.which("ffmpeg")
    if which_path:
        return os.path.abspath(which_path)

    # 3. 常见安装位置扫描
    for base_dir in _COMMON_PATHS:
        if not os.path.isdir(base_dir):
            continue
        # WinGet 目录需要递归搜索（子目录名含版本号）
        if "WinGet" in base_dir:
            try:
                for entry in os.scandir(base_dir):
                    if entry.is_dir() and "ffmpeg" in entry.name.lower():
                        candidate = os.path.join(entry.path, "bin", "ffmpeg.exe")
                        if os.path.isfile(candidate):
                            return candidate
            except Exception:
                continue
        else:
            candidate = os.path.join(base_dir, "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
            if os.path.isfile(candidate):
                return candidate

    return None


def find_ffmpeg_dir() -> str | None:
    """返回 ffmpeg 所在目录（给 yt-dlp 的 ffmpeg_location 参数用）"""
    ffmpeg_path = find_ffmpeg()
    if ffmpeg_path:
        return os.path.dirname(ffmpeg_path)
    return None


def get_ffmpeg_info(ffmpeg_path: str = None) -> dict:
    """
    执行 ffmpeg -version，返回版本信息。
    Returns:
        {"available": bool, "path": str|None, "version": str|None, "error": str|None}
    """
    path = ffmpeg_path or find_ffmpeg()
    if not path:
        return {"available": False, "path": None, "version": None, "error": "FFmpeg not found"}

    try:
        result = subprocess.run(
            [path, "-version"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=5,
            creationflags=0x08000000 if sys.platform == "win32" else 0
        )
        output = result.stdout.decode("utf-8", errors="ignore")
        # 只提取版本号数字: "ffmpeg version 8.1.1-full_build" -> "8.1.1"
        version_line = output.split("\n")[0] if output else ""
        version = version_line.strip()
        import re
        ver_match = re.search(r'(\d+\.\d+[\.\d]*)', version)
        if ver_match:
            version = ver_match.group(1)
        return {
            "available": result.returncode == 0,
            "path": path,
            "version": version,
            "error": None if result.returncode == 0 else result.stderr.decode("utf-8", errors="ignore")[:200]
        }
    except FileNotFoundError:
        return {"available": False, "path": path, "version": None, "error": f"File not found: {path}"}
    except Exception as e:
        return {"available": False, "path": path, "version": None, "error": str(e)}


def get_install_hint() -> str:
    """返回当前平台的 FFmpeg 安装指引"""
    if sys.platform == "win32":
        return (
            "Windows 安装 FFmpeg:\n"
            "  winget install Gyan.FFmpeg\n"
            "  或从 https://ffmpeg.org/download.html 下载"
        )
    elif sys.platform == "darwin":
        return (
            "macOS 安装 FFmpeg:\n"
            "  brew install ffmpeg"
        )
    else:
        return (
            "Linux 安装 FFmpeg:\n"
            "  sudo apt install ffmpeg  (Debian/Ubuntu)\n"
            "  sudo dnf install ffmpeg  (Fedora)"
        )
