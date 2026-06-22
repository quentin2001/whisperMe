import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import (
    config,
    save_config,
    load_config as load_config_dict
)
from app.core.prompt_manager import load_prompt, save_prompt
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
    online_api_key: str = ""
    online_base_url: str = "https://token-plan-sgp.xiaomimimo.com/v1"
    online_model: str = "mimo-v2.5-asr"
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

@router.post("/config")
def update_global_config(req: UpdateConfigRequest):
    new_cfg = req.dict()
    save_config(new_cfg)
    
    # 强制将新变量重写回内存 config 字典中，完成实时热更新
    for k, v in new_cfg.items():
        config[k] = v
        
    # 重更新 HF_TOKEN 内存缓存
    import app.config
    import app.core.transcriber
    
    new_token = new_cfg.get("hf_token", "").strip()
    app.config.HF_TOKEN = new_token
    app.core.transcriber.HF_TOKEN = new_token
    
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
