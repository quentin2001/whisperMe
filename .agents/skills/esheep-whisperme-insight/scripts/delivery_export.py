#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
delivery_export.py - 一键交付流格式打包导出工具

用于商业代工交付场景：把播客逐字稿与 AI 深度总结报告按规范排版，
一次性导出到独立的交付文件夹中（默认 ``deliveries/【播客名】单集标题/``）。

数据来源二选一：
  * ``--task-id``   —— 读取 whisperMe 本地数据库中的任务与段落
  * ``--task-json`` —— 读取外部 JSON（独立 ASR 转录产物）

导出格式由 ``--formats`` 控制，默认 ``all``（docx + md + srt）。

用法示例::

    python delivery_export.py --task-id <TASK_ID> --summary-file <SUMMARY.md> --formats all
    python delivery_export.py --task-json <TASK.json> --formats docx,md
"""

import os
import sys
import json
import argparse
import re
from pathlib import Path

# 把仓库的 backend/ 注入 sys.path，以便直接复用后端的排版引擎（docx_formatter / formatters）。
# 脚本位于 <repo>/.agents/skills/<skill>/scripts/，向上 3 层即仓库根目录。
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[3]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# 语气词清洗正则表达式（用于商业交付时提高文本可读性）
FILLER_INLINE = re.compile(
    r'(?:^|(?<=[。，、！？.,!?\s]))'
    r'(?:嗯+|啊+|呃+|额+|哦+|就是说|那个|然后嘛|对吧|你知道吗|怎么说呢)'
    r'(?=[。，、！？.,!?\s]|$)'
)
FILLER_LINE = re.compile(
    r'^[\s]*(嗯+|啊+|呃+|额+|哦+|唉+|哎+|诶+|对对对|是是是|好好好|'
    r'对的对的|没错没错|就是就是|然后然后)[\s。，、！？.,!?]*$'
)

def denoise_text(text: str) -> str:
    """清理多余中文口头禅与语气词"""
    if not text:
        return ""
    if FILLER_LINE.match(text):
        return ""
    return FILLER_INLINE.sub("", text).strip()

def sanitize_filename(name: str, max_len: int = 60) -> str:
    """清理 Windows/Linux 非法文件名字符"""
    clean = re.sub(r'[<>:"/\\|?*\n\r\t]', '_', name).strip()
    return clean[:max_len] or "podcast"

def main():
    """CLI 入口：加载任务 → 可选去噪 → 渲染并写出交付文件。

    执行流程：
      1. 从数据库或外部 JSON 载入任务、段落与说话人映射；
      2. 取得 AI 总结文本（文件 / 命令行 / 任务记录，优先级从高到低）；
      3. 默认执行口语语气词清洗（``--no-denoise`` 可关闭）；
      4. 计算交付目录并导出所选格式；
      5. 以 JSON 形式打印交付清单，供 Agent 读取归档路径。

    退出码：0 成功；1 参数或数据源校验失败。
    """
    parser = argparse.ArgumentParser(description="whisperMe 交付件自动化导出工具")
    parser.add_argument("--task-id", help="whisperMe 数据库中的任务 ID")
    parser.add_argument("--task-json", help="外部任务元数据与段落 JSON 文件路径")
    parser.add_argument("--summary-file", help="AI 深度总结 Markdown 文件路径")
    parser.add_argument("--summary-text", help="直接传入的 AI 深度总结 Markdown 文本")
    parser.add_argument("--output-dir", help="交付目标文件夹路径（若未指定则自动归档到 deliveries/【播客名】集名/）")
    parser.add_argument("--formats", default="all", help="导出格式组合：all（默认全量）或用逗号分隔，如 docx 或 docx,md 或 docx,md,srt")
    parser.add_argument("--denoise", action="store_true", default=True, help="是否对逐字稿文本进行语气词清洗（默认开启）")
    parser.add_argument("--no-denoise", action="store_false", dest="denoise", help="禁用语气词清洗")
    
    args = parser.parse_args()

    task = {}
    paragraphs = []
    speaker_mappings = {}

    # 1. 加载任务数据
    if args.task_id:
        try:
            from app.database import db
            task = db.get_task(args.task_id)
            if not task:
                sys.stderr.write(f"[ERROR] 未找到任务 ID: {args.task_id}\n")
                sys.exit(1)
            paragraphs = db.get_paragraphs_by_podcast(args.task_id)
            speaker_mappings = task.get("speaker_mappings") or {}
        except Exception as e:
            sys.stderr.write(f"[ERROR] 从数据库读取任务失败: {e}\n")
            sys.exit(1)
    elif args.task_json:
        try:
            with open(args.task_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            task = data.get("task") or data
            paragraphs = data.get("paragraphs") or task.get("transcript") or []
            speaker_mappings = task.get("speaker_mappings") or {}
        except Exception as e:
            sys.stderr.write(f"[ERROR] 读取任务 JSON 失败: {e}\n")
            sys.exit(1)
    elif args.summary_file and os.path.exists(args.summary_file):
        # 允许仅传入 --summary-file 针对已有交付件重新生成或增补格式
        stem = Path(args.summary_file).stem
        clean_stem = re.sub(r'_(?:AI深度总结报告|总结|summary)$', '', stem)
        m = re.match(r'^(?:【(.*?)】)?(.*)$', clean_stem)
        podcast = m.group(1) if m and m.group(1) else "精选播客"
        title = m.group(2) if m and m.group(2) else clean_stem
        task = {"title": title, "podcast_name": podcast}
    else:
        sys.stderr.write("[ERROR] 必须提供 --task-id 或 --task-json（或有效 --summary-file）\n")
        sys.exit(1)

    # 2. 获取总结内容
    summary = ""
    if args.summary_file and os.path.exists(args.summary_file):
        with open(args.summary_file, "r", encoding="utf-8") as f:
            summary = f.read()
    elif args.summary_text:
        summary = args.summary_text
    elif task.get("summary"):
        summary = task.get("summary")

    # 3. 文本去噪清洗
    if args.denoise and paragraphs:
        cleaned_paragraphs = []
        for p in paragraphs:
            raw_text = p.get("content") or p.get("text") or ""
            cleaned = denoise_text(raw_text)
            if cleaned:
                p_copy = dict(p)
                p_copy["content"] = cleaned
                p_copy["text"] = cleaned
                cleaned_paragraphs.append(p_copy)
        paragraphs = cleaned_paragraphs

    # 4. 计算交付目录路径
    title = task.get("title", "未知标题")
    podcast = task.get("podcast_name", "精选播客")
    clean_title = sanitize_filename(title, 80)
    clean_podcast = sanitize_filename(podcast, 40)

    if args.output_dir:
        target_dir = Path(args.output_dir)
    else:
        folder_name = f"【{clean_podcast}】{clean_title}" if clean_podcast else clean_title
        target_dir = PROJECT_ROOT / "deliveries" / folder_name

    target_dir.mkdir(parents=True, exist_ok=True)

    # 5. 解析需要导出的格式
    req_formats = set()
    raw_formats = args.formats.lower().strip()
    if raw_formats == "all":
        req_formats = {"pdf", "docx", "md", "srt"}
    else:
        for f in raw_formats.split(","):
            f = f.strip()
            if f in ("docx", "word"):
                req_formats.add("docx")
            elif f in ("md", "markdown"):
                req_formats.add("md")
            elif f in ("srt", "vtt"):
                req_formats.add(f)
            elif f == "pdf":
                req_formats.add("pdf")

    # 说话人解析函数
    def resolve_speaker(spk):
        return speaker_mappings.get(spk, spk) if speaker_mappings else spk

    exported_files = []

    # 导入生成引擎
    from app.utils.docx_formatter import generate_transcript_docx, generate_summary_docx
    from app.utils.pdf_formatter import generate_transcript_pdf, generate_summary_pdf
    from app.utils.formatters import format_markdown, format_srt, format_vtt

    # ==================== 逐字稿导出 ====================
    if paragraphs:
        # PDF 逐字稿
        if "pdf" in req_formats:
            pdf_path = target_dir / f"{clean_title}_逐字稿.pdf"
            generate_transcript_pdf(task, paragraphs, resolve_speaker, output_path=pdf_path)
            exported_files.append({"type": "transcript_pdf", "path": str(pdf_path), "size": pdf_path.stat().st_size})

        # DOCX 逐字稿
        if "docx" in req_formats:
            docx_path = target_dir / f"{clean_title}_逐字稿.docx"
            buf = generate_transcript_docx(task, paragraphs, resolve_speaker)
            with open(docx_path, "wb") as f:
                f.write(buf.getvalue())
            exported_files.append({"type": "transcript_docx", "path": str(docx_path), "size": docx_path.stat().st_size})

        # Markdown 逐字稿
        if "md" in req_formats:
            md_path = target_dir / f"{clean_title}_逐字稿.md"
            md_content = format_markdown(task, paragraphs, resolve_speaker)
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            exported_files.append({"type": "transcript_md", "path": str(md_path), "size": md_path.stat().st_size})

        # SRT 字幕
        if "srt" in req_formats:
            srt_path = target_dir / f"{clean_title}_逐字稿.srt"
            srt_content = format_srt(paragraphs, resolve_speaker)
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt_content)
            exported_files.append({"type": "transcript_srt", "path": str(srt_path), "size": srt_path.stat().st_size})

    # ==================== AI 深度总结报告导出 ====================
    if summary:
        task_with_summary = dict(task)
        task_with_summary["summary"] = summary

        # PDF 深度总结
        if "pdf" in req_formats:
            summary_pdf_path = target_dir / f"{clean_title}_AI深度总结报告.pdf"
            generate_summary_pdf(task_with_summary, output_path=summary_pdf_path)
            exported_files.append({"type": "summary_pdf", "path": str(summary_pdf_path), "size": summary_pdf_path.stat().st_size})

        # DOCX 深度总结
        if "docx" in req_formats:
            summary_docx_path = target_dir / f"{clean_title}_AI深度总结报告.docx"
            buf = generate_summary_docx(task_with_summary)
            with open(summary_docx_path, "wb") as f:
                f.write(buf.getvalue())
            exported_files.append({"type": "summary_docx", "path": str(summary_docx_path), "size": summary_docx_path.stat().st_size})

        # Markdown 深度总结
        if "md" in req_formats:
            summary_md_path = target_dir / f"{clean_title}_AI深度总结报告.md"
            with open(summary_md_path, "w", encoding="utf-8") as f:
                f.write(summary)
            exported_files.append({"type": "summary_md", "path": str(summary_md_path), "size": summary_md_path.stat().st_size})

    # 输出结果报告 JSON 给 Agent
    result = {
        "success": True,
        "title": title,
        "podcast": podcast,
        "delivery_directory": str(target_dir),
        "total_paragraphs": len(paragraphs),
        "exported_files": exported_files
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
