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
import subprocess
import webbrowser

# PyInstaller 打包后 __file__ 指向临时目录，需要用 exe 所在目录
if getattr(sys, 'frozen', False):
    ROOT_DIR = os.path.dirname(sys.executable)
else:
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
PORT = 9101
URL = f"http://localhost:{PORT}"


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
    python_exe = find_python()

    # 检查前端静态文件
    frontend_dist = os.path.join(ROOT_DIR, "frontend", "dist")
    if not os.path.isdir(frontend_dist):
        print(f"[whisperMe] 前端静态文件不存在: {frontend_dist}")
        print(f"  请先运行: cd frontend && npm run build")
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

    with open(log_file, "a", encoding="utf-8") as log:
        if sys.platform == "win32":
            # Windows: CREATE_NO_WINDOW 隐藏子进程窗口
            server = subprocess.Popen(
                cmd,
                cwd=BACKEND_DIR,
                stdout=log,
                stderr=subprocess.STDOUT,
                env=env,
                creationflags=0x08000000,
            )
        else:
            # macOS/Linux: 标准后台进程
            server = subprocess.Popen(
                cmd,
                cwd=BACKEND_DIR,
                stdout=log,
                stderr=subprocess.STDOUT,
                env=env,
                start_new_session=True,
            )

    # 写入 PID 文件（方便后续停止）
    pid_file = os.path.join(ROOT_DIR, ".whisperMe.pid")
    with open(pid_file, "w") as f:
        f.write(str(server.pid))

    # 等待服务就绪
    if wait_for_server():
        # 打开浏览器
        webbrowser.open(URL)
    else:
        print(f"[whisperMe] 启动超时，请查看日志: {log_file}")
        sys.exit(1)

    # 启动器自身退出，服务器继续在后台运行
    sys.exit(0)


if __name__ == "__main__":
    main()
