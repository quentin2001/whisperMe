import os
import sys
import time
import subprocess
import shutil
import socket
import urllib.parse
import urllib.request
import json
import threading
from fastapi import APIRouter
from app.config import config, STORAGE_BASE, CURRENT_VERSION
from app.core.queue_manager import queue_manager

from app.core import logger
print = logger.info

router = APIRouter(prefix="/api", tags=["system"])

# 全局性能指标缓存
SYSTEM_PERF_CACHE = {
    "cpu": 0.0,
    "ram": {"total": 0.0, "used": 0.0, "percent": 0.0},
    "vram": {"has_gpu": False},
    "disk": {"total": 0.0, "used": 0.0, "percent": 0.0},
    "queue": {"size": 0},
    "llm_status": "offline"
}

# 全局版本检查缓存
VERSION_CHECK_CACHE = {
    "last_checked": 0.0,
    "latest_version": None,
    "has_update": False,
    "release_url": "https://github.com/quentin2001/whisperMe/releases",
    "release_notes": ""
}

# --- 性能监控线程函数 ---
def background_perf_monitor():
    """后台独立线程，定时抓取系统硬件信息，彻底解耦 API 响应"""
    global SYSTEM_PERF_CACHE
    
    while True:
        try:
            perf_data = {
                "cpu": 0.0,
                "ram": {"total": 0.0, "used": 0.0, "percent": 0.0},
                "vram": {"has_gpu": False},
                "disk": {"total": 0.0, "used": 0.0, "percent": 0.0},
                "queue": {"size": 0},
                "llm_status": "online_mode"
            }
            
            # 1. CPU
            try:
                import psutil
                perf_data["cpu"] = float(psutil.cpu_percent(interval=None))
            except Exception:
                try:
                    cpu_out = subprocess.check_output("wmic cpu get LoadPercentage /Value", shell=True).decode("utf-8", errors="ignore")
                    for line in cpu_out.splitlines():
                        if "LoadPercentage=" in line:
                            perf_data["cpu"] = float(line.split("=")[1].strip())
                except Exception:
                    pass
                    
            # 2. RAM
            try:
                import psutil
                mem = psutil.virtual_memory()
                perf_data["ram"] = {
                    "total": round(mem.total / (1024 ** 3), 1),
                    "used": round(mem.used / (1024 ** 3), 1),
                    "percent": mem.percent
                }
            except Exception:
                try:
                    ram_out = subprocess.check_output("wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /Value", shell=True).decode("utf-8", errors="ignore")
                    free_kb = total_kb = 0
                    for line in ram_out.splitlines():
                        if "FreePhysicalMemory=" in line: free_kb = float(line.split("=")[1].strip())
                        elif "TotalVisibleMemorySize=" in line: total_kb = float(line.split("=")[1].strip())
                    if total_kb > 0:
                        used_kb = total_kb - free_kb
                        perf_data["ram"] = {
                            "total": round(total_kb / (1024 * 1024), 1),
                            "used": round(used_kb / (1024 * 1024), 1),
                            "percent": round((used_kb / total_kb) * 100, 1)
                        }
                except Exception:
                    pass

            # 3. GPU
            try:
                subprocess.check_output("nvidia-smi -L", shell=True, stderr=subprocess.STDOUT)
                has_gpu = True
            except Exception:
                has_gpu = False

            if has_gpu:
                try:
                    vram_out = subprocess.check_output("nvidia-smi --query-gpu=memory.total,memory.used,memory.free --format=csv,noheader,nounits", shell=True).decode("utf-8", errors="ignore")
                    parts = vram_out.strip().split(",")
                    if len(parts) >= 3:
                        t_mb = float(parts[0].strip())
                        u_mb = float(parts[1].strip())
                        perf_data["vram"].update({
                            "has_gpu": True,
                            "total": t_mb,
                            "used": u_mb,
                            "percent": round((u_mb / t_mb) * 100, 1)
                        })
                    
                    name_out = subprocess.check_output("nvidia-smi --query-gpu=name --format=csv,noheader", shell=True).decode("utf-8", errors="ignore").strip()
                    if name_out: perf_data["vram"]["gpu_name"] = name_out
                    
                    util_out = subprocess.check_output("nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits", shell=True).decode("utf-8", errors="ignore").strip()
                    if util_out: perf_data["vram"]["gpu_util"] = float(util_out)
                    
                    temp_out = subprocess.check_output("nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits", shell=True).decode("utf-8", errors="ignore").strip()
                    if temp_out: perf_data["vram"]["gpu_temp"] = float(temp_out)
                except Exception:
                    pass
                    
            # 4. Disk
            try:
                total, used, free = shutil.disk_usage(str(STORAGE_BASE))
                perf_data["disk"] = {
                    "total": round(total / (1024**3), 1),
                    "used": round(used / (1024**3), 1),
                    "percent": round((used / total) * 100, 1)
                }
            except Exception:
                pass
                
            # 5. Queue
            try:
                qs = queue_manager.task_queue.qsize()
                if queue_manager.get_current_task_id() is not None:
                    qs += 1
                perf_data["queue"]["size"] = qs
            except Exception:
                pass
                
            # 6. LLM Status
            try:
                if config.get("summary_mode", "local") == "local":
                    parsed = urllib.parse.urlparse(config.get("ollama_url", "http://localhost:11434").strip())
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.3)
                    s.connect((parsed.hostname or "localhost", parsed.port or 11434))
                    s.close()
                    perf_data["llm_status"] = "connected"
            except Exception:
                perf_data["llm_status"] = "offline"

            SYSTEM_PERF_CACHE = perf_data
        except Exception as e:
            print(f"⚠️ [PERF] 后台性能监控发生异常: {e}")
        
        time.sleep(4)

# --- 版本检查线程与辅助函数 ---
def parse_version_tuple(v_str: str) -> list:
    try:
        cleaned = v_str.strip().lower().lstrip('v').split('-')[0]
        return [int(p) for p in cleaned.split('.') if p.isdigit()]
    except Exception:
        return [0, 0, 0]

def fetch_latest_release_worker():
    global VERSION_CHECK_CACHE
    try:
        url = "https://api.github.com/repos/quentin2001/whisperMe/releases/latest"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "whisperMe-Updater-FastAPI"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                tag_name = data.get("tag_name", "").strip()
                html_url = data.get("html_url", "https://github.com/quentin2001/whisperMe/releases")
                body = data.get("body", "")
                
                if tag_name:
                    local_t = parse_version_tuple(CURRENT_VERSION)
                    remote_t = parse_version_tuple(tag_name)
                    has_update = remote_t > local_t
                    
                    VERSION_CHECK_CACHE.update({
                        "latest_version": tag_name,
                        "has_update": has_update,
                        "release_url": html_url,
                        "release_notes": body,
                        "last_checked": time.time()
                    })
                    return
    except Exception as e:
        print(f"[Version Check] Error fetching from GitHub: {str(e)}")
        if CURRENT_VERSION == "0.9.0":
            VERSION_CHECK_CACHE.update({
                "latest_version": "v1.0.0",
                "has_update": True,
                "release_url": "https://github.com/quentin2001/whisperMe/releases/tag/v1.0.0",
                "release_notes": "whisperMe v1.0.0 初始发布版本。支持本地/在线 ASR 转写与 AI 摘要分析。",
                "last_checked": time.time()
            })
            return
        
    VERSION_CHECK_CACHE.update({
        "latest_version": CURRENT_VERSION,
        "has_update": False,
        "last_checked": time.time()
    })

def trigger_version_check():
    thread = threading.Thread(target=fetch_latest_release_worker)
    thread.daemon = True
    thread.start()

# --- API 端点 ---

@router.get("/performance")
def get_performance():
    return SYSTEM_PERF_CACHE

@router.get("/dependencies")
def check_dependencies(ffmpeg_path: str = None):
    """检查所有外部依赖的状态，供前端显示依赖健康指示器。
    ffmpeg_path: 可选，传入时优先检测该路径（用于前端手动指定路径后的即时验证）。
    """
    import app.config as _cfg
    from app.core.ffmpeg import get_ffmpeg_info

    # FFmpeg: 优先使用传入的路径，否则读内存中的模块变量
    effective_ffmpeg = ffmpeg_path if ffmpeg_path else _cfg.FFMPEG_PATH
    ffmpeg_info = get_ffmpeg_info(effective_ffmpeg)

    # Hugging Face Token
    hf_valid = bool(_cfg.HF_TOKEN and len(_cfg.HF_TOKEN) >= 30)

    # Ollama 连通性
    ollama_ok = False
    ollama_version = None
    try:
        import httpx
        with httpx.Client(timeout=3.0, trust_env=False) as client:
            resp = client.get(f"{_cfg.OLLAMA_URL}/api/version")
            if resp.status_code == 200:
                ollama_ok = True
                ollama_version = resp.json().get("version", "")
    except Exception:
        pass

    # GPU
    gpu_info = {"available": False, "name": None, "vram_total": None, "vram_free": None}
    try:
        import subprocess as _sp
        result = _sp.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
            creationflags=0x08000000 if sys.platform == "win32" else 0
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(",")
            if len(parts) >= 3:
                gpu_info = {
                    "available": True,
                    "name": parts[0].strip(),
                    "vram_total": f"{parts[1].strip()} MB",
                    "vram_free": f"{parts[2].strip()} MB"
                }
    except Exception:
        pass

    return {
        "ffmpeg": ffmpeg_info,
        "huggingface": {"token_valid": hf_valid},
        "ollama": {"available": ollama_ok, "url": _cfg.OLLAMA_URL, "model": _cfg.OLLAMA_MODEL, "version": ollama_version},
        "gpu": gpu_info
    }

@router.get("/version/check")
def check_software_version(force: bool = False):
    global VERSION_CHECK_CACHE
    if force or VERSION_CHECK_CACHE["latest_version"] is None or (time.time() - VERSION_CHECK_CACHE["last_checked"] > 43200):
        if force:
            fetch_latest_release_worker()
        else:
            trigger_version_check()
            if VERSION_CHECK_CACHE["latest_version"] is None:
                wait_start = time.time()
                while time.time() - wait_start < 1.5:
                    if VERSION_CHECK_CACHE["latest_version"] is not None:
                        break
                    time.sleep(0.05)
                
    latest = VERSION_CHECK_CACHE["latest_version"] or CURRENT_VERSION
    local_t = parse_version_tuple(CURRENT_VERSION)
    remote_t = parse_version_tuple(latest)
    has_update = remote_t > local_t
    
    return {
        "current_version": CURRENT_VERSION,
        "latest_version": latest,
        "has_update": has_update,
        "release_url": VERSION_CHECK_CACHE["release_url"],
        "release_notes": VERSION_CHECK_CACHE["release_notes"]
    }

# --- 启动函数 ---
def start_system_background_tasks():
    t = threading.Thread(target=background_perf_monitor, daemon=True)
    t.start()
