"""
whisperMe 可执行文件构建脚本
将 launcher.py 编译为带 logo 图标的单个 .exe
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
DIST_DIR = ROOT_DIR / "release"


def ensure_icon():
    """确保 logo.ico 存在"""
    ico_path = ROOT_DIR / "logo.ico"
    if not ico_path.exists():
        print("🎨 生成图标...")
        subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "make_icon.py")],
            cwd=str(ROOT_DIR),
            check=True,
        )
    return ico_path


def build_exe():
    """使用 PyInstaller 编译 launcher.py 为单个 .exe"""
    ico_path = ensure_icon()

    print("\n🔨 编译 whisperMe.exe ...")

    # PyInstaller 参数
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                        # 单文件
        "--windowed",                       # 无控制台窗口
        "--name", "whisperMe",              # 输出文件名
        "--icon", str(ico_path),            # 图标
        "--clean",                          # 清理缓存
        "--noconfirm",                      # 不确认覆盖
        "--distpath", str(DIST_DIR),        # 输出目录
        "--workpath", str(ROOT_DIR / "build_tmp"),  # 临时目录
        "--specpath", str(ROOT_DIR),        # spec 文件位置
        str(ROOT_DIR / "launcher.py"),      # 入口脚本
    ]

    result = subprocess.run(cmd, cwd=str(ROOT_DIR))
    if result.returncode != 0:
        print("❌ 编译失败")
        sys.exit(1)

    exe_path = DIST_DIR / "whisperMe.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n✅ 编译完成: {exe_path}")
        print(f"   大小: {size_mb:.1f} MB")
    else:
        print("❌ 未找到输出文件")
        sys.exit(1)

    # 清理临时文件
    build_tmp = ROOT_DIR / "build_tmp"
    spec_file = ROOT_DIR / "whisperMe.spec"
    if build_tmp.exists():
        shutil.rmtree(build_tmp)
    if spec_file.exists():
        spec_file.unlink()

    return exe_path


def main():
    print("🚀 whisperMe 可执行文件构建工具")
    print(f"   平台: {sys.platform}")

    if sys.platform != "win32":
        print("⚠️  当前平台不是 Windows，生成的将是可执行文件而非 .exe")

    exe_path = build_exe()

    print(f"\n{'='*50}")
    print(f"  构建完成!")
    print(f"  输出: {exe_path}")
    print(f"{'='*50}")
    print(f"\n  将 whisperMe.exe 复制到 release/whisperMe/ 目录")
    print(f"  用户双击 whisperMe.exe 即可启动")


if __name__ == "__main__":
    main()
