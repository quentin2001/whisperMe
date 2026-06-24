#!/usr/bin/env python3
"""
whisperMe 构建脚本
准备发布目录：前端编译 + 后端代码 + 启动器 + 依赖清单
"""
import os
import sys
import shutil
import subprocess
import json
from pathlib import Path

ROOT_DIR = Path(__file__).parent.resolve()
RELEASE_DIR = ROOT_DIR / "release" / "whisperMe"
FRONTEND_DIR = ROOT_DIR / "frontend"


def clean():
    """清理旧的构建产物"""
    release_parent = ROOT_DIR / "release"
    if release_parent.exists():
        print(f"🧹 清理旧构建: {release_parent}")
        try:
            shutil.rmtree(release_parent)
        except PermissionError:
            # 文件被占用时，尝试删除子目录
            for item in release_parent.iterdir():
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                except PermissionError:
                    print(f"  ⚠️ 跳过被占用的文件: {item.name}")


def build_frontend():
    """编译前端静态文件"""
    print(f"\n📦 编译前端...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=str(FRONTEND_DIR),
        shell=(sys.platform == "win32"),
    )
    if result.returncode != 0:
        print("❌ 前端编译失败")
        sys.exit(1)
    dist = FRONTEND_DIR / "dist"
    if not dist.exists():
        print("❌ 前端编译产物不存在: frontend/dist")
        sys.exit(1)
    print(f"✅ 前端编译完成: {dist}")


def copy_files():
    """复制必要文件到发布目录"""
    print(f"\n📂 复制文件到 {RELEASE_DIR}...")
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 前端静态文件
    src_dist = FRONTEND_DIR / "dist"
    dst_dist = RELEASE_DIR / "frontend" / "dist"
    if dst_dist.exists():
        shutil.rmtree(dst_dist)
    shutil.copytree(src_dist, dst_dist)
    print(f"  ✅ frontend/dist")

    # 2. 后端代码（排除 __pycache__、venv、tests）
    src_backend = ROOT_DIR / "backend"
    dst_backend = RELEASE_DIR / "backend"
    if dst_backend.exists():
        shutil.rmtree(dst_backend)
    shutil.copytree(
        src_backend,
        dst_backend,
        ignore=shutil.ignore_patterns(
            "__pycache__", "venv", "*.pyc", ".pytest_cache", "tests"
        ),
    )
    print(f"  ✅ backend/")

    # 3. 启动器
    for f in ["launcher.py", "start.bat", "start.sh"]:
        src = ROOT_DIR / f
        if src.exists():
            shutil.copy2(src, RELEASE_DIR / f)
            print(f"  ✅ {f}")

    # 4. 配置模板
    config_example = ROOT_DIR / "config.example.json"
    if config_example.exists():
        shutil.copy2(config_example, RELEASE_DIR / "config.example.json")
        print(f"  ✅ config.example.json")

    # 5. 文档
    docs_dir = RELEASE_DIR / "docs"
    docs_dir.mkdir(exist_ok=True)
    for doc in ["user_guide.md", "changelog.md"]:
        src = ROOT_DIR / "docs" / doc
        if src.exists():
            shutil.copy2(src, docs_dir / doc)
    # README
    readme = ROOT_DIR / "README.md"
    if readme.exists():
        shutil.copy2(readme, RELEASE_DIR / "README.md")
    print(f"  ✅ docs/ + README.md")


def create_requirements():
    """生成精简的 requirements.txt（排除开发依赖）"""
    req_file = ROOT_DIR / "backend" / "requirements.txt"
    if not req_file.exists():
        return

    # 排除打包时不需要的包（用户选本地模式自己装）
    SKIP_PACKAGES = {
        "faster-whisper",
        "pyannote.audio",
        "torch",
        "torchaudio",
        "speechbrain",
        "pyannote",
    }

    lines = req_file.read_text(encoding="utf-8").strip().splitlines()
    filtered = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        pkg_name = line.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].strip().lower().replace("-", "_")
        if pkg_name in SKIP_PACKAGES or any(pkg_name == s.replace("-", "_") for s in SKIP_PACKAGES):
            continue
        filtered.append(line)

    out = RELEASE_DIR / "backend" / "requirements.txt"
    out.write_text("\n".join(filtered) + "\n", encoding="utf-8")
    print(f"\n📝 精简 requirements.txt（排除本地 ML 包）:")
    for pkg in filtered:
        print(f"    {pkg}")


def copy_ffmpeg():
    """复制 FFmpeg 二进制（如果存在）"""
    ffmpeg_dir = ROOT_DIR / "ffmpeg"
    if not ffmpeg_dir.exists():
        print(f"\n⚠️  ffmpeg/ 目录不存在，跳过。")
        print(f"   请将 ffmpeg.exe (Windows) 或 ffmpeg (macOS) 放入 {ffmpeg_dir}")
        return

    dst = RELEASE_DIR / "ffmpeg"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(ffmpeg_dir, dst)
    print(f"  ✅ ffmpeg/")


def create_version_info():
    """生成版本信息文件"""
    version_file = RELEASE_DIR / "VERSION.txt"
    version_file.write_text(
        f"whisperMe\n"
        f"Build: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Platform: {sys.platform}\n",
        encoding="utf-8",
    )
    print(f"  ✅ VERSION.txt")


def print_summary():
    """打印构建摘要"""
    # 统计目录大小
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(str(RELEASE_DIR)):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)

    size_mb = total_size / (1024 * 1024)
    print(f"\n{'='*50}")
    print(f"  构建完成!")
    print(f"  输出目录: {RELEASE_DIR}")
    print(f"  总大小: {size_mb:.1f} MB")
    print(f"{'='*50}")
    print(f"\n  下一步:")
    print(f"  1. 将 Python 嵌入式包放入 release/whisperMe/python/")
    print(f"  2. 安装依赖: pip install -r backend/requirements.txt --target python/")
    print(f"  3. 将 ffmpeg 放入 release/whisperMe/ffmpeg/")
    print(f"  4. 打包成 zip 发布")


def main():
    print("🔨 whisperMe 构建脚本")
    print(f"   平台: {sys.platform}")
    print(f"   目标: {RELEASE_DIR}")

    clean()
    build_frontend()
    copy_files()
    create_requirements()
    copy_ffmpeg()
    create_version_info()
    print_summary()


if __name__ == "__main__":
    main()
