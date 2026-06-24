import subprocess
import os
import sys
import time
import signal
import threading
from datetime import datetime

# 定义主要目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
LOGS_DIR = os.path.join(ROOT_DIR, "logs")

# 如果 logs 文件夹不存在，则创建
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# 生成带时间戳的日志文件名
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backend_log_file = os.path.join(LOGS_DIR, f"backend_{timestamp}.log")
frontend_log_file = os.path.join(LOGS_DIR, f"frontend_{timestamp}.log")

# 自动寻找虚拟环境的 python，如果没有则使用全局 python
if sys.platform == "win32":
    _venv_rel = os.path.join("Scripts", "python.exe")
else:
    _venv_rel = os.path.join("bin", "python")

venv_python = os.path.join(ROOT_DIR, "venv", _venv_rel)
if not os.path.exists(venv_python):
    venv_python = os.path.join(BACKEND_DIR, "venv", _venv_rel)
if not os.path.exists(venv_python):
    venv_python = "python"

env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"
env["PYTHONUNBUFFERED"] = "1"
env["NO_PROXY"] = "localhost,127.0.0.1,token-plan-sgp.xiaomimimo.com,hf-mirror.com"

print("========================================")
print("🚀 正在启动 whisperMe 项目服务...")
print("========================================")

# 启动后端
backend_process = subprocess.Popen(
    [venv_python, "run.py"],
    cwd=BACKEND_DIR,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding='utf-8',
    errors='replace',
    env=env
)

# 启动前端
frontend_process = subprocess.Popen(
    ["npm.cmd" if os.name == "nt" else "npm", "run", "dev"],
    cwd=FRONTEND_DIR,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding='utf-8',
    errors='replace',
    env=env
)

# 日志输出与流转发函数
def stream_and_log(process, name, log_path):
    with open(log_path, "w", encoding="utf-8") as f:
        for line in process.stdout:
            sys.stdout.write(f"[{name}] {line}")
            sys.stdout.flush()
            f.write(line)
            f.flush()

# 使用多线程同时读取前端和后端的输出
threading.Thread(target=stream_and_log, args=(backend_process, "BACKEND", backend_log_file), daemon=True).start()
threading.Thread(target=stream_and_log, args=(frontend_process, "FRONTEND", frontend_log_file), daemon=True).start()

print(f"\n✅ 前后端服务已成功拉起！")
print(f"📄 后端日志: {backend_log_file}")
print(f"📄 前端日志: {frontend_log_file}")
print(f"\n⚠️  需要停止项目时，请直接在此窗口按下 [Ctrl + C] 即可自动关闭所有服务。\n")

def cleanup(signum, frame):
    print("\n🛑 正在停止所有服务，请稍候...")
    if os.name == "nt":
        # Windows 环境下强制结束进程树，确保 node 子进程也被清理干净
        subprocess.call(["taskkill", "/F", "/T", "/PID", str(backend_process.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(["taskkill", "/F", "/T", "/PID", str(frontend_process.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        backend_process.terminate()
        frontend_process.terminate()
    print("👋 所有服务已完全关闭。")
    sys.exit(0)

# 绑定关闭信号
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

try:
    # 主线程保持运行状态
    while True:
        time.sleep(1)
        # 如果任意服务意外挂掉，执行清理并退出脚本，以便外层批处理脚本自动重启
        if backend_process.poll() is not None or frontend_process.poll() is not None:
            cleanup(None, None)
            break
except KeyboardInterrupt:
    cleanup(None, None)
