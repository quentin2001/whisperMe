import os
import sys
import io
import json
import ctypes
from pathlib import Path

# ==================== 🛡️ 钢铁防御层 0：NumPy 2.0 兼容性补焊 ====================
# 延迟导入：仅在 numpy 已安装时打补丁，在线模式不需要 numpy
try:
    import numpy as np
    if not hasattr(np, "NaN"):
        np.NaN = np.nan
    if not hasattr(np, "NAN"):
        np.NAN = np.nan
    if not hasattr(np, "float"):
        np.float = float
    if not hasattr(np, "int"):
        np.int = int
except ImportError:
    pass

# ==================== 🛡️ 钢铁防御层 1：强行重写控制台物理输出流 ====================
# 仅在编码不是 UTF-8 时替换，避免破坏 pytest 等工具的输出捕获机制
if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')
if hasattr(sys.stderr, "buffer") and getattr(sys.stderr, "encoding", "").lower() != "utf-8":
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

# ==================== Pydantic 配置模型校验 ====================
from pydantic import BaseModel, Field

class AppConfigModel(BaseModel):
    ffmpeg_path: str = ""
    ffmpeg_bin_dir: str = ""
    local_whisper_model_path: str = str((PROJECT_DIR / "models" / "funasr").resolve()).replace("\\", "/")
    local_whisper_model_size: str = "large-v3-turbo"
    local_model_idle_timeout: int = 300
    hf_token: str = ""
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b-instruct"
    smtp_server: str = "smtp.qq.com"
    smtp_port: int = 465
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_sender: str = ""
    notification_email: str = ""
    enable_win_notification: bool = True
    enable_email_notification: bool = False
    asr_mode: str = "online"
    online_asr_provider: str = "mimo"
    online_api_key: str = ""
    online_base_url: str = Field(default="")
    online_model: str = Field(default="")
    custom_asr_endpoint: str = ""
    custom_asr_method: str = "POST"
    custom_asr_headers: str = "{}"
    custom_asr_body_template: str = ""
    custom_asr_response_jsonpath: str = "$.data.text"
    custom_asr_timestamp_jsonpath: str = ""
    custom_asr_audio_format: str = "mp3"
    custom_asr_chunk_duration: int = 60
    summary_mode: str = "online"
    online_summary_api_key: str = ""
    online_summary_base_url: str = Field(default="")
    online_summary_model: str = Field(default="")
    enable_llm_semantic_sewing: bool = False
    webhook_url: str = ""
    custom_storage_dir: str = ""
    language: str = "en"
    enable_autostart_windows: bool = False
    enable_auto_cleanup: bool = False
    cleanup_threshold_days: int = 30
    max_concurrent_tasks: int = 0  # 0 = 自动检测 GPU 显存决定，1 = 串行，2+ = 并行
    enable_speaker_inference: bool = False
    preload_models: bool = True
    use_mp3_chunks: bool = False
    use_hf_mirror: bool = True

# 加载全局配置文件
def load_config() -> dict:
    default_config = AppConfigModel().model_dump()

    if not CONFIG_FILE_PATH.exists():
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        return default_config
    
    try:
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        # 默认本地 ASR 路径自动转换为绝对路径
        if not loaded.get("local_whisper_model_path"):
            loaded["local_whisper_model_path"] = str((PROJECT_DIR / "models" / "funasr").resolve()).replace("\\", "/")

        # ==================== 自动迁移：旧配置 → online_asr_provider 字段 ====================
        if "online_asr_provider" not in loaded:
            base_url = loaded.get("online_base_url", "")
            if "xiaomimimo.com" in base_url:
                loaded["online_asr_provider"] = "mimo"
            elif "openai.com" in base_url:
                loaded["online_asr_provider"] = "openai"
            else:
                loaded["online_asr_provider"] = "mimo"  # 默认 fallback
            print(f"🔄 [CONFIG] 自动迁移: online_asr_provider → '{loaded['online_asr_provider']}'")

        # 使用 Pydantic 进行类型与默认值补全校验
        validated = AppConfigModel.model_validate(loaded)
        validated_dict = validated.model_dump()
        
        # 检查是否有新增字段需要回写
        if len(loaded) != len(validated_dict):
            with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(validated_dict, f, ensure_ascii=False, indent=2)
                
        return validated_dict
    except Exception as e:
        print(f"⚠️ [CONFIG] 配置文件解析异常，将使用默认配置: {e}")
        return default_config

