import yaml

def format_srt(items, resolve_speaker):
    lines = []
    for i, p in enumerate(items):
        start = p.get("start_time", 0)
        end = p.get("end_time", 0)
        speaker = resolve_speaker(p.get("speaker", ""))
        text = p.get("content", "") or p.get("text", "")
        sh, sm, ss = int(start // 3600), int((start % 3600) // 60), start % 60
        eh, em, es = int(end // 3600), int((end % 3600) // 60), end % 60
        lines.append(
            f"{i + 1}\n{sh:02d}:{sm:02d}:{ss:06.3f}".replace(".", ",")
            + f" --> {eh:02d}:{em:02d}:{es:06.3f}".replace(".", ",")
            + f"\n{speaker}: {text}"
        )
    return "\n\n".join(lines)

def format_vtt(items, resolve_speaker):
    lines = ["WEBVTT", ""]
    for i, p in enumerate(items):
        start = p.get("start_time", 0)
        end = p.get("end_time", 0)
        speaker = resolve_speaker(p.get("speaker", ""))
        text = p.get("content", "") or p.get("text", "")
        sh, sm, ss = int(start // 3600), int((start % 3600) // 60), start % 60
        eh, em, es = int(end // 3600), int((end % 3600) // 60), end % 60
        lines.append(f"{i + 1}\n{sh:02d}:{sm:02d}:{ss:06.3f} --> {eh:02d}:{em:02d}:{es:06.3f}\n{speaker}: {text}")
    return "\n\n".join(lines)

def format_markdown(task):
    title = task.get("title", "未知标题")
    podcast = task.get("podcast_name", "未知播客")
    meta = task.get("metadata", {}) or {}
    pub_date = meta.get("pub_date", "")
    duration = meta.get("duration", "")
    url = task.get("url", "")
    summary = task.get("summary", "")

    frontmatter = {
        "title": title,
        "podcast": podcast,
        "date": pub_date,
        "duration": duration,
        "url": url,
    }
    fm_str = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False, sort_keys=False)

    doc = f"---\n{fm_str}---\n\n"
    doc += f"# {title}\n\n"
    doc += f"> {podcast}"
    if pub_date:
        doc += f" · {pub_date}"
    if duration:
        doc += f" · {duration}"
    doc += "\n\n"

    if summary:
        doc += f"## AI Summary\n\n{summary}\n"
    else:
        doc += "*暂无 AI 总结*\n"
    return doc

def format_text(items, resolve_speaker):
    lines = []
    for p in items:
        start = p.get("start_time", 0)
        speaker = resolve_speaker(p.get("speaker", ""))
        text = p.get("content", "") or p.get("text", "")
        mm, ss = int(start // 60), int(start % 60)
        lines.append(f"[{mm:02d}:{ss:02d}] {speaker}: {text}")
    return "\n".join(lines)
