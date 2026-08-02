"""MCP Server for whisperMe — exposes podcast tools to AI Agents."""
import json
from mcp.server.fastmcp import FastMCP
from app.database import db
from app.config import config
from app.core.llm_utils import call_llm

mcp = FastMCP(
    "whisperMe",
    instructions="AI播客转录与知识提炼工具。支持播客下载、转录、说话人识别、AI总结和问答。"
)


# ─── Tools ───────────────────────────────────────────────────────────────

@mcp.tool()
def list_tasks(status: str = None, limit: int = 50) -> str:
    """列出播客任务列表。

    Args:
        status: 按状态过滤（pending/downloading/transcribing/summarizing/completed/failed）
        limit: 返回数量上限，默认50
    """
    tasks = db.get_all_tasks()
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    tasks = tasks[:limit]

    result = []
    for t in tasks:
        result.append({
            "id": t.get("id"),
            "title": t.get("title"),
            "podcast_name": t.get("podcast_name"),
            "status": t.get("status"),
            "created_at": t.get("created_at"),
        })
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def get_task(task_id: str) -> str:
    """获取播客任务详情，包含段落、摘要和说话人信息。

    Args:
        task_id: 任务ID
    """
    task = db.get_task(task_id)
    if not task:
        return json.dumps({"error": "未找到该任务"}, ensure_ascii=False)

    paragraphs = db.get_paragraphs_by_podcast(task_id)
    task["paragraphs"] = paragraphs or []

    # Remove large binary fields for MCP consumption
    task.pop("speaker_embeddings", None)

    return json.dumps(task, ensure_ascii=False, indent=2, default=str)


@mcp.tool()
def search_tasks(query: str, limit: int = 20) -> str:
    """按关键词搜索播客任务（搜索标题、播客名、摘要内容）。

    Args:
        query: 搜索关键词
        limit: 返回数量上限
    """
    tasks = db.get_all_tasks()
    query_lower = query.lower()

    matched = []
    for t in tasks:
        title = (t.get("title") or "").lower()
        podcast_name = (t.get("podcast_name") or "").lower()
        summary = (t.get("summary") or "").lower()

        if query_lower in title or query_lower in podcast_name or query_lower in summary:
            matched.append({
                "id": t.get("id"),
                "title": t.get("title"),
                "podcast_name": t.get("podcast_name"),
                "status": t.get("status"),
                "created_at": t.get("created_at"),
            })
        if len(matched) >= limit:
            break

    return json.dumps(matched, ensure_ascii=False, indent=2)


@mcp.tool()
def create_task(url: str, asr_mode: str = "local") -> str:
    """提交新的播客URL开始处理。

    Args:
        url: 播客链接（支持小宇宙、Bilibili等平台）
        asr_mode: ASR模式，"local"（本地GPU）或 "online"（在线API）
    """
    import uuid
    from app.core.queue_manager import queue_manager

    task_id = str(uuid.uuid4())
    curr_summary_mode = config.get("summary_mode", "local")
    db.add_task(task_id, url, asr_mode=asr_mode, summary_mode=curr_summary_mode)
    queue_manager.add_task(task_id, url)

    return json.dumps({"task_id": task_id, "status": "pending"}, ensure_ascii=False)


