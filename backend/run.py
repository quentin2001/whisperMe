import os
import sys
import io
import subprocess

# 物理重写 stdout 流，屏蔽 Windows GBK 编码刺客
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')

def main():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(backend_dir)
    
    # 确定 venv 路径下的 python.exe
    venv_python = os.path.join(project_dir, "venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        # 兜底查找 backend 下的 venv
        venv_python = os.path.join(backend_dir, "venv", "Scripts", "python.exe")
        
    if not os.path.exists(venv_python):
        print("[ERROR] 找不到 Python 虚拟环境，请确保已成功创建 venv 并安装依赖。")
        sys.exit(1)
        
    print("[LOG] 启动 whisperMe 本地后台服务...")
    print(f"  * 虚拟环境 Python: {venv_python}")
    print("  * 监听地址: http://127.0.0.1:8000")
    print("  * 音频下载挂载路径: http://127.0.0.1:8000/audio")
    print("=" * 60)
    
    # 使用 venv 中的 python.exe 执行 uvicorn
    cmd = [
        venv_python, 
        "-m", "uvicorn", 
        "app.main:app", 
        "--host", "127.0.0.1", 
        "--port", "8000", 
        "--reload"
    ]
    
    try:
        # 切换工作目录到 backend 目录，以便正确导入 app 包
        subprocess.run(cmd, cwd=backend_dir)
    except KeyboardInterrupt:
        print("\n后端服务已安全停止。")
    except Exception as e:
        print(f"\n[ERROR] 启动失败: {e}")

if __name__ == "__main__":
    main()
