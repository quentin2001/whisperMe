import os
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import (
    config,
    save_config,
    load_config as load_config_dict
)
from app.core.prompt_manager import load_prompt, save_prompt, get_templates, get_template_prompt
from app.core.notifier import PodcastNotifier
from app.core import logger
print = logger.info

router = APIRouter(prefix="/api", tags=["config"])

class UpdateConfigRequest(BaseModel):
    ffmpeg_path: str
    ffmpeg_bin_dir: str
    local_whisper_model_path: str
    hf_token: str
    ollama_url: str
    ollama_model: str
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_sender: str
    notification_email: str
    enable_win_notification: bool
    enable_email_notification: bool = False
    asr_mode: str = "local"
    online_asr_provider: str = "mimo"
    online_api_key: str = ""
    online_base_url: str = ""
    online_model: str = ""
    custom_asr_endpoint: str = ""
    custom_asr_method: str = "POST"
    custom_asr_headers: str = "{}"
    custom_asr_body_template: str = ""
    custom_asr_response_jsonpath: str = "$.data.text"
    custom_asr_timestamp_jsonpath: str = ""
    custom_asr_audio_format: str = "mp3"
    custom_asr_chunk_duration: int = 60
    summary_mode: str = "local"
    online_summary_api_key: str = ""
    online_summary_base_url: str = ""
    online_summary_model: str = ""
    enable_llm_semantic_sewing: bool = False
    webhook_url: str = ""
    custom_storage_dir: str = ""
    language: str = "en"
    enable_autostart_windows: bool = False
    enable_speaker_inference: bool = False

class TestConfigRequest(BaseModel):
    api_key: str = ""
    base_url: str = ""
    model: str = ""

@router.post("/config/test/asr")
def test_asr_connection(req: TestConfigRequest):
    try:
        # 简单探测基础域名连通性
        test_url = req.base_url.rstrip("/") + "/models"
        headers = {"Authorization": f"Bearer {req.api_key}"}
        # 如果是 mimo，可能没有 /models 接口，我们只做基本的网络联通探测
        if "mimo" in req.base_url.lower():
            test_url = req.base_url.rstrip("/")
        resp = httpx.get(test_url, headers=headers, timeout=5.0)
        if resp.status_code in [200, 401, 403, 404]: # 404 is allowed because root endpoints of APIs often have no GET route
            return {"success": True, "message": "连接成功"}
        return {"success": False, "message": f"服务器返回异常状态码: {resp.status_code}"}
    except Exception as e:
        return {"success": False, "message": f"连接失败: {str(e)}"}

class TestLocalAsrRequest(BaseModel):
    model_path: str

@router.post("/config/test/local_asr")
def test_local_asr_connection(req: TestLocalAsrRequest):
    try:
        path = req.model_path.strip()
        if not path:
            return {"success": False, "message": "错误：为了避免意外的巨型文件下载，本地模式必须填写准确的模型绝对路径！"}
        
        if not os.path.exists(path):
            return {"success": False, "message": f"错误：未在您的电脑上找到该目录 ({path})"}
        
        # 简单验证目录下是否有关键文件
        has_config = os.path.exists(os.path.join(path, "config.yaml")) or os.path.exists(os.path.join(path, "config.json"))
        if not has_config:
            return {"success": False, "message": f"错误：目录已找到，但里面似乎没有模型文件 (缺少 config.yaml/json)"}

        # 校验 FunASR 依赖是否完好
        try:
            import funasr
            import torch
        except ImportError:
            return {"success": False, "message": "依赖缺失：当前核心极速版未包含 FunASR 与 PyTorch，请确认您下载的是否是完整版。"}

        return {"success": True, "message": "本地环境一切正常，模型路径有效！"}
    except Exception as e:
        return {"success": False, "message": f"测试异常: {str(e)}"}
 
@router.post("/config/test/llm")
def test_llm_connection(req: TestConfigRequest):
    try:
        # LLM 探测可以调用 /chat/completions 或 /models
        test_url = req.base_url.rstrip("/") + "/models"
        headers = {"Authorization": f"Bearer {req.api_key}"}
        resp = httpx.get(test_url, headers=headers, timeout=5.0)
        if resp.status_code in [200, 401, 403, 404]: # 404 is allowed because root endpoints of APIs often have no GET route
            return {"success": True, "message": "连接成功"}
        return {"success": False, "message": f"服务器返回异常状态码: {resp.status_code}"}
    except Exception as e:
        return {"success": False, "message": f"连接失败: {str(e)}"}

@router.get("/config")
def get_global_config():
    return load_config_dict()

@router.get("/asr-providers")
def list_asr_providers():
    """列出所有可用的 ASR Provider（供前端下拉选择器使用）"""
    from app.core.asr_providers import list_providers
    return list_providers()