@mcp.tool()
def export_transcript(task_id: str, format: str = "markdown") -> str:
    """导出播客转录或摘要。

    Args:
        task_id: 任务ID
        format: 导出格式 — "markdown"(AI摘要文档), "text"(纯文本), "srt"(字幕), "vtt"(WebVTT), "json"(结构化数据)
    """
    task = db.get_task(task_id)
    if not task:
        return json.dumps({"error": "未找到该任务"}, ensure_ascii=False)
    if task.get("status") != "completed":
        return json.dumps({"error": "任务尚未完成"}, ensure_ascii=False)

    speaker_mappings = task.get("speaker_mappings", {})
    paragraphs = db.get_paragraphs_by_podcast(task_id)
    transcript = task.get("transcript", [])
    items = paragraphs if paragraphs else transcript

    def resolve_speaker(speaker_id):
        return speaker_mappings.get(speaker_id, speaker_id)

    if format == "markdown":
        import yaml
        metadata = task.get("metadata", {}) or {}
        frontmatter = {
            "title": task.get("title", ""),
            "podcast": task.get("podcast_name", ""),
            "date": metadata.get("pub_date", ""),
            "duration": metadata.get("duration", ""),
            "url": task.get("url", ""),
        }
        fm_str = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False, sort_keys=False)
        doc = f"---\n{fm_str}---\n\n"
        doc += f"# {task.get('title', '')}\n\n"
        summary = task.get("summary", "")
        if summary:
            doc += f"## AI Summary\n\n{summary}\n"
        return doc

    if format == "json":
        return json.dumps({
            "task_id": task_id,
            "title": task.get("title"),
            "paragraphs": paragraphs,
            "speaker_mappings": speaker_mappings,
        }, ensure_ascii=False, indent=2)

    if format == "srt":
        lines = []
        for i, p in enumerate(items):
            start = p.get("start_time", 0)
            end = p.get("end_time", 0)
            speaker = resolve_speaker(p.get("speaker", ""))
            text = p.get("content", "") or p.get("text", "")
            sh, sm, ss = int(start//3600), int((start%3600)//60), start%60
            eh, em, es = int(end//3600), int((end%3600)//60), end%60
            lines.append(f"{i+1}\n{sh:02d}:{sm:02d}:{ss:06.3f}".replace(".",",") + f" --> {eh:02d}:{em:02d}:{es:06.3f}".replace(".",",") + f"\n{speaker}: {text}")
        return "\n\n".join(lines)

    if format == "vtt":
        lines = ["WEBVTT", ""]
        for i, p in enumerate(items):
            start = p.get("start_time", 0)
            end = p.get("end_time", 0)
            speaker = resolve_speaker(p.get("speaker", ""))
            text = p.get("content", "") or p.get("text", "")
            sh, sm, ss = int(start//3600), int((start%3600)//60), start%60
            eh, em, es = int(end//3600), int((end%3600)//60), end%60
            lines.append(f"{i+1}\n{sh:02d}:{sm:02d}:{ss:06.3f} --> {eh:02d}:{em:02d}:{es:06.3f}\n{speaker}: {text}")
        return "\n\n".join(lines)

    # Default: text
    lines = []
    for p in items:
        start = p.get("start_time", 0)
        speaker = resolve_speaker(p.get("speaker", ""))
        text = p.get("content", "") or p.get("text", "")
        mm, ss = int(start//60), int(start%60)
        lines.append(f"[{mm:02d}:{ss:02d}] {speaker}: {text}")
    return "\n".join(lines)


@mcp.tool()
def ask_podcast(task_id: str, question: str) -> str:
    """向播客提问，基于转录文本回答。

    Args:
        task_id: 任务ID
        question: 要问的问题
    """
    task = db.get_task(task_id)
    if not task:
        return json.dumps({"error": "未找到该任务"}, ensure_ascii=False)
    if task.get("status") not in ("completed", "transcribed"):
        return json.dumps({"error": "任务尚未转录完成"}, ensure_ascii=False)

    transcript_segments = task.get("transcript", [])
    speaker_mappings = task.get("speaker_mappings", {})
    paragraphs = db.get_paragraphs_by_podcast(task_id)
    items = paragraphs if paragraphs else transcript_segments

    if not items:
        return json.dumps({"error": "无转录数据"}, ensure_ascii=False)

    def resolve_speaker(speaker_id):
        return speaker_mappings.get(speaker_id, speaker_id)

    lines = []
    for p in items:
        start = p.get("start_time", 0)
        speaker = resolve_speaker(p.get("speaker", ""))
        text = p.get("content", "") or p.get("text", "")
        mm, ss = int(start // 60), int(start % 60)
        lines.append(f"[{mm:02d}:{ss:02d}] {speaker}: {text}")

    transcript_text = "\n".join(lines)
    title = task.get("title", "未知标题")
    podcast_name = task.get("podcast_name", "未知播客")

    max_chars = 18000 if config.get("summary_mode", "local") == "local" else 80000

    if len(transcript_text) <= max_chars:
        prompt = f"""你是一个播客内容分析助手。请根据以下播客转录文本回答用户的问题。
如果转录文本中没有相关信息，请明确说明。

播客: {title}（{podcast_name}）

转录文本:
{transcript_text}

用户问题: {question}"""
        return call_llm(prompt, label="MCP播客问答")
    else:
        from app.core.summarizer import PodcastSummarizer
        summarizer = PodcastSummarizer()
        chunks = summarizer._split_transcript_into_chunks(lines, max_chars, overlap_lines=15)

        chunk_answers = []
        for i, chunk in enumerate(chunks):
            chunk_text = "\n".join(chunk)
            chunk_prompt = f"""你是播客内容分析助手。以下是转录文本第{i+1}/{len(chunks)}部分。
根据此部分回答问题。无相关信息则回答"此部分无相关信息"。

播客: {title}（{podcast_name}）
转录文本（第{i+1}部分）:
{chunk_text}

问题: {question}"""
            chunk_answers.append(call_llm(chunk_prompt, label=f"MCP问答-分段{i+1}"))

        merge_prompt = f"""综合以下各段落回答，给出完整连贯的最终答案。
如所有段落都无相关信息，请说明转录中没有相关内容。

播客: {title}（{podcast_name}）
问题: {question}

各段落回答:
{chr(10).join(f"【段落{i+1}】{a}" for i, a in enumerate(chunk_answers))}"""
        return call_llm(merge_prompt, label="MCP问答-合并")


@mcp.tool()
def get_system_status() -> str:
    """获取系统状态（CPU、内存、GPU、队列等性能指标）。"""
    import psutil

    status = {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "memory": {
            "total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "used_gb": round(psutil.virtual_memory().used / (1024**3), 1),
            "percent": psutil.virtual_memory().percent,
        },
    }

    try:
        import torch
        if torch.cuda.is_available():
            status["gpu"] = {
                "name": torch.cuda.get_device_name(0),
                "memory_total_gb": round(torch.cuda.get_device_properties(0).total_mem / (1024**3), 1),
                "memory_used_gb": round(torch.cuda.memory_allocated(0) / (1024**3), 1),
            }
    except Exception:
        status["gpu"] = "不可用"

    tasks = db.get_all_tasks()
    status["queue"] = {
        "pending": len([t for t in tasks if t.get("status") == "pending"]),
        "processing": len([t for t in tasks if t.get("status") in ("downloading", "transcribing", "summarizing")]),
        "completed": len([t for t in tasks if t.get("status") == "completed"]),
        "total": len(tasks),
    }

    return json.dumps(status, ensure_ascii=False, indent=2)


@mcp.tool()
def get_config() -> str:
    """获取当前系统配置（API密钥已脱敏）。"""
    safe_config = {}
    for k, v in config.items():
        if any(sensitive in k.lower() for sensitive in ("key", "token", "secret", "password")):
            safe_config[k] = "***" if v else ""
        else:
            safe_config[k] = v
    return json.dumps(safe_config, ensure_ascii=False, indent=2)


# ─── Resources ───────────────────────────────────────────────────────────

@mcp.resource("whisperme://tasks")
def resource_tasks() -> str:
    """所有播客任务列表"""
    tasks = db.get_all_tasks()
    result = [{"id": t["id"], "title": t.get("title"), "status": t.get("status")} for t in tasks]
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.resource("whisperme://tasks/{task_id}")
def resource_task(task_id: str) -> str:
    """单个播客任务详情"""
    task = db.get_task(task_id)
    if not task:
        return json.dumps({"error": "未找到"})
    task.pop("speaker_embeddings", None)
    return json.dumps(task, ensure_ascii=False, indent=2, default=str)


@mcp.resource("whisperme://config")
def resource_config() -> str:
    """系统配置"""
    return get_config()


# ─── Prompts ─────────────────────────────────────────────────────────────

@mcp.prompt()
def summarize_podcast(task_id: str) -> str:
    """生成一个用于总结指定播客的提示词"""
    task = db.get_task(task_id)
    if not task:
        return f"任务 {task_id} 不存在"
    title = task.get("title", "未知标题")
    podcast_name = task.get("podcast_name", "未知播客")
    return f"请总结播客「{podcast_name}」的「{title}」这一期的核心内容、关键观点和值得记住的金句。"


@mcp.prompt()
def ask_about_podcast(task_id: str, question: str) -> str:
    """生成一个用于向播客提问的提示词"""
    task = db.get_task(task_id)
    if not task:
        return f"任务 {task_id} 不存在"
    title = task.get("title", "未知标题")
    podcast_name = task.get("podcast_name", "未知播客")
    return f"关于播客「{podcast_name}」的「{title}」这一期，请回答以下问题：{question}"
