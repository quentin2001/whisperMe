#!/usr/bin/env python3
"""
whisperMe 自包含服务入口 — PyInstaller 打包用
包含完整后端 + 前端静态文件 → 单 exe 双击即用
"""
import os
import sys
import time
import socket
import threading
import webbrowser

PORT = 9101
URL = f"http://127.0.0.1:{PORT}"

# ── PyInstaller 路径解析 ──────────────────────────────────────────
if getattr(sys, "frozen", False):
    BUNDLE_DIR = sys._MEIPASS
else:
    BUNDLE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 确保 frontend/dist 路径可被后端找到
# 后端 config.py 通过 PROJECT_DIR/frontend/dist 查找静态文件
# 在 frozen 模式下 PROJECT_DIR = BUNDLE_DIR，所以需要 frontend/dist 在根目录
_frontend_dist = os.path.join(BUNDLE_DIR, "frontend", "dist")
_ffmpeg_dir = os.path.join(BUNDLE_DIR, "ffmpeg")
_version_file = os.path.join(BUNDLE_DIR, "VERSION")


def check_port_in_use(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False


def print_banner():
    """品牌启动横幅"""
    version = "1.4.0"
    if os.path.isfile(_version_file):
        try:
            with open(_version_file, encoding="utf-8") as f:
                version = f.read().strip()
        except Exception:
            pass

    print()
    print("  ╔══════════════════════════════════════════════╗")
    print(f"  ║       whisperMe v{version:<10}                  ║")
    print("  ║   AI 播客转录工作台 · 本地优先              ║")
    print("  ╚══════════════════════════════════════════════╝")
    print()
    print(f"  🌐 服务地址:   {URL}")
    print(f"  📁 数据目录:   {os.getcwd()}")
    print()
    print("  💡 关闭此窗口将停止服务")
    print("  ───────────────────────────────────────────")
    print()


def main():
    # 检查端口
    if check_port_in_use(PORT):
        print(f"\n  ⚠️  端口 {PORT} 已被占用，whisperMe 可能已在运行中。")
        print(f"     如需重启，请先关闭现有实例。")
        input("\n  按 Enter 退出...")
        sys.exit(1)

    print_banner()

    # 验证关键资源
    if not os.path.isdir(_frontend_dist):
        print(f"  ⚠️  前端静态文件缺失: {_frontend_dist}")
        print("     请先运行: cd frontend && npm run build")
    else:
        print(f"  ✅ 前端静态文件: {_frontend_dist}")

    if os.path.isdir(_ffmpeg_dir):
        print(f"  ✅ FFmpeg 已内置")
    else:
        print(f"  ⚠️  FFmpeg 未内置，部分功能不可用")

    print()
    print("  ⏳ 正在启动服务...")

    # 延迟导入，让横幅先显示
    import uvicorn
    from app.main import app

    # 浏览器自动打开（2 秒后）
    def _open_browser():
        time.sleep(2)
        try:
            webbrowser.open(URL)
            print(f"  🌐 浏览器已打开: {URL}")
        except Exception:
            pass

    threading.Thread(target=_open_browser, daemon=True).start()

    print(f"  🟢 服务已启动，按 Ctrl+C 停止")
    print("  ───────────────────────────────────────────")
    print()

    try:
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=PORT,
            log_level="warning",  # 减少 uvicorn 访问日志噪音
        )
    except KeyboardInterrupt:
        print("\n  🛑 正在关闭服务...")
        sys.exit(0)


if __name__ == "__main__":
    main()
