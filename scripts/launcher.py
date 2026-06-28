#!/usr/bin/env python3
"""
whisperMe 生产模式启动器
启动后台服务器 → 打开浏览器 → 自身退出（不占窗口）
服务器在后台持续运行，关闭浏览器不影响。
停止方式：任务管理器结束 python/pythonw 进程，或访问 http://localhost:9101/api/shutdown
"""
import os
import sys
import time
import socket
import argparse
import subprocess
import webbrowser

# PyInstaller 打包后 __file__ 指向临时目录，需要用 exe 所在目录
if getattr(sys, 'frozen', False):
    ROOT_DIR = os.path.dirname(sys.executable)
else:
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    # 在 repo 中 scripts/launcher.py → 需要跳到项目根目录
    if not os.path.isdir(os.path.join(ROOT_DIR, "backend")):
        ROOT_DIR = os.path.dirname(ROOT_DIR)

BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
PORT = 9101
URL = f"http://localhost:{PORT}"


def check_port_in_use(port: int) -> bool:
    """检查端口是否已被占用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False


def show_port_conflict_message(port: int):
    """端口冲突时向用户显示提示"""
    msg = (
        f"whisperMe 启动失败：端口 {port} 已被占用。\n\n"
        "可能的原因：\n"
        "1. whisperMe 已经在运行中（请勿重复启动）\n"
        "2. 其他程序占用了该端口\n\n"
        "如需重启，请先运行 stop.bat / stop.sh 停止现有实例。"
    )
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, msg, "whisperMe", 0x10)
        except Exception:
            pass
    print(msg)


def find_python():
    """查找可用的 Python 解释器"""
    # 打包后的嵌入式 Python
    if sys.platform == "win32":
        embedded = os.path.join(ROOT_DIR, "python", "python.exe")
    else:
        embedded = os.path.join(ROOT_DIR, "python", "bin", "python3")
    if os.path.isfile(embedded):
        return embedded
    # venv
    if sys.platform == "win32":
        venv = os.path.join(ROOT_DIR, "venv", "Scripts", "python.exe")
    else:
        venv = os.path.join(ROOT_DIR, "venv", "bin", "python")
    if os.path.isfile(venv):
        return venv
    return sys.executable


def wait_for_server(timeout=30):
    """轮询等待服务器就绪"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=1):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.3)
    return False


def main():
    # 启用 Windows 10 ANSI 支持
    if sys.platform == "win32":
        os.system("")

    parser = argparse.ArgumentParser()
    parser.add_argument("--foreground", action="store_true", help="前台运行模式")
    args = parser.parse_args()

    # 炫酷的动态渐变 Logo (基于 assets/logo.svg 的波浪造型)
    logo = [
        "  \033[38;2;233;64;87m           _     _                             __  __       \033[0m",
        "  \033[38;2;233;64;87m          | |   (_)                           |  \\/  |      \033[0m",
        "  \033[38;2;242;113;33m __      _| |__  _ ___ _ __   ___ _ __        | \\  / | ___  \033[0m",
        "  \033[38;2;242;113;33m \\ \\ /\\ / / '_ \\| / __| '_ \\ / _ \\ '__|       | |\\/| |/ _ \\ \033[0m",
        "  \033[38;2;242;113;33m  \\ V  V /| | | | \\__ \\ |_) |  __/ |          | |  | |  __/ \033[0m",
        "  \033[38;2;138;35;135m   \\_/\\_/ |_| |_|_|___/ .__/ \\___|_|          |_|  |_|\\___| \033[0m",
        "  \033[38;2;138;35;135m                      | |                                   \033[0m",
        "  \033[38;2;138;35;135m                      |_|                                   \033[0m",
        "  ",
        "  \033[3m\033[38;2;138;35;135m         A I   P o d c a s t   W o r k s p a c e     \033[0m"
    ]
    print("\n" + "\n".join(logo) + "\n")

    # 检查端口是否已被占用
    if check_port_in_use(PORT):
        show_port_conflict_message(PORT)
        sys.exit(1)

    python_exe = find_python()

    # 检查前端静态文件
    frontend_dist = os.path.join(ROOT_DIR, "frontend", "dist")
    if not os.path.isdir(frontend_dist):
        print(f"  ⚠️  前端静态文件不存在: {frontend_dist}")
        print(f"     请先运行: cd frontend && npm run build")
        sys.exit(1)

    # 设置环境变量
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    env["NO_PROXY"] = "localhost,127.0.0.1"

    # 日志文件
    logs_dir = os.path.join(ROOT_DIR, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, "whisperMe.log")

    # 启动 uvicorn 后台进程（无窗口模式）
    cmd = [
        python_exe, "-u", "-m", "uvicorn",
        "app.main:app",
        "--host", "127.0.0.1",
        "--port", str(PORT),
    ]

    print(f"  ⏳ 正在启动服务...")

    if args.foreground:
        server = subprocess.Popen(
            cmd,
            cwd=BACKEND_DIR,
            env=env,
        )
    else:
        with open(log_file, "a", encoding="utf-8") as log:
            if sys.platform == "win32":
                server = subprocess.Popen(
                    cmd,
                    cwd=BACKEND_DIR,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    env=env,
                    creationflags=0x08000000,
                )
            else:
                server = subprocess.Popen(
                    cmd,
                    cwd=BACKEND_DIR,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    env=env,
                    start_new_session=True,
                )

    # 写入 PID 文件
    pid_file = os.path.join(ROOT_DIR, ".whisperMe.pid")
    with open(pid_file, "w") as f:
        f.write(str(server.pid))

    # 等待服务就绪
    if wait_for_server():
        print(f"  🟢 服务已启动: {URL}")
        print(f"  📁 日志文件:    {log_file}")
        print(f"  🛑 停止方式:    运行 stop.bat 或访问 {URL}/api/shutdown")
        print()
        webbrowser.open(URL)
    else:
        print(f"  ❌ 启动超时，请查看日志: {log_file}")
        sys.exit(1)

    if args.foreground:
        print("\n  👉 提示: 请保持此窗口打开。按 Ctrl+C 随时停止服务...")
        try:
            server.wait()
        except KeyboardInterrupt:
            server.terminate()
            print("\n  🛑 服务已优雅退出。")
        sys.exit(0)
    else:
        # 启动器自身退出，服务器继续在后台运行
        sys.exit(0)


if __name__ == "__main__":
    main()
