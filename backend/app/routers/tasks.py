import os
import re
import uuid
import shutil
import socket
import math
from urllib.parse import urlparse
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from app.config import (
    config,
    load_config,
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

# --- SSRF 防护：URL 白名单校验 ---
PRIVATE_IP_PATTERNS = [
    re.compile(r"^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$"),
    re.compile(r"^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$"),
    re.compile(r"^172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}$"),
    re.compile(r"^192\.168\.\d{1,3}\.\d{1,3}$"),
    re.compile(r"^0\.0\.0\.0$"),
]

def validate_url_safety(url: str):
    """拒绝指向内网地址的 URL（SSRF 防护）"""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
    except Exception:
        raise HTTPException(status_code=400, detail="无效的 URL 格式")

    if not hostname:
        raise HTTPException(status_code=400, detail="URL 中未包含有效的主机名")

    # 检查 localhost 类主机名
    if hostname in ("localhost", "localhost.localdomain", "127.0.0.1", "0.0.0.0",
                    "::1", "[::1]"):
        raise HTTPException(status_code=400, detail="不允许访问本地回环地址")

    # 检查是否裸 IP 且为私有地址
    for pattern in PRIVATE_IP_PATTERNS:
        if pattern.match(hostname):
            raise HTTPException(status_code=400, detail=f"不允许访问内网地址: {hostname}")

    # 尝试 DNS 解析，如果解析到私有 IP 也拒绝
    try:
        ips = socket.getaddrinfo(hostname, None)
        for info in ips:
            ip = info[4][0]
            for pattern in PRIVATE_IP_PATTERNS:
                if pattern.match(ip):
                    raise HTTPException(
                        status_code=400,
                        detail=f"域名 {hostname} 解析到内网地址 {ip}，不允许访问"
                    )
    except HTTPException:
        raise
    except Exception:
        pass  # DNS 解析失败不阻塞，后續下载阶段会报错


# --- Pydantic Schemas ---
class CreateTaskRequest(BaseModel):
    url: str
    asr_mode: str = "local"

class BatchCreateRequest(BaseModel):
    urls: list[str]
    asr_mode: str = "local"

class RenameSpeakerRequest(BaseModel):
    speaker_id: str
    new_name: str

class QARequest(BaseModel):
    question: str
    history: list[dict] = []  # [{"role": "user"/"assistant", "content": "..."}]

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

def _check_and_clear_missing_audio(task):
    if not task: return task
    audio_url = task.get("audio_url")
    if audio_url:
        import os
        from app.config import SHORT_DOWNLOADS_DIR
        filename = os.path.basename(audio_url)
        local_path = os.path.join(SHORT_DOWNLOADS_DIR, filename)
        if not os.path.exists(local_path):
            task["audio_url"] = ""
    return task

# --- API Endpoints ---

@router.get("")
def list_tasks():
    tasks = db.get_all_tasks()
    # 动态注入排队位置
    for t in tasks:
        _check_and_clear_missing_audio(t)
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
    task = _check_and_clear_missing_audio(task)
    # 动态注入排队位置
    if task.get("status") == "pending":
        pos = queue_manager.get_queue_position(task.get("id"))
        task["queue_position"] = pos
        
    # 注入段落（所有状态都返回，支持增量转录显示）
    try:
        paragraphs = db.get_paragraphs_by_podcast(task_id) or []

        if task.get("status") == "completed":
            # 旧格式兼容 + 段落丢失兜底：从 transcript 重新生成段落
            need_regen = False
            if not paragraphs and task.get("transcript"):
                need_regen = True
            elif paragraphs and (
                "sentences" not in paragraphs[0] or
                not isinstance(paragraphs[0].get("sentences"), list)
            ):
                need_regen = True

            if need_regen and task.get("transcript"):
                try:
                    paragraphs = transcriber.cluster_segments_to_paragraphs(task_id, task.get("transcript"))
                    db.delete_paragraphs_by_podcast(task_id)
                    db.add_paragraphs(paragraphs)
                except Exception as regen_ex:
                    print(f"⚠️ [LOG ERROR] 段落重新生成失败: {regen_ex}")

            # 仅对已完成任务做 sedimented 检查
            for p in paragraphs:
                p["sedimented"] = False

        task["paragraphs"] = paragraphs
    except Exception as e:
        print(f"⚠️ [LOG ERROR] Failed to inject paragraphs: {e}")
        task["paragraphs"] = []
        
    return sanitize_floats(task)

@router.get("/{task_id}/transcript")
def get_task_transcript(task_id: str, format: str = "text"):
    """导出转录文本（支持 text/srt/vtt/json 格式，供外部工具/MCP 调用）"""
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="未找到该任务")
    if task.get("status") != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成，无法导出转录文本")

    transcript = task.get("transcript", [])
    speaker_mappings = task.get("speaker_mappings", {})
    paragraphs = db.get_paragraphs_by_podcast(task_id)

    if format == "json":
        return {"task_id": task_id, "title": task.get("title"), "paragraphs": paragraphs, "speaker_mappings": speaker_mappings}

    # 使用 paragraphs（有结构化时间）或 fallback 到 transcript
    items = paragraphs if paragraphs else transcript
    if not items:
        raise HTTPException(status_code=404, detail="无转录数据")

    def resolve_speaker(speaker_id):
        return speaker_mappings.get(speaker_id, speaker_id)

    if format == "srt":
        from fastapi.responses import PlainTextResponse
        from app.utils.formatters import format_srt
        return PlainTextResponse(format_srt(items, resolve_speaker), media_type="text/plain", headers={"Content-Disposition": f"attachment; filename=transcript.srt"})

    if format == "vtt":
        from fastapi.responses import PlainTextResponse
        from app.utils.formatters import format_vtt
        return PlainTextResponse(format_vtt(items, resolve_speaker), media_type="text/vtt", headers={"Content-Disposition": f"attachment; filename=transcript.vtt"})

    if format == "markdown":
        from fastapi.responses import PlainTextResponse
        from app.utils.formatters import format_markdown
        title = task.get("title", "未知标题")
        safe_name = "".join(c for c in title if c not in '<>:"/\\|?*')[:60]
        return PlainTextResponse(
            format_markdown(task),
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}.md"'}
        )

    # 默认 text 格式
    from fastapi.responses import PlainTextResponse
    from app.utils.formatters import format_text
    return PlainTextResponse(format_text(items, resolve_speaker), media_type="text/plain")

