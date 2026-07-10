import os
import uuid
import traceback
import shutil
import time
import threading
import urllib.parse
import json
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import (
    config,
    SHORT_DOWNLOADS_DIR,
    SHORT_TRANSCRIPTS_DIR,
    CURRENT_VERSION,
    PROJECT_DIR
)
from app.core.compat import patch_subprocess_no_window
patch_subprocess_no_window()

from app.database import db
from app.core.queue_manager import queue_manager

# 导入日志模块，统一接管标准输出日志
from app.core import logger
print = logger.info

# 导入子路由
from app.routers.tasks import router as tasks_router, upload_router
from app.routers.config import router as config_router
from app.routers.system import router as system_router, start_system_background_tasks

app = FastAPI(
    title="whisperMe Local Podcast Processor",
    version=CURRENT_VERSION,
    description="本地优先的播客转录与知识提炼工具。支持小宇宙、Bilibili 等平台的播客音频下载、ASR 转录、说话人识别和 AI 总结。",
)

# 配置 CORS 跨域请求
# 允许本地任意端口（前端 9173 + 未来 AI Agent 调用）
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件挂载：允许前端直接读取下载好的原始 MP3 播客音频
app.mount("/audio", StaticFiles(directory=str(SHORT_DOWNLOADS_DIR)), name="audio")

# 引入模块化路由
app.include_router(tasks_router)
app.include_router(upload_router)
app.include_router(config_router)
app.include_router(system_router)

# --- MCP Server 挂载 ---
try:
    from app.mcp_server import mcp as mcp_server
    app.mount("/mcp", mcp_server.streamable_http_app())
    print("✅ [STARTUP] MCP Server 已挂载到 /mcp")
except ImportError:
    print("⚠️ [STARTUP] MCP SDK 未安装，跳过 MCP Server 挂载。安装命令: pip install mcp")
except Exception as e:
    print(f"⚠️ [STARTUP] MCP Server 挂载失败: {e}")

