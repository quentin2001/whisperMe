import os
import uuid
import shutil
import math
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from app.config import (
    config,
    SHORT_DOWNLOADS_DIR,
    PROJECT_DIR
)
from app.database import db
from app.core.downloader import PodcastDownloader
from app.core.transcriber import PodcastTranscriber
from app.core.summarizer import PodcastSummarizer
from app.core.queue_manager import queue_manager

from app.core import logger
print = logger.info

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# We instantiate downloader, transcriber, summarizer or import them from a shared location if needed.
# Since main.py instantiated them globally, we can do the same here or import them.
# Let's import them or instantiate them here. In main.py:
# downloader = PodcastDownloader()
# transcriber = PodcastTranscriber()
# summarizer = PodcastSummarizer()
# We will initialize them here to avoid circular imports.
downloader = PodcastDownloader()
transcriber = PodcastTranscriber()
summarizer = PodcastSummarizer()

# --- Pydantic Schemas ---
class CreateTaskRequest(BaseModel):
    url: str
    asr_mode: str = "local"

class RenameSpeakerRequest(BaseModel):
    speaker_id: str
    new_name: str

# --- Helper Functions ---
def check_low_disk_space():
    try:
        from app.config import STORAGE_BASE
        check_path = STORAGE_BASE if (STORAGE_BASE and os.path.exists(STORAGE_BASE)) else PROJECT_DIR
        if os.path.exists(check_path):
            total, used, free = shutil.disk_usage(check_path)
            # 2.0 GB threshold = 2 * 1024 * 1024 * 1024
            if free < 2 * 1024 * 1024 * 1024:
                return f"警告：当前设置中的存储路径或系统盘剩余空间不足 2.0 GB（仅剩 {free / (1024**3):.2f} GB），可能会导致后续播客音频下载或转录失败，请及时清理磁盘！"
    except Exception as e:
        print(f"⚠️ [LOG ERROR] Failed to check disk space: {e}")
    return None

def save_speaker_fingerprint(name: str, embedding: list[float]):
    """保存声纹到全局 SQLite 声纹库"""
    if not name or not embedding:
        return
    try:
        db.upsert_speaker(name, embedding)
        print(f"💾 [LOG] 声纹特征成功写入全局声纹库: {name}")
    except Exception as e:
        print(f"⚠️ [LOG] 写入声纹特征库失败: {e}")

def sanitize_floats(obj):
    if isinstance(obj, dict):
        return {k: sanitize_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_floats(x) for x in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
    return obj

# --- API Endpoints ---

@router.get("")
def list_tasks():
    tasks = db.get_all_tasks()
    # 动态注入排队位置
    for t in tasks:
        if t.get("status") == "pending":
            pos = queue_manager.get_queue_position(t.get("id"))
            t["queue_position"] = pos
    return tasks

# --- 全局声纹库 API（必须在 /{task_id} 之前定义，避免被路径参数拦截）---

class MergeSpeakerRequest(BaseModel):
    source_name: str
    target_name: str

class ForgetSpeakerRequest(BaseModel):
    name: str

@router.get("/speakers/list")
def list_speakers():
    """获取全局声纹库列表（不含 embedding 向量）"""
    speakers = db.get_all_speakers()
    return {"speakers": speakers}

@router.post("/speakers/merge")
def merge_speakers(req: MergeSpeakerRequest):
    """合并两个说话人声纹"""
    if req.source_name == req.target_name:
        raise HTTPException(status_code=400, detail="不能合并同一个说话人")
    success = db.merge_speakers(req.source_name, req.target_name)
    if not success:
        raise HTTPException(status_code=404, detail="未找到指定说话人")
    return {"success": True, "message": f"已将 '{req.source_name}' 合并到 '{req.target_name}'"}

@router.post("/speakers/forget")
def forget_speaker(req: ForgetSpeakerRequest):
    """从全局声纹库中忘记某说话人"""
    success = db.delete_speaker(req.name)
    if not success:
        raise HTTPException(status_code=404, detail="未找到指定说话人")
    return {"success": True, "message": f"已从声纹库中移除 '{req.name}'"}

@router.get("/{task_id}")
def get_task_details(task_id: str):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="未找到该任务")
    # 动态注入排队位置
    if task.get("status") == "pending":
        pos = queue_manager.get_queue_position(task.get("id"))
        task["queue_position"] = pos
        
    # 注入段落与沉淀状态
    if task.get("status") == "completed":
        try:
            paragraphs = db.get_paragraphs_by_podcast(task_id)
            is_old_format = paragraphs and len(paragraphs) > 0 and ("sentences" not in paragraphs[0] or not isinstance(paragraphs[0].get("sentences"), list))
            if (not paragraphs or is_old_format) and task.get("transcript"):
                paragraphs = transcriber.cluster_segments_to_paragraphs(task_id, task.get("transcript"))
                db.delete_paragraphs_by_podcast(task_id)
                db.add_paragraphs(paragraphs)
            
            # Check sedimented status
            podcast_cards = db.get_cards_by_podcast(task_id)
            sedimented_paragraph_ids = {c["paragraph_id"] for c in podcast_cards}
            for p in paragraphs:
                p["sedimented"] = p["id"] in sedimented_paragraph_ids
                
            task["paragraphs"] = paragraphs
        except Exception as e:
            print(f"⚠️ [LOG ERROR] Failed to inject paragraphs: {e}")
            task["paragraphs"] = []
    else:
        task["paragraphs"] = []
        
    return sanitize_floats(task)

