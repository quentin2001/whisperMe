#!/usr/bin/env python3
"""
whisperMe 生产模式启动器
双击 start.bat (Windows) 或 start.sh (macOS) 即可运行。
后台启动 FastAPI 服务，自动打开浏览器。
"""
import os
import sys
import time
import signal
import socket
import subprocess
import webbrowser
import threading

# ===== 路径设置 =====
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
PORT = 9101
URL = f"http://localhost:{PORT}"


def find_python():
    """查找可用的 Python 解释器（优先使用 venv）"""
    if sys.platform == "win32":
        candidates = [
            os.path.join(ROOT_DIR, "venv", "Scripts", "python.exe"),
            os.path.join(BACKEND_DIR, "venv", "Scripts", "python.exe"),
        ]
    else:
        candidates = [
            os.path.join(ROOT_DIR, "venv", "bin", "python"),
            os.path.join(BACKEND_DIR, "venv", "bin", "python"),
        ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    # 嵌入式 Python（打包后）
    if sys.platform == "win32":
        embedded = os.path.join(ROOT_DIR, "python", "python.exe")
    else:
        embedded = os.path.join(ROOT_DIR, "python", "bin", "python3")
    if os.path.isfile(embedded):
        return embedded
    return sys.executable


def wait_for_server(url, timeout=30):
    """轮询等待服务器就绪"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=1):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.3)
    return False


def stream_output(process, prefix):
    """后台线程：将子进程输出转发到控制台"""
    for line in process.stdout:
        sys.stdout.write(f"[{prefix}] {line}")
        sys.stdout.flush()


def main():
    # 确保日志目录存在
    logs_dir = os.path.join(ROOT_DIR, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    python_exe = find_python()
    print(f"🐍 Python: {python_exe}")
    print(f"📁 Backend: {BACKEND_DIR}")
    print(f"🌐 URL: {URL}")

    # 检查前端静态文件
    frontend_dist = os.path.join(ROOT_DIR, "frontend", "dist")
    if os.path.isdir(frontend_dist):
        print(f"✅ 前端静态文件: {frontend_dist}")
    else:
        print(f"⚠️  前端静态文件不存在: {frontend_dist}")
        print(f"   开发模式请使用 start_project.py 或 一键启动.bat")
        print(f"   生产模式请先运行: cd frontend && npm run build")
        sys.exit(1)

    # 设置环境变量
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    env["NO_PROXY"] = "localhost,127.0.0.1"

    # 启动 uvicorn（生产模式，不带 --reload）
    cmd = [
        python_exe, "-u", "-m", "uvicorn",
        "app.main:app",
        "--host", "127.0.0.1",
        "--port", str(PORT),
    ]

    print(f"\n🚀 正在启动 whisperMe 服务...")
    server = subprocess.Popen(
        cmd,
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )

    # 后台转发日志
    threading.Thread(target=stream_output, args=(server, "SERVER"), daemon=True).start()

    # 等待服务器就绪
    print(f"⏳ 等待服务就绪...")
    if wait_for_server(URL):
        print(f"✅ 服务已就绪！")
        # 自动打开浏览器
        print(f"🌐 正在打开浏览器: {URL}")
        webbrowser.open(URL)
        print(f"\n{'='*50}")
        print(f"  whisperMe 已启动")
        print(f"  浏览器访问: {URL}")
        print(f"  关闭此窗口或按 Ctrl+C 停止服务")
        print(f"{'='*50}\n")
    else:
        print(f"❌ 服务启动超时，请检查日志")
        server.terminate()
        sys.exit(1)

    # 保持进程运行
    def cleanup(signum=None, frame=None):
        print("\n🛑 正在停止服务...")
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
        print("👋 whisperMe 已停止。")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        server.wait()
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