# --- 生产模式：FastAPI 直接托管前端静态文件 ---
import pathlib as _pathlib
_frontend_dist = PROJECT_DIR / "frontend" / "dist"
if _frontend_dist.is_dir():
    from fastapi.staticfiles import StaticFiles as _StaticFiles
    app.mount("/", _StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
    print(f"✅ [STARTUP] 前端静态文件已托管: {_frontend_dist}")

# --- 生产模式：优雅关闭接口 ---
import threading as _threading
@app.post("/api/shutdown")
async def shutdown():
    """优雅关闭服务（仅生产模式使用）"""
    import signal
    _threading.Thread(target=lambda: (time.sleep(0.5), os.kill(os.getpid(), signal.SIGTERM)), daemon=True).start()
    return {"message": "whisperMe is shutting down..."}

# --- 智能声纹特征与大模型命名推理引擎 ---
from app.core.speaker import auto_rename_speakers, apply_interjection_labels

# --- 异步后台工作引擎 ---
from app.core.pipeline import run_podcast_pipeline

# --- 自动清理逻辑 ---

def run_auto_cleanup():
    from datetime import datetime
    current_cfg = config
    if not current_cfg.get("enable_auto_cleanup", False):
        return
        
    threshold_days = int(current_cfg.get("cleanup_threshold_days", 30))
    print(f"🧹 [Auto Cleanup] Starting audio file check. Threshold: {threshold_days} days.")
    
    try:
        all_tasks = db.get_all_tasks()
        now = datetime.now()
        cleaned_count = 0
        
        for task in all_tasks:
            audio_url = task.get("audio_url")
            if not audio_url:
                continue
                
            created_at_str = task.get("created_at")
            if not created_at_str:
                continue
                
            try:
                cleaned_date_str = created_at_str
                if "+" in cleaned_date_str:
                    cleaned_date_str = cleaned_date_str.split("+")[0]
                elif "-" in cleaned_date_str and "T" in cleaned_date_str and len(cleaned_date_str) > 19:
                    cleaned_date_str = cleaned_date_str[:19]
                    
                created_dt = datetime.strptime(cleaned_date_str[:19], "%Y-%m-%dT%H:%M:%S")
                age_days = (now - created_dt).days
                
                if age_days >= threshold_days:
                    filename = os.path.basename(audio_url)
                    
                    other_tasks = [t for t in all_tasks if t.get("id") != task["id"]]
                    is_shared_with_younger = False
                    for ot in other_tasks:
                        ot_audio = ot.get("audio_url")
                        if ot_audio and os.path.basename(ot_audio) == filename:
                            ot_created = ot.get("created_at")
                            if ot_created:
                                if "+" in ot_created:
                                    ot_created = ot_created.split("+")[0]
                                ot_dt = datetime.strptime(ot_created[:19], "%Y-%m-%dT%H:%M:%S")
                                if (now - ot_dt).days < threshold_days:
                                    is_shared_with_younger = True
                                    break
                                    
                    if not is_shared_with_younger:
                        local_file_path = os.path.join(SHORT_DOWNLOADS_DIR, filename)
                        if os.path.exists(local_file_path):
                            try:
                                os.remove(local_file_path)
                                print(f"🗑️ [Auto Cleanup] Cleaned up old audio file: {local_file_path}")
                            except Exception as e:
                                print(f"⚠️ [Auto Cleanup] Failed to delete file: {e}")
                                
                    db.update_task_field(task["id"], audio_url="")
                    cleaned_count += 1
            except Exception as parse_err:
                print(f"⚠️ [Auto Cleanup] Error processing task {task.get('id')} date: {parse_err}")
                
        if cleaned_count > 0:
            print(f"🧹 [Auto Cleanup] Done. Cleaned up {cleaned_count} audio files.")
    except Exception as e:
        print(f"❌ [Auto Cleanup] Error checking tasks: {e}")

def background_auto_cleanup_loop():
    """后台独立线程，启动 5 秒后及此后每隔 1 小时自动执行一次音频清理检测"""
    time.sleep(5)
    while True:
        try:
            run_auto_cleanup()
        except Exception as e:
            print(f"⚠️ [Auto Cleanup Thread Error] {e}")
        time.sleep(3600)

# --- App 启动生命周期管理 ---

@app.on_event("startup")
def startup_event():
    # 0. 依赖检查
    from app.core.ffmpeg import get_ffmpeg_info, get_install_hint
    from app.config import FFMPEG_PATH
    ffmpeg_info = get_ffmpeg_info(FFMPEG_PATH)
    if ffmpeg_info["available"]:
        print(f"[STARTUP] FFmpeg: {ffmpeg_info['version']}")
        print(f"[STARTUP] FFmpeg path: {ffmpeg_info['path']}")
    else:
        print("[STARTUP WARNING] FFmpeg not found!")
        print(get_install_hint())
        print("[STARTUP WARNING] Audio download and transcription will not work until FFmpeg is installed.")

    # 0.1 启动后台独立性能监控线程 (来自 routers.system)
    start_system_background_tasks()
    print("✅ [STARTUP] 独立后台性能监控哨兵已上线！")
    
    # 0.5 启动自动音频清理检查线程
    threading.Thread(target=background_auto_cleanup_loop, daemon=True).start()
    print("✅ [STARTUP] 独立后台音频文件自动清理哨兵已上线！")
    
    # 0.8 预加载 PyAnnote 声纹模型
    from app.core.transcriber import model_cache_manager
    threading.Thread(target=model_cache_manager.preload_models, daemon=True).start()
    
    # 1. 启动队列管理器并绑定管道处理器
    queue_manager.start(run_podcast_pipeline)
    
    # 2. 自动恢复数据库中因服务重启而中断的未完成/排队任务，并重入队列
    try:
        tasks = db.get_all_tasks()
        requeued_count = 0
        for t in tasks:
            status = t.get("status")
            if status in ["pending", "downloading", "transcribing", "summarizing"]:
                db.update_task_field(
                    t["id"],
                    status="pending",
                    progress=0.0,
                    error_message=None
                )
                
                # 重回队列
                queue_manager.add_task(t["id"], t["url"])
                requeued_count += 1
                print(f"🔄 [STARTUP] 检测到未完成任务，已自动重新入队: {t.get('title') or t.get('id')} | URL: {t.get('url')}")
        print(f"✅ [STARTUP] 成功恢复并重新排队 {requeued_count} 个未完成任务。")
    except Exception as e:
        print(f"❌ [STARTUP] 恢复未完成任务失败: {e}")

    # 3. 运行历史任务语气助词发言人自动标记迁移 (已修复 SQLite _write_data 写入 Bug)
    try:
        tasks = db.get_all_tasks()
        interjection_chars = set("嗯对啊哦吧呢呀啦哈哼嗨呗嘛呃喔呦哎对好的噢唏嚯啥呀么）—（,，.。?？!！谢拜行了")
        for t in tasks:
            full_t = db.get_task(t["id"])
            if not full_t: continue
            transcript = full_t.get("transcript", [])
            if not transcript:
                continue
            
            speaker_texts = {}
            for seg in transcript:
                sp = seg.get("speaker")
                if not sp:
                    continue
                text = seg.get("text", "").strip()
                speaker_texts[sp] = speaker_texts.get(sp, "") + text
                
            mappings = full_t.get("speaker_mappings", {})
            task_modified = False
            for sp, full_text in speaker_texts.items():
                if sp in mappings and mappings[sp] and mappings[sp] != sp:
                    continue
                
                pure_text = "".join([c for c in full_text if c.strip()])
                if pure_text == "" or set(pure_text).issubset(interjection_chars):
                    mappings[sp] = "语气词发言人"
                    task_modified = True
                    
            if task_modified:
                db.update_task_field(t["id"], speaker_mappings=mappings)
                print(f"🏷️ [STARTUP MIGRATION] 自动为任务 {t.get('title') or t.get('id')} 中的发言人标记 '语气词发言人'")
    except Exception as migration_ex:
        print(f"❌ [STARTUP MIGRATION] 语气词发言人迁移失败: {migration_ex}")