# 更新全局配置文件
def save_config(new_config: dict):
    try:
        # 保存前进行 Pydantic 校验
        validated = AppConfigModel.model_validate(new_config)
        validated_dict = validated.model_dump()
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(validated_dict, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ [CONFIG] 配置文件校验并保存失败: {e}")
        # 退避保存原生字典
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(new_config, f, ensure_ascii=False, indent=2)

config = load_config()

# ==================== 🛡️ 钢铁防御层 2：提取 venv 内的 NVIDIA DLL 并硬焊进 PATH ====================
# 后端 venv 路径
venv_base = BACKEND_DIR / "venv"
if not venv_base.exists():
    # 兼容根目录下的 venv
    venv_base = PROJECT_DIR / "venv"

if sys.platform == "win32":
    _site_packages = venv_base / "Lib" / "site-packages"
else:
    # macOS/Linux: lib/python3.x/site-packages
    import glob as _glob
    _matches = list(_glob.glob(str(venv_base / "lib" / "python*" / "site-packages")))
    _site_packages = Path(_matches[0]) if _matches else venv_base / "lib" / "site-packages"

cublas_bin_path = _site_packages / "nvidia" / "cublas" / "bin"
cudnn_bin_path = _site_packages / "nvidia" / "cudnn" / "bin"

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
HF_CACHE_DIR = storage_base / "models" / "huggingface"

# 确保文件夹存在
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
TEMP_SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
HF_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 物理转换为 8.3 短路径（仅 Windows 需要，规避中文路径问题）
SHORT_TEMP_DIR = get_short_path_name(TEMP_SANDBOX_DIR)
SHORT_HF_CACHE_DIR = get_short_path_name(HF_CACHE_DIR)

if sys.platform == "win32":
    # 只重定向临时目录，不劫持用户目录（避免 .matplotlib/.cache/NVIDIA/torch 写入 temp_sandbox）
    for env_key in ["TEMP", "TMP"]:
        os.environ[env_key] = SHORT_TEMP_DIR
else:
    # macOS/Linux: 只设置 TEMP/TMP，不动 HOME（会破坏子进程的配置解析）
    os.environ["TEMP"] = str(TEMP_SANDBOX_DIR)
    os.environ["TMP"] = str(TEMP_SANDBOX_DIR)

os.environ["HF_HOME"] = SHORT_HF_CACHE_DIR
os.environ["HF_HUB_CACHE"] = SHORT_HF_CACHE_DIR
os.environ["HF_ASSETS_CACHE"] = SHORT_HF_CACHE_DIR
os.environ["XDG_CACHE_HOME"] = SHORT_HF_CACHE_DIR
# Use hf-mirror.com by default if in China region, since huggingface.co is often blocked.
import locale
def is_china_region():
    try:
        if sys.platform == 'win32':
            langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            return langid in (0x0804, 0x0404, 0x0c04, 0x1004, 0x1404)
        else:
            loc = locale.getdefaultlocale()
            if loc and loc[0] and 'CN' in loc[0]:
                return True
    except Exception:
        pass
    return False

use_hf_mirror = config.get("use_hf_mirror", is_china_region())
if use_hf_mirror and not os.environ.get("HF_ENDPOINT"):
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    print("🌍 [CONFIG] 检测到位于中国大陆地区，自动启用 HF 镜像站 (https://hf-mirror.com)")

# huggingface_hub API 动态配置声明
HF_TOKEN = config.get("hf_token", "").strip()
endpoint_url = os.environ.get("HF_ENDPOINT", "https://huggingface.co" if not use_hf_mirror else "https://hf-mirror.com")
os.environ["HF_ENDPOINT"] = endpoint_url
os.environ["HF_HOME"] = SHORT_HF_CACHE_DIR
os.environ["HF_HUB_CACHE"] = SHORT_HF_CACHE_DIR
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "True"
if HF_TOKEN:
    os.environ["HF_TOKEN"] = HF_TOKEN


# ==================== 导出全局可用变量 ====================
# FFmpeg 自动发现：config 为空时自动检测系统安装
from app.core.ffmpeg import find_ffmpeg, find_ffmpeg_dir
FFMPEG_PATH = config.get("ffmpeg_path") or ""
FFMPEG_BIN_DIR = config.get("ffmpeg_bin_dir") or ""
if not FFMPEG_PATH or not os.path.isfile(FFMPEG_PATH):
    _auto_ffmpeg = find_ffmpeg()
    if _auto_ffmpeg:
        FFMPEG_PATH = _auto_ffmpeg
        FFMPEG_BIN_DIR = find_ffmpeg_dir() or ""
        config["ffmpeg_path"] = FFMPEG_PATH
        config["ffmpeg_bin_dir"] = FFMPEG_BIN_DIR
        print(f"[CONFIG] FFmpeg auto-detected: {FFMPEG_PATH}")
    else:
        print("[CONFIG WARNING] FFmpeg not found! Some features will not work.")
else:
    print(f"[CONFIG] FFmpeg loaded from config: {FFMPEG_PATH}")

LOCAL_WHISPER_MODEL_PATH = config.get("local_whisper_model_path")

OLLAMA_URL = config.get("ollama_url", "http://localhost:11434")
OLLAMA_MODEL = config.get("ollama_model", "qwen2.5:7b-instruct")

SUMMARY_MODE = config.get("summary_mode", "online")
ONLINE_SUMMARY_API_KEY = config.get("online_summary_api_key", "").strip()
ONLINE_SUMMARY_BASE_URL = config.get("online_summary_base_url", "").strip()
ONLINE_SUMMARY_MODEL = config.get("online_summary_model", "").strip()

# 获取短路径版本，给 C++ 底层库直接使用
SHORT_LOCAL_WHISPER_MODEL_PATH = get_short_path_name(LOCAL_WHISPER_MODEL_PATH)
SHORT_DOWNLOADS_DIR = get_short_path_name(DOWNLOADS_DIR)
SHORT_TRANSCRIPTS_DIR = get_short_path_name(TRANSCRIPTS_DIR)
STORAGE_BASE = storage_base

# ==================== 📦 软件版本定义 ====================
_VERSION_FILE = PROJECT_DIR / "VERSION"
if _VERSION_FILE.exists():
    CURRENT_VERSION = _VERSION_FILE.read_text(encoding="utf-8").strip()
else:
    CURRENT_VERSION = "1.0.1"