@router.post("/{task_id}/qa")
def ask_podcast(task_id: str, req: QARequest):
    """向播客提问，基于转录文本用 LLM 回答"""
    from app.core.llm_utils import call_llm, LLMError

    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="未找到该任务")
    if task.get("status") not in ("completed", "transcribed"):
        raise HTTPException(status_code=400, detail="任务尚未转录完成，无法进行问答")

    # Load existing Q&A history from database
    qa_history = task.get("qa_history") or []

    # Build transcript context
    transcript_segments = task.get("transcript", [])
    speaker_mappings = task.get("speaker_mappings", {})
    paragraphs = db.get_paragraphs_by_podcast(task_id)

    items = paragraphs if paragraphs else transcript_segments
    if not items:
        raise HTTPException(status_code=400, detail="无转录数据，无法进行问答")

    def resolve_speaker(speaker_id):
        return speaker_mappings.get(speaker_id, speaker_id)

    # Format transcript lines
    lines = []
    for p in items:
        start = p.get("start_time", 0)
        speaker = resolve_speaker(p.get("speaker", ""))
        text = p.get("content", "") or p.get("text", "")
        mm, ss = int(start // 60), int(start % 60)
        lines.append(f"[{mm:02d}:{ss:02d}] {speaker}: {text}")

    transcript_text = "\n".join(lines)

    # Build prompt
    title = task.get("title", "未知标题")
    podcast_name = task.get("podcast_name", "未知播客")

    # Build conversation context from Q&A history
    history_context = ""
    if qa_history:
        recent_history = qa_history[-10:]  # Last 5 Q&A pairs (10 messages)
        history_lines = []
        for msg in recent_history:
            role = "用户" if msg["role"] == "user" else "助手"
            history_lines.append(f"{role}: {msg['content']}")
        history_context = "\n\n以下是之前的对话历史，请参考上下文回答：\n" + "\n".join(history_lines)

    system_context = f"""你是一个播客内容分析助手。请根据以下播客转录文本回答用户的问题。
如果转录文本中没有相关信息，请明确说明。

播客: {title}（{podcast_name}）

转录文本:
{transcript_text}{history_context}"""

    # Call LLM — use smaller chunking threshold for local mode to prevent timeouts
    max_chars = 18000 if config.get("summary_mode", "local") == "local" else 80000

    try:
        if len(transcript_text) <= max_chars:
            # Short transcript: single call
            full_prompt = system_context + f"\n\n用户问题: {req.question}"
            answer = call_llm(full_prompt, label="播客问答")
        else:
            # Long transcript: chunk and merge
            summarizer_obj = PodcastSummarizer()
            chunks = summarizer_obj._split_transcript_into_chunks(lines, max_chars, overlap_lines=15)

            chunk_answers = []
            for i, chunk in enumerate(chunks):
                chunk_text = "\n".join(chunk)
                chunk_prompt = f"""你是一个播客内容分析助手。以下是播客转录文本的第{i+1}/{len(chunks)}部分。
请根据此部分回答用户的问题。如果此部分没有相关信息，请回答"此部分无相关信息"。

播客: {title}（{podcast_name}）

转录文本（第{i+1}部分）:
{chunk_text}

用户问题: {req.question}"""
                chunk_answer = call_llm(chunk_prompt, label=f"播客问答-分段{i+1}")
                if chunk_answer and "此部分无相关信息" not in chunk_answer and "无相关信息" not in chunk_answer:
                    chunk_answers.append(chunk_answer)

            if not chunk_answers:
                answer = "播客转录文本中未找到与您提问相关的内容。"
            elif len(chunk_answers) == 1:
                answer = chunk_answers[0]
            else:
                # Merge answers
                merge_prompt = f"""你是一个播客内容分析助手。以下是对同一个播客问题在不同段落中的回答，请综合这些回答给出一个完整、连贯的最终答案。

播客: {title}（{podcast_name}）
用户问题: {req.question}

各段落回答:
{chr(10).join(f"【段落{i+1}】{a}" for i, a in enumerate(chunk_answers))}"""
                answer = call_llm(merge_prompt, label="播客问答-合并")

    except LLMError as e:
        print(f"❌ [LOG ERROR] 播客问答 LLM 调用失败: {e}")
        status_code = 504 if "timed out" in str(e).lower() else 500
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        print(f"❌ [LOG ERROR] 播客问答未捕获异常: {e}")
        raise HTTPException(status_code=500, detail=f"问答服务处理失败: {str(e)}")

    # Save Q&A to history
    qa_history.append({"role": "user", "content": req.question})
    qa_history.append({"role": "assistant", "content": answer})
    db.update_task_field(task_id, qa_history=qa_history)

    return {"answer": answer, "history": qa_history}

@router.get("/{task_id}/qa")
def get_qa_history(task_id: str):
    """获取播客问答历史"""
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="未找到该任务")
    return {"history": task.get("qa_history") or []}

