"""
whisperMe 全量可执行文件构建脚本
将完整后端 + 前端 + FFmpeg 编译为单个 .exe，双击即用
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
RELEASE_DIR = ROOT_DIR / "release"
FRONTEND_DIR = ROOT_DIR / "frontend"
BACKEND_DIR = ROOT_DIR / "backend"


def ensure_icon():
    """确保 logo.ico 存在"""
    ico_path = ROOT_DIR / "assets" / "logo.ico"
    if not ico_path.exists():
        print("🎨 生成图标...")
        subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "make_icon.py")],
            cwd=str(ROOT_DIR),
            check=True,
        )
    return ico_path


def ensure_frontend_built():
    """确保前端已编译"""
    dist = FRONTEND_DIR / "dist"
    if not dist.exists():
        print("📦 前端未编译，正在构建...")
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=str(FRONTEND_DIR),
            shell=(sys.platform == "win32"),
        )
        if result.returncode != 0:
            print("❌ 前端编译失败")
            sys.exit(1)
    else:
        print(f"✅ 前端已有编译产物: {dist}")
    return dist


def get_version():
    """读取版本号"""
    version_file = ROOT_DIR / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "1.4.0"


def build_full_exe():
    """PyInstaller 全量打包"""
    ico_path = ensure_icon()
    frontend_dist = ensure_frontend_built()
    ffmpeg_dir = ROOT_DIR / "ffmpeg"
    version_file = ROOT_DIR / "VERSION"

    version = get_version()
    out_name = "whisperMe"
    exe_filename = f"{out_name}.exe" if sys.platform == "win32" else out_name

    print(f"\n🔨 编译 whisperMe v{version} 全量单文件 ...")
    print(f"   入口: backend/run_server.py")
    print(f"   前端: frontend/dist")
    if ffmpeg_dir.exists():
        print(f"   FFmpeg: ffmpeg/")

    RELEASE_DIR.mkdir(parents=True, exist_ok=True)

    # ── 构建 --add-data 参数 ──────────────────────────────────
    separator = ";" if sys.platform == "win32" else ":"

    add_data = [
        # 前端静态文件
        f"{frontend_dist}{separator}frontend/dist",
        # 版本文件
        f"{version_file}{separator}.",
    ]

    # FFmpeg（如果存在）
    if ffmpeg_dir.exists():
        add_data.append(f"{ffmpeg_dir}{separator}ffmpeg")

    # 构建命令行
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        # 显示控制台窗口（让用户看到品牌横幅和运行状态）
        f"--name={out_name}",
        f"--icon={str(ico_path)}",
        "--clean",
        "--noconfirm",
        f"--distpath={str(RELEASE_DIR)}",
        f"--workpath={str(ROOT_DIR / 'build_tmp')}",
        f"--specpath={str(ROOT_DIR)}",
        # 入口
        str(BACKEND_DIR / "run_server.py"),
    ]

    # 追加 add-data
    for data in add_data:
        cmd.extend(["--add-data", data])

    # 关键隐藏导入（确保 PyInstaller 发现所有模块）
    hidden_imports = [
        "app.main", "app.config", "app.database",
        "app.core.pipeline", "app.core.transcriber", "app.core.speaker",
        "app.core.summarizer", "app.core.downloader", "app.core.ffmpeg",
        "app.core.llm_utils", "app.core.network", "app.core.compat",
        "app.core.queue_manager", "app.core.logger",
        "app.routers.tasks", "app.routers.config", "app.routers.system",
        "app.routers.boards",
        "app.core.asr_providers.mimo", "app.core.asr_providers.openai",
        "app.core.asr_providers.funasr", "app.core.asr_providers.custom",
        "uvicorn", "uvicorn.loops", "uvicorn.loops.auto",
        "uvicorn.protocols", "uvicorn.protocols.http",
        "fastapi", "starlette", "websockets",
        "pydantic", "httpx", "aiofiles",
    ]
    for mod in hidden_imports:
        cmd.extend(["--hidden-import", mod])

    # 排除不需要的大库（在线模式不需要本地 ML）
    # 注意：只排除确定不会用到的包，避免运行时 ImportError
    cmd.extend([
        "--exclude-module", "torch",
        "--exclude-module", "torchaudio",
        "--exclude-module", "faster_whisper",
        "--exclude-module", "pyannote",
        "--exclude-module", "speechbrain",
        "--exclude-module", "ctranslate2",
        "--exclude-module", "tensorflow",
    ])

    # 执行
    print(f"\n   PyInstaller 命令: {' '.join(cmd[:20])} ...")
    result = subprocess.run(cmd, cwd=str(BACKEND_DIR))
    if result.returncode != 0:
        print("❌ 编译失败")
        sys.exit(1)

    # 验证输出
    exe_path = RELEASE_DIR / exe_filename
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n   ✅ 编译完成: {exe_path}")
        print(f"      大小: {size_mb:.1f} MB")
    else:
        print("❌ 未找到输出文件")
        sys.exit(1)

    # 清理
    for tmp in [ROOT_DIR / "build_tmp", ROOT_DIR / f"{out_name}.spec"]:
        if tmp.exists():
            try:
                if tmp.is_dir():
                    shutil.rmtree(tmp)
                else:
                    tmp.unlink()
            except Exception:
                pass

    # 复制到 release/whisperMe/（如果存在）
    release_app = RELEASE_DIR / "whisperMe"
    if release_app.exists():
        dest = release_app / exe_filename
        shutil.copy2(exe_path, dest)
        print(f"      已复制到: {dest}")

    return exe_path


def main():
    version = get_version()
    print(f"🚀 whisperMe v{version} 全量构建工具")
    print(f"   平台: {sys.platform}")

    if sys.platform != "win32":
        print("⚠️  当前平台不是 Windows，生成的可执行文件可能无法在 Windows 上运行")

    exe_path = build_full_exe()

    print(f"\n{'='*50}")
    print(f"  构建完成! v{version}")
    print(f"  单文件: {exe_path}")
    print(f"{'='*50}")
    print(f"\n  用户双击 {exe_path.name} 即可启动 whisperMe。")
    print(f"  发布时同时提供此 exe 和完整 zip 包。")


if __name__ == "__main__":
    main()
