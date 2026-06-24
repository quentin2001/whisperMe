import os
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
    online_base_url: str = "https://token-plan-sgp.xiaomimimo.com/v1"
    online_model: str = "mimo-v2.5-asr"
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
    online_summary_base_url: str = "https://api.openai.com/v1"
    online_summary_model: str = "gpt-4o-mini"
    enable_llm_semantic_sewing: bool = False
    webhook_url: str = ""
    custom_storage_dir: str = ""
    language: str = "en"

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
    new_cfg = req.dict()
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
