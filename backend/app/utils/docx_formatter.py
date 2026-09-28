"""Word (.docx) export engine for transcripts and AI summary reports.

This module renders whisperMe content into presentation-grade Word documents
entirely in memory (``io.BytesIO``), so callers can stream the result straight
back over HTTP without touching the filesystem.

Two entry points are exposed:

* :func:`generate_transcript_docx` — timestamped, speaker-labelled transcript.
* :func:`generate_summary_docx`    — Markdown AI summary rendered with real
  Word constructs (headings, tables, blockquotes, code blocks).

Design notes
------------
* Output is intentionally **brand-neutral**: no product name, watermark or
  footer is ever written into the document, because these files are delivered
  to end readers (and often to paying clients) as clean standalone documents.
* Chinese and Latin text are rendered through explicit East-Asian font
  bindings, otherwise Word silently falls back to a default font for CJK.
* Markdown features that Word cannot natively render (Mermaid / flowchart /
  mindmap code fences) are downgraded to structured bullet points instead of
  being emitted verbatim as raw code.
"""

import io
import re
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

# ----------------------------------------------------
# Helper styling utilities
# ----------------------------------------------------

def _apply_font(run, font_name="Microsoft YaHei", size_pt=10.5, color_rgb=None, bold=False, italic=False):
    """Apply family/size/weight/colour to a run, binding the CJK font as well.

    python-docx only sets the Latin font by default. Word then picks an
    arbitrary fallback for Chinese glyphs, which breaks the intended typography,
    so the ``w:rFonts`` element is patched explicitly for ascii/hAnsi/eastAsia.
    """
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.italic = italic
    if color_rgb:
        run.font.color.rgb = color_rgb
    # Ensure East Asia font applies correctly in Word
    rPr = run._r.get_or_add_rPr()
    rFonts = parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="{font_name}" w:hAnsi="{font_name}" w:eastAsia="{font_name}"/>')
    rPr.append(rFonts)