@router.delete("/{task_id}/qa")
def clear_qa_history(task_id: str):
    """清空播客问答历史"""
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="未找到该任务")
    db.update_task_field(task_id, qa_history=[])
    return {"success": True, "message": "问答历史已清空"}

@router.post("")
def create_task(req: CreateTaskRequest):
    raw_url = req.url.strip()
    import re
    # Split by spaces or commas to support multiple URLs pasted into the single URL box
    urls = [u.strip() for u in re.split(r'[\s,]+', raw_url) if u.strip()]
    urls = [u for u in urls if u.startswith("http")]
    
    if not urls:
        raise HTTPException(status_code=400, detail="未检测到有效的 URL 链接")

    if len(urls) > 1:
        # Treat as batch creation
        curr_summary_mode = config.get("summary_mode", "local")
        created_tasks = []
        for u in urls:
            validate_url_safety(u)
            existing_task = db.get_task_by_url(u)
            if existing_task and existing_task["status"] in ["pending", "downloading", "transcribing", "summarizing", "completed", "transcribed"]:
                created_tasks.append(existing_task["id"])
                continue
            task_id = str(uuid.uuid4())
            db.add_task(task_id, u, asr_mode=req.asr_mode, summary_mode=curr_summary_mode)
            queue_manager.add_task(task_id, u)
            created_tasks.append(task_id)
        
        res = {"task_id": created_tasks[0], "status": "pending", "is_duplicate": False, "batch_count": len(created_tasks)}
        warning = check_low_disk_space()
        if warning:
            res["warning"] = warning
        return res

    single_url = urls[0]
    validate_url_safety(single_url)
    
    # Duplicate prevention
    existing_task = db.get_task_by_url(single_url)
    if existing_task and existing_task["status"] in ["pending", "downloading", "transcribing", "summarizing", "completed", "transcribed"]:
        return {"task_id": existing_task["id"], "status": existing_task["status"], "is_duplicate": True}

    task_id = str(uuid.uuid4())
    curr_summary_mode = config.get("summary_mode", "local")
    db.add_task(task_id, single_url, asr_mode=req.asr_mode, summary_mode=curr_summary_mode)
    
    # Put into global queue
    queue_manager.add_task(task_id, single_url)
    
    res = {"task_id": task_id, "status": "pending", "is_duplicate": False}
    warning = check_low_disk_space()
    if warning:
        res["warning"] = warning
    return res

@router.post("/batch")
def create_batch_tasks(req: BatchCreateRequest):
    """批量创建转录任务（队列自动串行处理）"""
    if not req.urls:
        raise HTTPException(status_code=400, detail="URL 列表不能为空")
    if len(req.urls) > 20:
        raise HTTPException(status_code=400, detail="单次批量最多支持 20 个链接")

    curr_summary_mode = config.get("summary_mode", "local")
    created = []
    for url in req.urls:
        url = url.strip()
        if not url:
            continue
        validate_url_safety(url)
        
        # Duplicate prevention
        existing_task = db.get_task_by_url(url)
        if existing_task and existing_task["status"] in ["pending", "downloading", "transcribing", "summarizing", "completed", "transcribed"]:
            created.append({"task_id": existing_task["id"], "url": url, "status": existing_task["status"], "is_duplicate": True})
            continue

        task_id = str(uuid.uuid4())
        db.add_task(task_id, url, asr_mode=req.asr_mode, summary_mode=curr_summary_mode)
        queue_manager.add_task(task_id, url)
        created.append({"task_id": task_id, "url": url, "status": "pending", "is_duplicate": False})

    res = {"created": len([c for c in created if not c.get("is_duplicate")]), "tasks": created}
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
        db.update_task_field(task_id, status="cancelled", progress=100.0, error_message="任务在删除前已被取消。")
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
        db.update_task_field(task_id, status="cancelled", progress=100.0, error_message="任务已被手动取消。")
        print(f"🚫 [LOG] 任务 {task_id} 已被手动取消。")
        return {"success": True, "message": "任务已被手动取消。"}
    
    return {"success": False, "message": f"当前任务状态为 {task.get('status')}，不可取消。"}


@router.post("/{task_id}/retry")
def retry_task(task_id: str):
    """重新执行失败或已取消的任务"""
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    status = task.get("status")
    if status not in ("failed", "cancelled"):
        raise HTTPException(status_code=400, detail=f"当前任务状态为 {status}，仅支持重试失败或已取消的任务")

    # 获取最新全局配置
    latest_config = load_config()
    current_asr_mode = latest_config.get("asr_mode", "online")
    current_summary_mode = latest_config.get("summary_mode", "online")

    # 重置任务状态为 pending，清除错误信息和进度，并强制更新 asr_mode 和 summary_mode 为当前配置
    db.update_task_field(task_id, status="pending", progress=0.0, error_message="", asr_mode=current_asr_mode, summary_mode=current_summary_mode)
    # 重新加入队列
    queue_manager.add_task(task_id, task.get("url", ""))
    print(f"🔄 [LOG] 任务 {task_id} 已重新加入队列 (asr_mode: {current_asr_mode}, summary_mode: {current_summary_mode})。")
    return {"success": True, "message": "任务已重新加入队列", "task_id": task_id}


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
    db.update_task_field(task_id, restoring=True, restore_progress=0.0)
        
    # 启动后台任务进行下载修复
    def do_redownload():
        try:
            print(f"📥 [LOG] 启动后台音频修复重新下载, 原始链接: {task['url']}")
            
            def restore_progress_callback(percent):
                db.update_task_field(task_id, restore_progress=round(percent, 1))
                
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
            db.update_task_field(task_id, audio_url=new_audio_url, restoring=False, restore_progress=100.0)
        except Exception as e:
            print(f"❌ [LOG] 音频文件修复重新下载失败: {e}")
            db.update_task_field(task_id, restoring=False, restore_progress=0.0)
            
    background_tasks.add_task(do_redownload)
    return {"success": True, "message": "已在后台启动音频文件下载修复"}

@router.post("/{task_id}/speaker/rename")
def rename_speaker(task_id: str, req: RenameSpeakerRequest):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="未找到任务")
        
    mappings = task.get("speaker_mappings", {})
    mappings[req.speaker_id] = req.new_name
    db.update_task_field(task_id, speaker_mappings=mappings)
    
    # 将手动命名的发言人声纹特征写入本地声纹库
    speaker_embs = task.get("speaker_embeddings", {})
    emb = speaker_embs.get(req.speaker_id)
    if emb:
        save_speaker_fingerprint(req.new_name, emb)
        
    return {"success": True, "speaker_mappings": mappings}


class StartSummaryRequest(BaseModel):
    prompt_text: str = None

@router.post("/{task_id}/summary/start")
def start_summary(task_id: str, req: StartSummaryRequest, background_tasks: BackgroundTasks):
    """
    手动发起大模型深度总结，支持转录完成初次启动或后续重新生成
    """
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="未找到任务")
    
    if task["status"] not in ["completed", "failed", "transcribed"]:
        raise HTTPException(status_code=400, detail="任务处于非就绪状态，无法启动总结")

    custom_prompt = req.prompt_text if req else None

    def run_re_summarize():
        try:
            db.update_task_field(task_id, status="summarizing", progress=80.0)
            summary_report = summarizer.summarize(
                task["metadata"], 
                task["transcript"], 
                speaker_mappings=task.get("speaker_mappings"),
                summary_mode=task.get("summary_mode", "local"),
                custom_prompt=custom_prompt
            )
            db.update_task_field(task_id, status="completed", summary=summary_report, progress=100.0)
        except Exception as ex:
            db.update_task_field(task_id, status="failed", error_message=str(ex), progress=100.0)

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
        updated_t = db.update_task_field(
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
    db.update_task_field(
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
