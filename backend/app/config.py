import os
import sys
import io
import json
import ctypes
from pathlib import Path

# ==================== 🛡️ 钢铁防御层 0：NumPy 2.0 兼容性补焊 ====================
import numpy as np
if not hasattr(np, "NaN"):
    np.NaN = np.nan
if not hasattr(np, "NAN"):
    np.NAN = np.nan
if not hasattr(np, "float"):
    np.float = float
if not hasattr(np, "int"):
    np.int = int

# ==================== 🛡️ 钢铁防御层 1：强行重写控制台物理输出流 ====================
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='ignore')
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# 基础目录定义
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent
CONFIG_FILE_PATH = PROJECT_DIR / "config.json"

# Windows 内核级 8.3 短路径转换器（规避一切中文路径报错）
def get_short_path_name(long_name_path):
    try:
        long_name = str(long_name_path)
        if sys.platform != 'win32': 
            return long_name
        output_buf_size = 1024
        buf = ctypes.create_unicode_buffer(output_buf_size)
        if ctypes.windll.kernel32.GetShortPathNameW(long_name, buf, output_buf_size) == 0: 
            return long_name
        return buf.value.replace("\\", "/")
    except Exception: 
        return str(long_name_path)

# 加载全局配置文件
def load_config():
    default_config = {
        "ffmpeg_path": "C:\\Users\\asd\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-8.1.1-full_build\\bin\\ffmpeg.exe",
        "ffmpeg_bin_dir": "C:\\Users\\asd\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-8.1.1-full_build\\bin",
        "local_whisper_model_path": "c:\\Users\\asd\\Desktop\\whisper\\model_large_v3",
        "hf_token": "",
        "ollama_url": "http://localhost:11434",
        "ollama_model": "qwen2.5:7b-instruct",
        "smtp_server": "smtp.qq.com",
        "smtp_port": 465,
        "smtp_username": "",
        "smtp_password": "",
        "smtp_sender": "",
        "notification_email": "",
        "enable_win_notification": True,
        "enable_email_notification": False,
        "asr_mode": "online",
        "online_api_key": "",
        "online_base_url": "https://token-plan-sgp.xiaomimimo.com/v1",
        "online_model": "mimo-v2.5-asr",
        "summary_mode": "online",
        "online_summary_api_key": "",
        "online_summary_base_url": "https://api.openai.com/v1",
        "online_summary_model": "gpt-4o-mini",
        "enable_llm_semantic_sewing": False,
        "webhook_url": "",
        "custom_storage_dir": ""
    }

    if not CONFIG_FILE_PATH.exists():
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        return default_config
    
    with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    # 合并缺失的默认配置
    changed = False
    for k, v in default_config.items():
        if k not in loaded:
            loaded[k] = v
            changed = True
            
    if changed:
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(loaded, f, ensure_ascii=False, indent=2)
            
    return loaded

# 更新全局配置文件
def save_config(new_config):
    with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(new_config, f, ensure_ascii=False, indent=2)

config = load_config()

# ==================== 🛡️ 钢铁防御层 2：提取 venv 内的 NVIDIA DLL 并硬焊进 PATH ====================
# 后端 venv 路径
venv_base = BACKEND_DIR / "venv"
if not venv_base.exists():
    # 兼容根目录下的 venv
    venv_base = PROJECT_DIR / "venv"

cublas_bin_path = venv_base / "Lib" / "site-packages" / "nvidia" / "cublas" / "bin"
cudnn_bin_path = venv_base / "Lib" / "site-packages" / "nvidia" / "cudnn" / "bin"

if cublas_bin_path.exists():
    os.environ["PATH"] = str(cublas_bin_path) + os.pathsep + os.environ["PATH"]
if cudnn_bin_path.exists():
    os.environ["PATH"] = str(cudnn_bin_path) + os.pathsep + os.environ["PATH"]

# ==================== 🛡️ 钢铁防御层 3：构建本地沙盒和 HF 镜像 ====================
# 支持外挂存储路径
CUSTOM_STORAGE_DIR = config.get("custom_storage_dir", "").strip()
if CUSTOM_STORAGE_DIR and Path(CUSTOM_STORAGE_DIR).exists():
    storage_base = Path(CUSTOM_STORAGE_DIR)
else:
    storage_base = PROJECT_DIR

DOWNLOADS_DIR = storage_base / "downloads"
TRANSCRIPTS_DIR = storage_base / "transcripts"
TEMP_SANDBOX_DIR = storage_base / "temp_sandbox"
HF_CACHE_DIR = storage_base / "hf_cache_models"

# 确保文件夹存在
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
TEMP_SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
HF_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 物理转换为 8.3 短路径
SHORT_TEMP_DIR = get_short_path_name(TEMP_SANDBOX_DIR)
SHORT_HF_CACHE_DIR = get_short_path_name(HF_CACHE_DIR)

# 重置环境变量，锁死本地英文临时区与模型区
for env_key in ["TEMP", "TMP", "USERPROFILE", "HOMEPATH", "HOME", "APPDATA", "LOCALAPPDATA"]:
    os.environ[env_key] = SHORT_TEMP_DIR

os.environ["HF_HOME"] = SHORT_HF_CACHE_DIR
os.environ["HF_HUB_CACHE"] = SHORT_HF_CACHE_DIR
os.environ["HF_ASSETS_CACHE"] = SHORT_HF_CACHE_DIR
os.environ["XDG_CACHE_HOME"] = SHORT_HF_CACHE_DIR
hf_token_temp = config.get("hf_token", "").strip()
if hf_token_temp and len(hf_token_temp) >= 30:
    os.environ["HF_ENDPOINT"] = "https://huggingface.co"
else:
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"  # 国内高速镜像站

# huggingface_hub API 动态 Patch 拦截
try:
    import huggingface_hub.constants
    import huggingface_hub.file_download
    
    if hf_token_temp and len(hf_token_temp) >= 30:
        huggingface_hub.constants.ENDPOINT = "https://huggingface.co"
        huggingface_hub.constants.HUGGINGFACE_CO_URL_TEMPLATE = "https://huggingface.co/{repo_id}/resolve/{revision}/{filename}"
    else:
        huggingface_hub.constants.ENDPOINT = "https://hf-mirror.com"
        huggingface_hub.constants.HUGGINGFACE_CO_URL_TEMPLATE = "https://hf-mirror.com/{repo_id}/resolve/{revision}/{filename}"
        
    huggingface_hub.constants.HF_HOME = SHORT_HF_CACHE_DIR
    huggingface_hub.constants.HF_HUB_CACHE = SHORT_HF_CACHE_DIR
    huggingface_hub.constants.DEFAULT_HF_CACHE_HOME = SHORT_HF_CACHE_DIR
    huggingface_hub.constants.HF_HUB_DISABLE_SYMLINKS_WARNING = True
    
    raw_hf_hub_download = huggingface_hub.file_download.hf_hub_download
    def patched_hf_hub_download(*args, **kwargs):
        if 'use_auth_token' in kwargs: 
            kwargs['token'] = kwargs.pop('use_auth_token')
        kwargs['cache_dir'] = SHORT_HF_CACHE_DIR
        kwargs['local_dir'] = SHORT_HF_CACHE_DIR
        return raw_hf_hub_download(*args, **kwargs)
    huggingface_hub.hf_hub_download = patched_hf_hub_download
    huggingface_hub.file_download.hf_hub_download = patched_hf_hub_download
except Exception:
    pass

# ==================== 导出全局可用变量 ====================
FFMPEG_PATH = config.get("ffmpeg_path")
FFMPEG_BIN_DIR = config.get("ffmpeg_bin_dir")
LOCAL_WHISPER_MODEL_PATH = config.get("local_whisper_model_path")
HF_TOKEN = config.get("hf_token", "").strip()

OLLAMA_URL = config.get("ollama_url", "http://localhost:11434")
OLLAMA_MODEL = config.get("ollama_model", "qwen2.5:7b-instruct")

SUMMARY_MODE = config.get("summary_mode", "online")
ONLINE_SUMMARY_API_KEY = config.get("online_summary_api_key", "").strip()
ONLINE_SUMMARY_BASE_URL = config.get("online_summary_base_url", "https://api.openai.com/v1").strip()
ONLINE_SUMMARY_MODEL = config.get("online_summary_model", "gpt-4o-mini").strip()

# 获取短路径版本，给 C++ 底层库直接使用
SHORT_LOCAL_WHISPER_MODEL_PATH = get_short_path_name(LOCAL_WHISPER_MODEL_PATH)
SHORT_DOWNLOADS_DIR = get_short_path_name(DOWNLOADS_DIR)
SHORT_TRANSCRIPTS_DIR = get_short_path_name(TRANSCRIPTS_DIR)
STORAGE_BASE = storage_base