def _set_cell_background(cell, hex_color):
    """Fill a table cell with a solid background colour (``hex_color``, no ``#``)."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tc_pr.append(shd)

def _set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
    """Set cell padding in twips (1/20 pt) so tables stop looking cramped."""
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tc_pr.append(tc_mar)

def _set_table_borders(table, color="D0D7DE"):
    """Draw horizontal rules only (top / bottom / insideH), giving the airy
    'booktabs' look used across the generated reports."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="none"/>'
        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="none"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def _format_seconds(secs):
    """Format seconds as ``MM:SS``, or ``HH:MM:SS`` once the value passes one hour."""
    if secs is None or secs < 0:
        return "00:00"
    hrs = int(secs // 3600)
    mins = int((secs % 3600) // 60)
    seconds = int(secs % 60)
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{seconds:02d}"
    return f"{mins:02d}:{seconds:02d}"

def _add_formatted_runs(paragraph, text, is_header=False, default_color=None):
    """Parse inline Markdown (``**bold**``, ``*italic*``, ``` `code` ```) into runs.

    Only inline markers are handled here — block-level structures (headings,
    lists, tables, fences) are the caller's responsibility. Unmatched markers
    fall through as plain text, so malformed Markdown degrades safely.
    """
    pattern = re.compile(r'(\*\*.*?\*\*|\*.*?\*|`.*?`)')
    tokens = pattern.split(text)
    for tok in tokens:
        if not tok:
            continue
        if tok.startswith('**') and tok.endswith('**'):
            inner = tok[2:-2]
            r = paragraph.add_run(inner)
            _apply_font(
                r,
                size_pt=10 if not is_header else 10.5,
                color_rgb=RGBColor(255, 255, 255) if is_header else (default_color or RGBColor(31, 56, 100)),
                bold=True
            )
        elif tok.startswith('*') and tok.endswith('*'):
            inner = tok[1:-1]
            r = paragraph.add_run(inner)
            _apply_font(
                r,
                size_pt=10 if not is_header else 10.5,
                color_rgb=RGBColor(255, 255, 255) if is_header else (default_color or RGBColor(89, 89, 89)),
                italic=True
            )
        elif tok.startswith('`') and tok.endswith('`'):
            inner = tok[1:-1]
            r = paragraph.add_run(f" {inner} ")
            _apply_font(
                r,
                font_name="Consolas",
                size_pt=9.5,
                color_rgb=RGBColor(199, 37, 78) if not is_header else RGBColor(255, 255, 255),
                bold=True
            )
        else:
            r = paragraph.add_run(tok)
            _apply_font(
                r,
                size_pt=10 if not is_header else 10.5,
                color_rgb=RGBColor(255, 255, 255) if is_header else (default_color or RGBColor(38, 38, 38))
            )


# ----------------------------------------------------
# 1. Transcript DOCX Generation
# ----------------------------------------------------

def generate_transcript_docx(task: dict, items: list, resolve_speaker) -> io.BytesIO:
    """Render a timestamped, speaker-labelled transcript as a Word document.

    Args:
        task: Task record. ``title`` / ``podcast_name`` / ``metadata`` /
            ``created_at`` are used to build the document header block.
        items: Transcript paragraphs, each a dict with ``start_time`` /
            ``end_time`` / ``speaker`` / ``content`` (``text`` also accepted).
        resolve_speaker: Callable mapping a raw speaker id to a display name.
            Pass ``None`` to keep the raw ids.

    Returns:
        A ``BytesIO`` positioned at offset 0 containing a complete ``.docx``.
        The caller owns the buffer and may stream or write it directly.
    """
    doc = Document()
    title = task.get("title", "转录文本")
    podcast = task.get("podcast_name", "未知播客")
    meta = task.get("metadata", {}) or {}

    # Page setup: A4, 1 inch margins (页眉页脚保持空白，不出现工具名称)
    for s in doc.sections:
        s.top_margin = Inches(1)
        s.bottom_margin = Inches(1)
        s.left_margin = Inches(1)
        s.right_margin = Inches(1)

    # Document Header Title
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(12)
    title_p.paragraph_format.space_after = Pt(4)
    r_tag = title_p.add_run(f"【{podcast}】\n")
    _apply_font(r_tag, size_pt=14, color_rgb=RGBColor(46, 117, 182), bold=True)
    r_title = title_p.add_run(title)
    _apply_font(r_title, size_pt=20, color_rgb=RGBColor(31, 56, 100), bold=True)

    # Metadata callout box
    meta_p = doc.add_paragraph()
    meta_p.paragraph_format.space_before = Pt(8)
    meta_p.paragraph_format.space_after = Pt(16)

    total_secs = items[-1].get("end_time", 0) if items else 0
    total_chars = sum(len(p.get("content", "") or p.get("text", "")) for p in items)
    created_at = task.get("created_at", "")[:10]

    meta_text = (
        f"🎙️ 播客节目：{podcast}  |  ⏱️ 节目时长：{_format_seconds(total_secs)}\n"
        f"📊 文本统计：共 {len(items)} 个段落，约 {total_chars:,} 字符  |  📅 创建时间：{created_at}"
    )
    r_meta = meta_p.add_run(meta_text)
    _apply_font(r_meta, size_pt=9.5, color_rgb=RGBColor(89, 89, 89))

    # Add divider line
    div_p = doc.add_paragraph()
    div_p.paragraph_format.space_before = Pt(2)
    div_p.paragraph_format.space_after = Pt(12)
    pPr = div_p._p.get_or_add_pPr()
    pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="1" w:color="D0D7DE"/></w:pBdr>')
    pPr.append(pBdr)

    # Transcript Paragraphs
    for p in items:
        start_t = _format_seconds(p.get("start_time", 0))
        end_t = _format_seconds(p.get("end_time", 0))
        raw_speaker = p.get("speaker", "")
        speaker = resolve_speaker(raw_speaker) if resolve_speaker else raw_speaker
        if not speaker or speaker == "UNKNOWN_SPEAKER":
            speaker = "发言人"
        content = (p.get("content", "") or p.get("text", "")).strip()

        para_p = doc.add_paragraph()
        para_p.paragraph_format.space_before = Pt(4)
        para_p.paragraph_format.space_after = Pt(8)
        para_p.paragraph_format.line_spacing = 1.25

        # Timestamp badge
        r_time = para_p.add_run(f"[{start_t} - {end_t}] ")
        _apply_font(r_time, size_pt=9, color_rgb=RGBColor(46, 117, 182), bold=True)

        # Speaker
        r_spk = para_p.add_run(f"{speaker}：")
        _apply_font(r_spk, size_pt=10, color_rgb=RGBColor(31, 56, 100), bold=True)

        # Text
        r_txt = para_p.add_run(content)
        _apply_font(r_txt, size_pt=10.5, color_rgb=RGBColor(38, 38, 38))

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


# ----------------------------------------------------
# 2. AI Summary DOCX Generation
# ----------------------------------------------------

def generate_summary_docx(task: dict) -> io.BytesIO:
    """Render a Markdown AI summary report as a formatted Word document.

    Supports the Markdown subset the summary pipeline emits: ATX headings
    (``#``–``####``), bullet and numbered lists, blockquotes, GFM tables,
    fenced code blocks and horizontal rules. Mermaid/flowchart/mindmap fences
    are downgraded to bullet points, since Word cannot render them.

    Args:
        task: Task record. ``title``, ``podcast_name`` and ``summary``
            (Markdown source) are used.

    Returns:
        A ``BytesIO`` positioned at offset 0 containing a complete ``.docx``.
    """
    doc = Document()
    title = task.get("title", "AI 总结报告")
    podcast = task.get("podcast_name", "未知播客")
    summary = task.get("summary", "") or "*暂无 AI 总结内容*"

    # Page setup: A4, 1 inch margins (页眉页脚保持空白，不出现工具名称)
    for s in doc.sections:
        s.top_margin = Inches(1)
        s.bottom_margin = Inches(1)
        s.left_margin = Inches(1)
        s.right_margin = Inches(1)

    in_code_block = False
    code_block_lines = []
    in_table = False
    table_lines = []

    def flush_code_block():
        nonlocal code_block_lines
        if not code_block_lines:
            return
        code_text = "".join(code_block_lines).strip()
        first_line = code_text.splitlines()[0].strip().lower() if code_text else ""
        if any(first_line.startswith(prefix) for prefix in ("mermaid", "graph ", "flowchart", "mindmap", "sequence")):
            # Mermaid/flowchart diagrams do not render in Word; convert to clean structured bullet points
            raw_lines = [l.strip() for l in code_text.splitlines() if l.strip()]
            for cl in raw_lines:
                if any(cl.lower().startswith(p) for p in ("mermaid", "graph ", "flowchart", "mindmap", "sequence", "subgraph", "end")):
                    continue
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(0.25)
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.line_spacing = 1.2
                r_b = p.add_run("▪  ")
                _apply_font(r_b, size_pt=8, color_rgb=RGBColor(46, 117, 182), bold=True)
                node_text = re.sub(r'[-=]+>+', ' ➔ ', cl)
                node_text = re.sub(r'[\[\]{}()]', '', node_text).strip()
                _add_formatted_runs(p, node_text)
            code_block_lines = []
            return

        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.left_indent = Inches(0.2)
        p.paragraph_format.right_indent = Inches(0.2)
        r = p.add_run(code_text)
        _apply_font(r, font_name="Consolas", size_pt=9, color_rgb=RGBColor(64, 64, 64))
        pPr = p._p.get_or_add_pPr()
        pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:left w:val="single" w:sz="24" w:space="8" w:color="2E75B6"/></w:pBdr>')
        pPr.append(pBdr)
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F4F6F9"/>')
        pPr.append(shd)
        code_block_lines = []

    def flush_table():
        nonlocal table_lines
        if not table_lines:
            return
        rows_data = []
        for line in table_lines:
            if re.match(r'^\s*\|?\s*:?-+:?\s*\|', line):
                continue
            cols = [c.strip() for c in line.strip().strip('|').split('|')]
            rows_data.append(cols)

        if not rows_data:
            table_lines = []
            return

        num_cols = max(len(r) for r in rows_data)
        for r in rows_data:
            while len(r) < num_cols:
                r.append("")

        table = doc.add_table(rows=len(rows_data), cols=num_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        _set_table_borders(table, color="D0D7DE")

        for i, row in enumerate(rows_data):
            tr = table.rows[i]
            is_header = (i == 0)
            for j, cell_text in enumerate(row):
                cell = tr.cells[j]
                _set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
                if is_header:
                    _set_cell_background(cell, "2E75B6")
                elif i % 2 == 1:
                    _set_cell_background(cell, "F9FAFB")
                else:
                    _set_cell_background(cell, "FFFFFF")

                cp = cell.paragraphs[0]
                cp.paragraph_format.space_before = Pt(2)
                cp.paragraph_format.space_after = Pt(2)
                cp.paragraph_format.line_spacing = 1.15
                _add_formatted_runs(cp, cell_text, is_header=is_header)

        p_space = doc.add_paragraph()
        p_space.paragraph_format.space_before = Pt(4)
        p_space.paragraph_format.space_after = Pt(6)
        table_lines = []

    lines = summary.splitlines()

    for line in lines:
        raw = line.rstrip('\r\n')

        # Code block toggle
        if raw.startswith("```"):
            if in_code_block:
                in_code_block = False
                flush_code_block()
            else:
                in_code_block = True
                code_block_lines = []
            continue

        if in_code_block:
            code_block_lines.append(line + "\n")
            continue

        # Markdown Table line
        if '|' in raw and (raw.strip().startswith('|') or raw.strip().endswith('|')):
            in_table = True
            table_lines.append(raw)
            continue
        elif in_table:
            in_table = False
            flush_table()

        stripped = raw.strip()
        if not stripped:
            continue

        # Divider
        if re.match(r'^-{3,}$', stripped) or re.match(r'^\*{3,}$', stripped):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(8)
            pPr = p._p.get_or_add_pPr()
            pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="1" w:color="E0E0E0"/></w:pBdr>')
            pPr.append(pBdr)
            continue

        # Headings
        if stripped.startswith('# '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(16)
            p.paragraph_format.space_after = Pt(8)
            r = p.add_run(stripped[2:].strip())
            _apply_font(r, size_pt=20, color_rgb=RGBColor(31, 56, 100), bold=True)
        elif stripped.startswith('## '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(6)
            r = p.add_run(stripped[3:].strip())
            _apply_font(r, size_pt=15, color_rgb=RGBColor(46, 117, 182), bold=True)
            pPr = p._p.get_or_add_pPr()
            pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="4" w:color="D0D7DE"/></w:pBdr>')
            pPr.append(pBdr)
        elif stripped.startswith('### '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            r = p.add_run(stripped[4:].strip())
            _apply_font(r, size_pt=12.5, color_rgb=RGBColor(31, 56, 100), bold=True)
        elif stripped.startswith('#### '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(stripped[5:].strip())
            _apply_font(r, size_pt=11, color_rgb=RGBColor(46, 117, 182), bold=True)
        elif stripped.startswith('> '):
            # Blockquote
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.right_indent = Inches(0.2)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(6)
            pPr = p._p.get_or_add_pPr()
            pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:left w:val="single" w:sz="24" w:space="8" w:color="2E75B6"/></w:pBdr>')
            pPr.append(pBdr)
            shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F9FBFD"/>')
            pPr.append(shd)
            _add_formatted_runs(p, stripped[2:].strip(), default_color=RGBColor(89, 89, 89))
        elif re.match(r'^[-*+]\s+', stripped):
            # Bullet list
            content = re.sub(r'^[-*+]\s+', '', stripped)
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.25
            r_bullet = p.add_run("▪  ")
            _apply_font(r_bullet, size_pt=8, color_rgb=RGBColor(46, 117, 182), bold=True)
            _add_formatted_runs(p, content)
        elif re.match(r'^\d+\.\s+', stripped):
            # Numbered list
            m = re.match(r'^(\d+\.)\s+(.*)', stripped)
            num_prefix = m.group(1)
            content = m.group(2)
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.25
            r_num = p.add_run(f"{num_prefix} ")
            _apply_font(r_num, size_pt=10, color_rgb=RGBColor(31, 56, 100), bold=True)
            _add_formatted_runs(p, content)
        else:
            # Regular paragraph
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(5)
            p.paragraph_format.line_spacing = 1.25
            _add_formatted_runs(p, stripped)

    if in_table:
        flush_table()
    if in_code_block:
        flush_code_block()

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf
