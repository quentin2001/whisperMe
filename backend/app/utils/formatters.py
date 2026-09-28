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

def format_markdown(task, items=None, resolve_speaker=None):
    title = task.get("title", "未知标题")
    podcast = task.get("podcast_name", "")
    meta = task.get("metadata", {}) or {}
    pub_date = meta.get("pub_date", "")
    duration = meta.get("duration", "")
    url = task.get("url", "")
    summary = task.get("summary", "")

    frontmatter = {
        "title": title,
    }
    if podcast:
        frontmatter["podcast"] = podcast
    if pub_date:
        frontmatter["date"] = pub_date
    if duration:
        frontmatter["duration"] = duration
    if url:
        frontmatter["url"] = url

    fm_str = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False, sort_keys=False)

    doc = f"---\n{fm_str}---\n\n"
    doc += f"# {title}\n\n"
    if podcast:
        meta_parts = [f"**播客**：{podcast}"]
        if pub_date:
            meta_parts.append(f"**日期**：{pub_date}")
        if duration:
            meta_parts.append(f"**时长**：{duration}")
        if items:
            meta_parts.append(f"**段落数**：{len(items)}")
        doc += f"> {' · '.join(meta_parts)}\n\n"

    if items:
        doc += "---\n\n## 完整逐字稿\n\n"
        def _fmt_time(secs):
            if secs is None or secs < 0:
                return "00:00"
            hrs = int(secs // 3600)
            mins = int((secs % 3600) // 60)
            seconds = int(secs % 60)
            if hrs > 0:
                return f"{hrs:02d}:{mins:02d}:{seconds:02d}"
            return f"{mins:02d}:{seconds:02d}"

        lines = []
        for p in items:
            start_t = _fmt_time(p.get("start_time", 0))
            end_t = _fmt_time(p.get("end_time", 0))
            raw_speaker = p.get("speaker", "")
            speaker = resolve_speaker(raw_speaker) if resolve_speaker else raw_speaker
            if not speaker or speaker == "UNKNOWN_SPEAKER":
                speaker = "发言人"
            text = (p.get("content", "") or p.get("text", "")).strip()
            lines.append(f"**[{start_t} - {end_t}] {speaker}**\n\n{text}")
        doc += "\n\n".join(lines) + "\n"
    elif summary:
        doc += f"## AI Summary\n\n{summary}\n"
    else:
        doc += "*暂无转录内容*\n"
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