@router.post("")
def create_task(req: CreateTaskRequest):
    task_id = str(uuid.uuid4())
    curr_summary_mode = config.get("summary_mode", "local")
    db.add_task(task_id, req.url, asr_mode=req.asr_mode, summary_mode=curr_summary_mode)
    
    # 放入全局单例队列管理器进行排队串行处理，不再直接塞给 background_tasks 并行跑
    queue_manager.add_task(task_id, req.url)
    
    res = {"task_id": task_id, "status": "pending"}
    warning = check_low_disk_space()
    if warning:
        res["warning"] = warning
    return res

@router.delete("/{task_id}")
def delete_task(task_id: str):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
        
    # 如果任务处于排队或运行状态，先将其置为取消状态，触发后台工作线程中断
    if task.get("status") in ["pending", "downloading", "transcribing", "summarizing"]:
        db.update_task(task_id, status="cancelled", progress=100.0, error_message="任务在删除前已被取消。")
        print(f"🚫 [LOG] 正在运行的任务 {task_id} 在被删除前已被取消。")
        
    # 物理清除下载的 MP3 文件以释放硬盘，前提是该音频没有被其他任务共享
    audio_url = task.get("audio_url")
    if audio_url:
        filename = os.path.basename(audio_url)
        
        # 扫描是否有其他任务也在使用这个文件名
        other_tasks = [t for t in db.get_all_tasks() if t.get("id") != task_id]
        is_shared = False
        for ot in other_tasks:
            ot_audio = ot.get("audio_url")
            if ot_audio and os.path.basename(ot_audio) == filename:
                is_shared = True
                break
                
        if is_shared:
            print(f"ℹ️ [LOG] 任务删除 - 音频文件 {filename} 被其他任务共享，跳过物理删除。")
        else:
            local_file_path = os.path.join(SHORT_DOWNLOADS_DIR, filename)
            if os.path.exists(local_file_path):
                try:
                    os.remove(local_file_path)
                    print(f"🗑️ [LOG] 任务删除 - 已物理清除音频文件: {local_file_path}")
                except Exception as e:
                    print(f"⚠️ [LOG 警告] 无法删除物理音频: {e}")

    success = db.delete_task(task_id)
    return {"success": success}

@router.post("/{task_id}/cancel")
def cancel_task(task_id: str):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
        
    if task.get("status") in ["pending", "downloading", "transcribing", "summarizing"]:
        db.update_task(task_id, status="cancelled", progress=100.0, error_message="任务已被手动取消。")
        print(f"🚫 [LOG] 任务 {task_id} 已被手动取消。")
        return {"success": True, "message": "任务已被手动取消。"}
    
    return {"success": False, "message": f"当前任务状态为 {task.get('status')}，不可取消。"}

@router.post("/{task_id}/redownload")
def redownload_task_audio(task_id: str, background_tasks: BackgroundTasks):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
        
    audio_url = task.get("audio_url")
    filename = os.path.basename(audio_url) if audio_url else None
    local_file_path = os.path.join(SHORT_DOWNLOADS_DIR, filename) if filename else None
    
    if local_file_path and os.path.exists(local_file_path):
        return {"success": True, "message": "音频文件已存在，无需重新下载"}
        
    # 在数据库中初始化修复状态和进度
    db.update_task(task_id, restoring=True, restore_progress=0.0)
        
    # 启动后台任务进行下载修复
    def do_redownload():
        try:
            print(f"📥 [LOG] 启动后台音频修复重新下载, 原始链接: {task['url']}")
            
            def restore_progress_callback(percent):
                db.update_task(task_id, restore_progress=round(percent, 1))
                
            local_path, metadata = downloader.download_url_audio(task['url'], progress_callback=restore_progress_callback)
            
            downloaded_filename = os.path.basename(local_path)
            # 如果之前有文件名且不一致，重命名为原来的文件名，否则直接使用新下载的文件名
            if filename and downloaded_filename != filename:
                downloaded_expected_path = os.path.join(SHORT_DOWNLOADS_DIR, downloaded_filename)
                expected_path = os.path.join(SHORT_DOWNLOADS_DIR, filename)
                if os.path.exists(downloaded_expected_path):
                    shutil.move(downloaded_expected_path, expected_path)
                final_filename = filename
            else:
                final_filename = downloaded_filename
                
            new_audio_url = f"/audio/{final_filename}"
            print(f"✅ [LOG] 音频文件修复重新下载成功: {final_filename}")
            db.update_task(task_id, audio_url=new_audio_url, restoring=False, restore_progress=100.0)
        except Exception as e:
            print(f"❌ [LOG] 音频文件修复重新下载失败: {e}")
            db.update_task(task_id, restoring=False, restore_progress=0.0)
            
    background_tasks.add_task(do_redownload)
    return {"success": True, "message": "已在后台启动音频文件下载修复"}

@router.post("/{task_id}/speaker/rename")
def rename_speaker(task_id: str, req: RenameSpeakerRequest):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="未找到任务")
        
    mappings = task.get("speaker_mappings", {})
    mappings[req.speaker_id] = req.new_name
    db.update_task(task_id, speaker_mappings=mappings)
    
    # 将手动命名的发言人声纹特征写入本地声纹库
    speaker_embs = task.get("speaker_embeddings", {})
    emb = speaker_embs.get(req.speaker_id)
    if emb:
        save_speaker_fingerprint(req.new_name, emb)
        
    return {"success": True, "speaker_mappings": mappings}

@router.post("/{task_id}/summary/regenerate")
def regenerate_summary(task_id: str, background_tasks: BackgroundTasks):
    """
    当修改了发言人昵称或需要重新总结时，可手动发起 Ollama 重建总结任务
    """
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="未找到任务")
    
    if task["status"] != "completed" and task["status"] != "failed":
        raise HTTPException(status_code=400, detail="任务处于非就绪状态，无法重新生成总结")

    def run_re_summarize():
        try:
            db.update_task(task_id, status="summarizing", progress=80.0)
            summary_report = summarizer.summarize(
                task["metadata"], 
                task["transcript"], 
                speaker_mappings=task.get("speaker_mappings"),
                summary_mode=task.get("summary_mode", "local")
            )
            db.update_task(task_id, status="completed", summary=summary_report, progress=100.0)
        except Exception as ex:
            db.update_task(task_id, status="failed", error_message=str(ex), progress=100.0)

    background_tasks.add_task(run_re_summarize)
    return {"status": "summarizing"}

@router.post("/{task_id}/metadata/refresh")
def refresh_metadata(task_id: str):
    """
    重新抓取播客的最新点赞数、评论数、简介/Shownotes等，实时同步到本地库中
    """
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="未找到任务")
    
    url = task.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="本地上传任务没有源链接，无法刷新元数据")
        
    try:
        new_metadata = downloader.parse_metadata(url)
        
        # 合并最新的元数据
        old_meta = task.get("metadata", {}) or {}
        for k, v in new_metadata.items():
            if v is not None:
                old_meta[k] = v
                
        # 更新数据库
        updated_t = db.update_task(
            task_id,
            metadata=old_meta,
            title=new_metadata.get("title", task.get("title")),
            podcast_name=new_metadata.get("podcast_name", task.get("podcast_name")),
            image_url=new_metadata.get("image_url", task.get("image_url"))
        )
        return {
            "success": True, 
            "task": {
                "id": updated_t.get("id"),
                "url": updated_t.get("url"),
                "asr_mode": updated_t.get("asr_mode", "local"),
                "summary_mode": updated_t.get("summary_mode", "local"),
                "title": updated_t.get("title", "未命名任务"),
                "podcast_name": updated_t.get("podcast_name", "未知播客"),
                "status": updated_t.get("status", "pending"),
                "progress": updated_t.get("progress", 0),
                "error_message": updated_t.get("error_message"),
                "created_at": updated_t.get("created_at"),
                "image_url": updated_t.get("image_url"),
                "metadata": updated_t.get("metadata"),
                "audio_url": updated_t.get("audio_url")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新元数据失败: {str(e)}")

# --- Audio Upload is POST /api/upload. It is slightly different prefix but relates to tasks ---
upload_router = APIRouter(prefix="/api/upload", tags=["upload"])

@upload_router.post("")
def upload_audio(file: UploadFile = File(...), asr_mode: str = Form("local")):
    # 1. 验证文件后缀
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"]:
        raise HTTPException(status_code=400, detail="不支持的音频格式。仅支持 mp3, wav, m4a, aac, flac, ogg 等格式。")
    
    # 2. 生成唯一的任务 ID 和文件名
    task_id = str(uuid.uuid4())
    safe_filename = f"uploaded_{task_id}{ext}"
    local_path = os.path.join(SHORT_DOWNLOADS_DIR, safe_filename)
    
    # 3. 保存上传文件到 downloads 目录
    try:
        with open(local_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存上传音频文件失败: {str(e)}")
        
    # 4. 创建任务并以本地导入的元数据初始化
    curr_summary_mode = config.get("summary_mode", "local")
    db.add_task(task_id, local_path, asr_mode=asr_mode, summary_mode=curr_summary_mode)
    
    name_without_ext = os.path.splitext(file.filename)[0]
    db.update_task(
        task_id,
        title=name_without_ext,
        podcast_name="本地导入",
        metadata={
            "title": name_without_ext,
            "podcast_name": "本地导入",
            "shownotes": "用户上传的本地音频文件，完全离线处理。",
            "like_count": 0,
            "comment_count": 0,
            "comments": [],
            "source": "local"
        }
    )
    
    # 5. 放入全局单例队列管理器进行排队串行处理
    queue_manager.add_task(task_id, local_path)
    
    res = {"task_id": task_id, "status": "pending"}
    warning = check_low_disk_space()
    if warning:
        res["warning"] = warning
    return res