@router.post("/config")
def update_global_config(req: UpdateConfigRequest):
    new_cfg = req.model_dump()
    save_config(new_cfg)
    
    # 强制将新变量重写回内存 config 字典中，完成实时热更新
    for k, v in new_cfg.items():
        config[k] = v
        
    # 热更新内存中的模块级变量
    import app.config
    import app.core.transcriber

    new_token = new_cfg.get("hf_token", "").strip()
    app.config.HF_TOKEN = new_token
    app.core.transcriber.HF_TOKEN = new_token

    # 热更新 FFmpeg 路径
    new_ffmpeg_path = new_cfg.get("ffmpeg_path", "").strip()
    new_ffmpeg_dir = new_cfg.get("ffmpeg_bin_dir", "").strip()
    if new_ffmpeg_path:
        app.config.FFMPEG_PATH = new_ffmpeg_path
        app.config.FFMPEG_BIN_DIR = new_ffmpeg_dir
    else:
        # 用户清空了路径，重新自动检测
        from app.core.ffmpeg import find_ffmpeg, find_ffmpeg_dir
        auto = find_ffmpeg()
        if auto:
            app.config.FFMPEG_PATH = auto
            app.config.FFMPEG_BIN_DIR = find_ffmpeg_dir() or ""
        else:
            app.config.FFMPEG_PATH = ""
            app.config.FFMPEG_BIN_DIR = ""
    
    # 重更新 HF_ENDPOINT 环境变量与 huggingface_hub constants
    if new_token and len(new_token) >= 30:
        os.environ["HF_ENDPOINT"] = "https://huggingface.co"
        try:
            import huggingface_hub.constants
            huggingface_hub.constants.ENDPOINT = "https://huggingface.co"
            huggingface_hub.constants.HUGGINGFACE_CO_URL_TEMPLATE = "https://huggingface.co/{repo_id}/resolve/{revision}/{filename}"
        except Exception:
            pass
    else:
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        try:
            import huggingface_hub.constants
            huggingface_hub.constants.ENDPOINT = "https://hf-mirror.com"
            huggingface_hub.constants.HUGGINGFACE_CO_URL_TEMPLATE = "https://hf-mirror.com/{repo_id}/resolve/{revision}/{filename}"
        except Exception:
            pass

    # 清理可能存在的历史自启动配置 (Windows / macOS)
    import sys
    import app.config
    root_dir = os.path.dirname(app.config.PROJECT_DIR)

    if sys.platform == "win32":
        try:
            startup_dir = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
            bat_path = os.path.join(startup_dir, "whisperMe-autostart.bat")
            if os.path.exists(bat_path):
                os.remove(bat_path)
        except Exception:
            pass
            
    elif sys.platform == "darwin":
        try:
            plist_dir = os.path.expanduser("~/Library/LaunchAgents")
            plist_path = os.path.join(plist_dir, "com.whisperme.autostart.plist")
            if os.path.exists(plist_path):
                os.system(f"launchctl unload -w {plist_path} >/dev/null 2>&1")
                os.remove(plist_path)
        except Exception:
            pass
        
    # 重启更新 notifier SMTP 缓存
    import app.core.notifier
    app.core.notifier.notifier = PodcastNotifier()
    
    return {"success": True}

@router.get("/prompt")
def get_prompt():
    return load_prompt()

@router.post("/prompt")
def set_prompt(req: dict):
    save_prompt(req)
    return {"status": "ok"}

@router.get("/settings/hf-token-status")
def get_hf_token_status():
    """验证 HuggingFace Token 是否有效（调用 hf-mirror.com 镜像 API）"""
    token = config.get("hf_token", "").strip()
    if not token or len(token) < 30:
        return {"status": "missing", "message": "未配置 HuggingFace Token"}

    try:
        with httpx.Client(timeout=10.0, trust_env=True) as client:
            resp = client.get(
                "https://hf-mirror.com/api/whoami-v2",
                headers={"Authorization": f"Bearer {token}"}
            )
            if resp.status_code == 200:
                data = resp.json()
                return {"status": "valid", "username": data.get("name", "unknown")}
            elif resp.status_code == 401:
                return {"status": "invalid", "message": "Token 无效或已过期"}
            else:
                return {"status": "unknown", "message": f"验证失败 (HTTP {resp.status_code})"}
    except Exception as e:
        return {"status": "unknown", "message": f"无法验证（网络异常）: {str(e)[:80]}"}

@router.get("/prompt/templates")
def list_prompt_templates():
    """列出所有内置 Prompt 模板（供前端下拉选择器使用）"""
    return get_templates()

@router.get("/prompt/template/{template_id}")
def get_prompt_template(template_id: str):
    """获取指定模板的 Prompt 内容"""
    prompt = get_template_prompt(template_id)
    if prompt is None:
        raise HTTPException(status_code=404, detail=f"模板 '{template_id}' 不存在")
    return {"id": template_id, "prompt": prompt}
