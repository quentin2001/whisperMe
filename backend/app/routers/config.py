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

    # 自动启动管理 (Windows / macOS)
    import sys
    import app.config
    root_dir = os.path.dirname(app.config.PROJECT_DIR)  # PROJECT_DIR is backend, parent is root

    if sys.platform == "win32":
        try:
            startup_dir = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
            bat_path = os.path.join(startup_dir, "whisperMe-autostart.bat")
            if new_cfg.get("enable_autostart_windows"):
                start_bat = os.path.join(root_dir, "start.bat")
                if os.path.exists(start_bat):
                    with open(bat_path, "w", encoding="utf-8") as f:
                        f.write(f'@echo off\ncd /d "{root_dir}"\nstart "" /b cmd /c "start.bat"\n')
            else:
                if os.path.exists(bat_path):
                    os.remove(bat_path)
        except Exception as e:
            print(f"❌ [STARTUP] Failed to configure Windows autostart: {e}")
            
    elif sys.platform == "darwin":
        try:
            import platform
            plist_dir = os.path.expanduser("~/Library/LaunchAgents")
            os.makedirs(plist_dir, exist_ok=True)
            plist_path = os.path.join(plist_dir, "com.whisperme.autostart.plist")
            
            if new_cfg.get("enable_autostart_windows"):
                start_sh = os.path.join(root_dir, "start.sh")
                if os.path.exists(start_sh):
                    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.whisperme.autostart</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>{start_sh}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>{root_dir}</string>
</dict>
</plist>"""
                    with open(plist_path, "w", encoding="utf-8") as f:
                        f.write(plist_content)
                    os.system(f"launchctl load -w {plist_path} >/dev/null 2>&1")
            else:
                if os.path.exists(plist_path):
                    os.system(f"launchctl unload -w {plist_path} >/dev/null 2>&1")
                    os.remove(plist_path)
        except Exception as e:
            print(f"❌ [STARTUP] Failed to configure macOS autostart: {e}")
        
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
