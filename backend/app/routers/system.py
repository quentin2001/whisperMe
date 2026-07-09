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
from fastapi import APIRouter, Response, HTTPException
from app.config import config, STORAGE_BASE, CURRENT_VERSION
from app.core.queue_manager import queue_manager

from app.core import logger
print = logger.info

router = APIRouter(prefix="/api", tags=["system"])

ALLOWED_IMAGE_DOMAINS = {
    "xiaoyuzhoufm.com",
    "xyzcdn.net",
    "bilibili.com",
    "hdslb.com",
    "xmcdn.com",
    "lizhi.fm",
    "music.126.net",
    "126.net",
    "unsplash.com"
}

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
        if sys.platform == "darwin":
            # macOS GPU/MPS detection
            try:
                brand = _sp.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode("utf-8", errors="ignore").strip()
            except Exception:
                import os
                # Fallback check
                machine = "arm64"
                try:
                    machine = os.uname().machine
                except Exception:
                    pass
                brand = "Apple Silicon" if machine == "arm64" else "Intel Mac"
            
            has_mps = False
            try:
                import torch
                has_mps = torch.backends.mps.is_available()
            except Exception:
                has_mps = "Apple" in brand
            
            if has_mps:
                gpu_info = {
                    "available": True,
                    "name": brand,
                    "vram_total": f"{system_ram} GB (Unified)",
                    "vram_free": f"{round(system_ram * 0.7, 1)} GB (Est.)"
                }
        else:
            # Windows/Linux CUDA detection
            result = _sp.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5,
                creationflags=_sp.CREATE_NO_WINDOW if sys.platform == "win32" else 0
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

    # Get system RAM
    system_ram = 8.0  # fallback
    try:
        import psutil
        system_ram = round(psutil.virtual_memory().total / (1024 ** 3), 1)
    except Exception:
        try:
            ram_out = subprocess.check_output("wmic OS get TotalVisibleMemorySize /Value", shell=True).decode("utf-8", errors="ignore")
            for line in ram_out.splitlines():
                if "TotalVisibleMemorySize=" in line:
                    total_kb = float(line.split("=")[1].strip())
                    system_ram = round(total_kb / (1024 * 1024), 1)
        except Exception:
            pass

    return {
        "ffmpeg": ffmpeg_info,
        "huggingface": {"token_valid": hf_valid},
        "ollama": {"available": ollama_ok, "url": _cfg.OLLAMA_URL, "model": _cfg.OLLAMA_MODEL, "version": ollama_version},
        "gpu": gpu_info,
        "system_ram": system_ram
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


@router.get("/proxy/image")
def proxy_image(url: str):
    """代理图片请求，解决浏览器无法直接访问某些 CDN 的问题"""
    if not url:
        raise HTTPException(status_code=400, detail="Missing url parameter")

    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise HTTPException(status_code=403, detail="Invalid protocol")
        
        hostname = parsed.hostname
        if not hostname:
            raise HTTPException(status_code=403, detail="Invalid url format")

        # 校验白名单
        is_allowed = False
        for domain in ALLOWED_IMAGE_DOMAINS:
            if hostname == domain or hostname.endswith("." + domain):
                is_allowed = True
                break
                
        if not is_allowed:
            raise HTTPException(status_code=403, detail="Domain not allowed")

        import httpx
        with httpx.Client(timeout=10, follow_redirects=True, trust_env=False) as client:
            resp = client.get(url, headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": ""
            })
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "image/jpeg")
                return Response(
                    content=resp.content,
                    media_type=content_type,
                    headers={"Cache-Control": "public, max-age=86400"}
                )
            raise HTTPException(status_code=resp.status_code, detail="Upstream error")
    except HTTPException:
        raise
    except Exception as e:
        print(f"⚠️ [PROXY] 图片代理失败: {url} - {e}")
        raise HTTPException(status_code=502, detail="Bad Gateway")


@router.get("/models/registry")
def get_models_registry():
    """获取本地 ASR / LLM 模型推荐列表，支持从公网动态同步更新"""
    default_registry = {
        "asr": [
            {
                "id": "funasr-paraformer-zh",
                "name": "FunASR Paraformer (Chinese)",
                "type": "local",
                "size": "120 MB",
                "description": "Recommended for Chinese offline speech recognition. Runs extremely fast on CPU/GPU.",
                "url": "https://modelscope.cn/models/iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
                "recommended_for": "Chinese / CPU & GPU"
            },
            {
                "id": "whisper-base",
                "name": "Whisper Base (Multi-language)",
                "type": "local",
                "size": "140 MB",
                "description": "Good accuracy for multi-language or English podcasts. Runs well on average hardware.",
                "url": "https://hf-mirror.com/Systran/faster-whisper-base",
                "recommended_for": "Multi-language / Low Spec"
            },
            {
                "id": "whisper-large-v3",
                "name": "Whisper Large-V3",
                "type": "local",
                "size": "3.1 GB",
                "description": "Best transcription quality. Requires CUDA GPU with at least 6GB VRAM.",
                "url": "https://hf-mirror.com/Systran/faster-whisper-large-v3",
                "recommended_for": "Multi-language / GPU >= 6GB VRAM"
            }
        ],
        "llm": [
            {
                "id": "qwen2.5:7b-instruct",
                "name": "Qwen 2.5 7B Instruct",
                "type": "ollama",
                "size": "4.7 GB",
                "description": "Highly recommended for summary and outline generation. Excellent Chinese support. Runs well on 16GB RAM/8GB VRAM.",
                "command": "ollama run qwen2.5:7b-instruct",
                "recommended_for": "Chinese & English / RAM >= 16GB"
            },
            {
                "id": "qwen2.5:1.5b-instruct",
                "name": "Qwen 2.5 1.5B Instruct",
                "type": "ollama",
                "size": "980 MB",
                "description": "Ultra lightweight model for low-spec machines. Runs fast on CPU.",
                "command": "ollama run qwen2.5:1.5b-instruct",
                "recommended_for": "Low Spec / CPU Mode"
            },
            {
                "id": "llama3:8b",
                "name": "Llama 3 8B Instruct",
                "type": "ollama",
                "size": "4.7 GB",
                "description": "Meta's standard 8B model. Best for English podcast analysis.",
                "command": "ollama run llama3:8b",
                "recommended_for": "English Only"
            }
        ]
    }
    
    try:
        import httpx
        url = "https://raw.githubusercontent.com/quentin2001/whisperMe/main/models_registry.json"
        with httpx.Client(timeout=3.0, trust_env=False) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if "asr" in data and "llm" in data:
                    print("✅ [LOG] 成功同步最新云端模型注册表！")
                    return data
    except Exception as e:
        print(f"⚠️ [LOG] 云端模型注册表同步跳过 (使用内置配置): {e}")
        
    return default_registry


# --- 启动函数 ---
def start_system_background_tasks():
    t = threading.Thread(target=background_perf_monitor, daemon=True)
    t.start()
