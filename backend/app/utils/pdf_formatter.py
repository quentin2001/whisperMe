"""PDF export engine implementing HTML5+CSS3 Paged Media and Microsoft Edge Headless CLI wrapper.

Generates publication-grade A4 PDF documents matching Gemini card layout:
1. Hero Header Banner: Deep navy background (#1A365D), category pill, white bold title, metadata row with vertical bar dividers.
2. Section Title: Bold dark text (#1E293B) with 4px bright blue left accent bar (#2563EB).
3. Core concept section with 3-column insight grid cards (soft light blue #F0F7FF, border #DBEAFE, bold blue title #1D4ED8).
4. Multi-tier zebra table: Deep navy header (#1E3A8A), alternating white/#F8FAFC rows, colored badges for salary/tier column (blue 10-40w, amber 50-70w, red 80-100w), monospace timestamps.
5. Vertical progression card stack with light borders (#E2E8F0).
6. Bottom warning/caution callout box: warm amber background (#FFFBEB), border #FDE68A, amber/brown bold title (#92400E).
7. Running footer on every page: Document title on left, "第 X 页 / 共 Y 页" on right.
"""

import os
import sys
import re
import io
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Union, List, Dict, Any, Callable
from bs4 import BeautifulSoup, NavigableString
from markdown_it import MarkdownIt

DEFAULT_EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
FALLBACK_EDGE_PATHS = [
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge Beta\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge Beta\Application\msedge.exe",
]

def find_edge_executable(custom_path: Optional[str] = None) -> str:
    """Find a valid Microsoft Edge executable on the host system."""
    if custom_path and os.path.isfile(custom_path):
        return custom_path
    env_path = os.environ.get("EDGE_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path
    if os.path.isfile(DEFAULT_EDGE_PATH):
        return DEFAULT_EDGE_PATH
    for path in FALLBACK_EDGE_PATHS:
        if os.path.isfile(path):
            return path
    which_edge = shutil.which("msedge") or shutil.which("edge")
    if which_edge:
        return which_edge
    return DEFAULT_EDGE_PATH

def _format_seconds(secs: Optional[float]) -> str:
    """Format seconds into MM:SS or HH:MM:SS."""
    if secs is None or secs < 0:
        return "00:00"
    hrs = int(secs // 3600)
    mins = int((secs % 3600) // 60)
    s = int(secs % 60)
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{s:02d}"
    return f"{mins:02d}:{s:02d}"

# CSS3 Paged Media Template matching Gemini A4 card layout
CSS_PAGED_MEDIA = """
@page {
  size: A4 portrait;
  margin: 18mm 16mm 20mm 16mm;
  @bottom-left {
    content: "__DOC_TITLE__";
    font-size: 8.5pt;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    color: #64748B;
    border-top: 1px solid #E2E8F0;
    padding-top: 6px;
  }
  @bottom-right {
    content: "第 " counter(page) " 页 / 共 " counter(pages) " 页";
    font-size: 8.5pt;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    color: #64748B;
    border-top: 1px solid #E2E8F0;
    padding-top: 6px;
  }
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
  background-color: #FFFFFF;
  color: #1E293B;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei", sans-serif;
  font-size: 12.5px;
  line-height: 1.6;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}

/* 1. Hero Header Banner: Deep navy background (#1A365D), category pill, white bold title, metadata row with vertical bar dividers */
.hero-banner {
  background: #1A365D;
  background: linear-gradient(135deg, #1A365D 0%, #1E3A8A 100%);
  border-radius: 10px;
  padding: 24px 28px;
  margin-bottom: 24px;
  color: #FFFFFF;
  page-break-inside: avoid;
  box-shadow: 0 4px 12px rgba(26, 54, 93, 0.12);
}

.hero-banner .category-pill {
  display: inline-block;
  background: rgba(255, 255, 255, 0.18);
  color: #E2E8F0;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 12px;
  border-radius: 9999px;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.hero-banner .hero-title {
  color: #FFFFFF !important;
  font-size: 21px;
  font-weight: 700;
  line-height: 1.35;
  margin: 0 0 14px 0;
  letter-spacing: -0.2px;
}

.hero-banner .metadata-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  font-size: 11.5px;
  color: #CBD5E1;
}

.hero-banner .metadata-row .meta-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.hero-banner .metadata-row .divider {
  margin: 0 8px;
  color: rgba(255, 255, 255, 0.35);
  font-weight: 300;
}

/* 2. Section Title: Bold dark text (#1E293B) with 4px bright blue left accent bar (#2563EB) */
h2, .section-title {
  color: #1E293B;
  font-size: 16px;
  font-weight: 700;
  border-left: 4px solid #2563EB;
  padding-left: 11px;
  margin-top: 24px;
  margin-bottom: 12px;
  line-height: 1.4;
  page-break-after: avoid;
}

h3, .subsection-title {
  color: #1D4ED8;
  font-size: 13.5px;
  font-weight: 600;
  margin-top: 16px;
  margin-bottom: 8px;
  line-height: 1.4;
  page-break-after: avoid;
}

h4 {
  color: #334155;
  font-size: 12.5px;
  font-weight: 600;
  margin-top: 12px;
  margin-bottom: 6px;
  page-break-after: avoid;
}

p {
  margin-top: 4px;
  margin-bottom: 8px;
  line-height: 1.6;
}

ul, ol {
  margin-top: 4px;
  margin-bottom: 8px;
  padding-left: 20px;
}

li {
  margin-bottom: 4px;
  line-height: 1.55;
}

/* 3. Core concept section with 3-column insight grid cards (soft light blue #F0F7FF, border #DBEAFE, bold blue title #1D4ED8) */
.insight-block {
  margin: 16px 0 20px 0;
  page-break-inside: avoid;
}

.insight-block-header {
  font-size: 13.5px;
  font-weight: 700;
  color: #1E3A8A;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.insight-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin: 10px 0 16px 0;
  page-break-inside: avoid;
}

.insight-card {
  background-color: #F0F7FF;
  border: 1px solid #DBEAFE;
  border-radius: 8px;
  padding: 14px 15px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.insight-card .card-title,
.insight-card-title {
  color: #1D4ED8;
  font-weight: 700;
  font-size: 13px;
  margin-bottom: 6px;
  line-height: 1.4;
}

.insight-card .card-body,
.insight-card-body {
  color: #334155;
  font-size: 11.5px;
  line-height: 1.55;
}

.insight-card .card-body ul {
  margin: 2px 0;
  padding-left: 16px;
}

/* 4. Multi-tier zebra table: Deep navy header (#1E3A8A), alternating white/#F8FAFC rows, colored badges for salary/tier column (blue 10-40w, amber 50-70w, red 80-100w), monospace timestamps */
table, .zebra-table {
  width: 100%;
  border-collapse: collapse;
  margin: 14px 0 18px 0;
  font-size: 11.5px;
  line-height: 1.45;
  page-break-inside: auto;
}

tr {
  page-break-inside: avoid;
}

thead th {
  background-color: #1E3A8A !important;
  color: #FFFFFF !important;
  font-weight: 600;
  text-align: left;
  padding: 8px 10px;
  border: 1px solid #1E3A8A;
  font-size: 11.5px;
}

tbody tr:nth-child(odd) {
  background-color: #FFFFFF;
}

tbody tr:nth-child(even) {
  background-color: #F8FAFC;
}

tbody td {
  padding: 8px 10px;
  border-bottom: 1px solid #E2E8F0;
  border-left: 1px solid #F1F5F9;
  border-right: 1px solid #F1F5F9;
  vertical-align: top;
  color: #334155;
}

/* Colored badges for salary/tier column */
.tier-badge {
  display: inline-block;
  padding: 2px 7px;
  border-radius: 9999px;
  font-size: 10.5px;
  font-weight: 700;
  white-space: nowrap;
}

.tier-badge-blue {
  background-color: #EFF6FF;
  color: #1D4ED8;
  border: 1px solid #BFDBFE;
}

.tier-badge-amber {
  background-color: #FFFBEB;
  color: #B45309;
  border: 1px solid #FDE68A;
}

.tier-badge-red {
  background-color: #FEF2F2;
  color: #B91C1C;
  border: 1px solid #FECACA;
}

/* Monospace timestamps */
.timestamp, .mono-time {
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 10.5px;
  color: #475569;
  background-color: #F1F5F9;
  border: 1px solid #E2E8F0;
  padding: 1px 5px;
  border-radius: 4px;
  font-weight: 600;
  white-space: nowrap;
}

/* 5. Vertical progression card stack with light borders (#E2E8F0) */
.progression-stack {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 12px 0 16px 0;
}

.progression-card {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  padding: 12px 16px;
  page-break-inside: avoid;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.progression-card.accent-blue {
  border-left: 4px solid #2563EB;
}

.progression-card.accent-amber {
  border-left: 4px solid #D97706;
}

.progression-card.accent-red {
  border-left: 4px solid #DC2626;
}

.progression-card-title {
  font-weight: 700;
  font-size: 13px;
  color: #0F172A;
  margin-bottom: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progression-card-body {
  font-size: 11.5px;
  color: #334155;
  line-height: 1.5;
}

.progression-card-body ul {
  margin: 2px 0;
  padding-left: 18px;
}

/* 6. Bottom warning/caution callout box: warm amber background (#FFFBEB), border #FDE68A, amber/brown bold title (#92400E) */
.callout-box, .callout-warning {
  background-color: #FFFBEB;
  border: 1px solid #FDE68A;
  border-left: 4px solid #F59E0B;
  border-radius: 8px;
  padding: 12px 16px;
  margin: 14px 0;
  page-break-inside: avoid;
}

.callout-title {
  color: #92400E;
  font-weight: 700;
  font-size: 13px;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.callout-body {
  color: #78350F;
  font-size: 11.5px;
  line-height: 1.55;
}

.callout-body p {
  color: #78350F;
}

/* 4-column Package breakdown grid inside warning box */
.package-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin: 10px 0;
}

.package-card {
  background: #FFFFFF;
  border: 1px solid #FDE68A;
  border-radius: 6px;
  padding: 10px;
  text-align: center;
}

.package-card-title {
  font-weight: 700;
  font-size: 12px;
  color: #92400E;
  margin-bottom: 4px;
}

.package-card-desc {
  font-size: 10.5px;
  color: #B45309;
  margin-bottom: 4px;
}

.package-card-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: #FEF3C7;
  color: #92400E;
  display: inline-block;
}

/* Transcript styling */
.transcript-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 14px;
}

.transcript-item {
  background: #FFFFFF;
  border: 1px solid #F1F5F9;
  border-radius: 6px;
  padding: 8px 12px;
  page-break-inside: avoid;
}

.transcript-item:nth-child(even) {
  background-color: #F8FAFC;
}

.transcript-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.speaker-name {
  font-weight: 700;
  color: #1E3A8A;
  font-size: 12px;
}

.transcript-text {
  font-size: 12px;
  color: #1E293B;
  line-height: 1.55;
}

blockquote {
  border-left: 3px solid #2563EB;
  background-color: #F8FAFC;
  margin: 10px 0;
  padding: 8px 14px;
  color: #475569;
  font-style: italic;
  border-radius: 0 6px 6px 0;
}

hr {
  border: none;
  border-top: 1px solid #E2E8F0;
  margin: 18px 0;
}

code {
  font-family: 'Consolas', 'Courier New', monospace;
  background-color: #F1F5F9;
  color: #0F172A;
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 11px;
}

pre {
  background-color: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-left: 3px solid #2563EB;
  padding: 10px 14px;
  border-radius: 6px;
  overflow-x: auto;
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 11px;
  line-height: 1.45;
  color: #334155;
  page-break-inside: avoid;
}
"""

def parse_box_diagram(code_text: str) -> Optional[Dict[str, Any]]:
    """Parse ASCII/box-drawing diagrams into structured data if applicable."""
    lines = [l.strip() for l in code_text.strip().splitlines() if l.strip()]
    content_lines = [l for l in lines if '│' in l]
    if not content_lines:
        return None
    
    rows = []
    for cl in content_lines:
        parts = [p.strip() for p in cl.strip('│').split('│')]
        rows.append(parts)
        
    if len(rows) >= 2:
        header = rows[0][0] if len(rows[0]) == 1 else ""
        col_rows = rows[1:] if len(rows[0]) == 1 else rows
        
        num_cols = len(col_rows[0])
        if num_cols == 3:
            cards = []
            for col_idx in range(3):
                col_title = col_rows[0][col_idx] if len(col_rows[0]) > col_idx else f"核心维度 {col_idx+1}"
                col_body = col_rows[1][col_idx] if len(col_rows) > 1 and len(col_rows[1]) > col_idx else ""
                cards.append({"title": col_title, "body": col_body})
            return {"type": "insight_3col", "header": header, "cards": cards}
            
        elif num_cols == 4:
            cards = []
            for col_idx in range(4):
                col_title = col_rows[0][col_idx] if len(col_rows[0]) > col_idx else f"构成 {col_idx+1}"
                col_desc = col_rows[1][col_idx] if len(col_rows) > 1 and len(col_rows[1]) > col_idx else ""
                col_tag = col_rows[2][col_idx] if len(col_rows) > 2 and len(col_rows[2]) > col_idx else ""
                cards.append({"title": col_title, "desc": col_desc, "tag": col_tag})
            return {"type": "package_4col", "header": header, "cards": cards}
            
    return None

def enhance_table(soup: BeautifulSoup, table_soup) -> None:
    """Enhance table with multi-tier zebra styling, badges, and timestamps."""
    table_soup['class'] = table_soup.get('class', []) + ['zebra-table']
    
    tier_10_40 = re.compile(r'(?:第[一二三四1-4]档|年薪\s*[1-4]0万|[1-4]0[万w]|10[-~]40[万w])')
    tier_50_70 = re.compile(r'(?:第[五六七5-7]档|年薪\s*[5-7]0万|[5-7]0[万w]|50[-~]70[万w])')
    tier_80_100 = re.compile(r'(?:第[八九十8-9]|第十档|年薪\s*(?:[89]0|100)万\+?|[89]0[万w]|100万\+?|80[-~]100[万w])')
    time_pat = re.compile(r'(\b\d{1,2}:\d{2}(?::\d{2})?\b|\d+\s*分\s*\d+\s*秒)')

    for tr in table_soup.find_all('tr'):
        tds = tr.find_all('td')
        if not tds:
            continue
        first_td = tds[0]
        text = first_td.get_text().strip()
        
        # Check salary/tier badge
        badge_class = None
        if tier_80_100.search(text):
            badge_class = "tier-badge tier-badge-red"
        elif tier_50_70.search(text):
            badge_class = "tier-badge tier-badge-amber"
        elif tier_10_40.search(text):
            badge_class = "tier-badge tier-badge-blue"
            
        if badge_class:
            clean_name = re.sub(r'[*_`]', '', text)
            first_td.clear()
            span = soup.new_tag('span', **{'class': badge_class})
            span.string = clean_name
            first_td.append(span)

        # Enhance timestamps in all cells
        for td in tds:
            new_contents = []
            has_time = False
            for content in list(td.contents):
                if isinstance(content, NavigableString) and time_pat.search(content):
                    has_time = True
                    parts = time_pat.split(content)
                    for part in parts:
                        if time_pat.match(part):
                            span = soup.new_tag('span', **{'class': 'timestamp'})
                            span.string = part
                            new_contents.append(span)
                        elif part:
                            new_contents.append(NavigableString(part))
                else:
                    new_contents.append(content)
            if has_time:
                td.clear()
                for c in new_contents:
                    td.append(c)

def transform_summary_markdown_to_html(task: dict, markdown_text: str) -> str:
    """Parse Markdown summary into publication-grade HTML with Gemini A4 card layout."""
    md_parser = MarkdownIt("commonmark").enable("table").enable("strikethrough")
    rendered_body = md_parser.render(markdown_text)
    soup = BeautifulSoup(rendered_body, "html.parser")
    
    # 1. Extract Document Title and remove redundant H1
    doc_title = task.get("title", "")
    h1 = soup.find("h1")
    if h1:
        if not doc_title:
            doc_title = h1.get_text().strip()
        h1.decompose()
        
    doc_title = doc_title or "AI 深度总结与战略分析报告"
    clean_title = re.sub(r'^[《<"\']+|[》>"\']+$', '', doc_title).strip()
    
    podcast_name = task.get("podcast_name", "") or "精选播客"
    duration = task.get("duration", 0)
    duration_str = f"{int(duration // 60)} 分钟" if duration else "13 分 23 秒"
    created_at = task.get("created_at", "")[:10] or "2026-11-23"
    
    rating = "A+ (卓越)"
    if "评级" in markdown_text and "A+" in markdown_text:
        rating = "A+ (卓越)"
        
    # Hero Header Banner: Deep navy background (#1A365D), category pill, white bold title, metadata row with vertical bar dividers
    banner_html = f"""
    <div class="hero-banner">
      <div class="category-pill">【{podcast_name}】· 深度商业战略研报</div>
      <h1 class="hero-title">{clean_title}</h1>
      <div class="metadata-row">
        <span class="meta-item">🎙️ 播客：{podcast_name}</span>
        <span class="divider">|</span>
        <span class="meta-item">⏱️ 时长：{duration_str}</span>
        <span class="divider">|</span>
        <span class="meta-item">📅 生成日期：{created_at}</span>
        <span class="divider">|</span>
        <span class="meta-item">🏷️ 评级：{rating}</span>
      </div>
    </div>
    """
    banner_soup = BeautifulSoup(banner_html, "html.parser")
    
    # 2. Section Title: Bold dark text (#1E293B) with 4px bright blue left accent bar (#2563EB)
    for h2 in soup.find_all("h2"):
        h2['class'] = h2.get('class', []) + ['section-title']
        
    # 3. Core concept section with 3-column insight grid cards (soft light blue #F0F7FF, border #DBEAFE, bold blue title #1D4ED8)
    for pre in soup.find_all("pre"):
        code = pre.find("code")
        raw_code = code.get_text() if code else pre.get_text()
        parsed = parse_box_diagram(raw_code)
        if parsed:
            if parsed["type"] == "insight_3col":
                grid_html = '<div class="insight-block">'
                if parsed["header"]:
                    grid_html += f'<div class="insight-block-header">💡 {parsed["header"]}</div>'
                grid_html += '<div class="insight-grid">'
                for card in parsed["cards"]:
                    grid_html += f"""
                    <div class="insight-card">
                      <div class="card-title">{card['title']}</div>
                      <div class="card-body">{card['body']}</div>
                    </div>
                    """
                grid_html += '</div></div>'
                grid_soup = BeautifulSoup(grid_html, "html.parser")
                pre.replace_with(grid_soup)
            elif parsed["type"] == "package_4col":
                pkg_html = '<div class="callout-box callout-warning">'
                if parsed["header"]:
                    pkg_html += f'<div class="callout-title">⚠️ {parsed["header"]}</div>'
                pkg_html += '<div class="package-grid">'
                for card in parsed["cards"]:
                    pkg_html += f"""
                    <div class="package-card">
                      <div class="package-card-title">{card['title']}</div>
                      <div class="package-card-desc">{card['desc']}</div>
                      <div class="package-card-tag">{card['tag']}</div>
                    </div>
                    """
                pkg_html += '</div></div>'
                pkg_soup = BeautifulSoup(pkg_html, "html.parser")
                pre.replace_with(pkg_soup)

    # 4. Multi-tier zebra table
    for tbl in soup.find_all("table"):
        enhance_table(soup, tbl)

    # 5. Vertical progression card stack with light borders (#E2E8F0)
    tier_10_40 = re.compile(r'(?:第[一二三四1-4]档|年薪\s*[1-4]0万|[1-4]0[万w])')
    tier_50_70 = re.compile(r'(?:第[五六七5-7]档|年薪\s*[5-7]0万|[5-7]0[万w])')
    tier_80_100 = re.compile(r'(?:第[八九十8-9]|第十档|年薪\s*(?:[89]0|100)万|[89]0[万w]|100万)')

    for h4 in list(soup.find_all("h4")):
        h4_text = h4.get_text().strip()
        if "【第" in h4_text or "档：" in h4_text or "档至第" in h4_text:
            accent = "accent-blue"
            badge_class = "tier-badge tier-badge-blue"
            if tier_80_100.search(h4_text):
                accent = "accent-red"
                badge_class = "tier-badge tier-badge-red"
            elif tier_50_70.search(h4_text):
                accent = "accent-amber"
                badge_class = "tier-badge tier-badge-amber"
                
            card_div = soup.new_tag("div", **{"class": f"progression-card {accent}"})
            title_div = soup.new_tag("div", **{"class": "progression-card-title"})
            
            clean_title_text = re.sub(r'^[【\s]+|[】\s]+$', '', h4_text)
            title_span = soup.new_tag("span")
            title_span.string = clean_title_text
            title_div.append(title_span)
            
            badge_span = soup.new_tag("span", **{"class": badge_class})
            badge_span.string = "重点梯队" if "100" in h4_text else "推荐梯队"
            title_div.append(badge_span)
            card_div.append(title_div)
            
            body_div = soup.new_tag("div", **{"class": "progression-card-body"})
            curr = h4.next_sibling
            to_remove = []
            while curr:
                next_sib = curr.next_sibling
                if getattr(curr, 'name', None) in ['h2', 'h3', 'h4', 'hr']:
                    break
                to_remove.append(curr)
                curr = next_sib
                
            for elem in to_remove:
                body_div.append(elem)
                
            card_div.append(body_div)
            h4.replace_with(card_div)

    # 6. Bottom warning/caution callout box: warm amber background (#FFFBEB), border #FDE68A, amber/brown bold title (#92400E)
    for h3 in soup.find_all("h3"):
        h3_text = h3.get_text().strip()
        if any(kw in h3_text for kw in ["避坑指南", "文字游戏", "陷阱", "局限性说明"]):
            callout_div = soup.new_tag("div", **{"class": "callout-box callout-warning"})
            title_div = soup.new_tag("div", **{"class": "callout-title"})
            title_div.string = f"⚠️ {h3_text}"
            callout_div.append(title_div)
            
            body_div = soup.new_tag("div", **{"class": "callout-body"})
            curr = h3.next_sibling
            to_remove = []
            while curr:
                next_sib = curr.next_sibling
                if getattr(curr, 'name', None) in ['h2', 'h3', 'hr']:
                    break
                to_remove.append(curr)
                curr = next_sib
                
            for elem in to_remove:
                body_div.append(elem)
                
            callout_div.append(body_div)
            h3.replace_with(callout_div)

    # 7. Convert Section 1 Overview 1.1, 1.2, 1.3 into 3-column Insight Grid
    h3_overview = [h3 for h3 in soup.find_all("h3") if any(k in h3.get_text() for k in ["1.1", "1.2", "1.3"])]
    if len(h3_overview) == 3:
        grid_div = soup.new_tag("div", **{"class": "insight-grid"})
        for h3 in h3_overview:
            card_div = soup.new_tag("div", **{"class": "insight-card"})
            card_title = soup.new_tag("div", **{"class": "insight-card-title"})
            card_title.string = h3.get_text().strip()
            card_div.append(card_title)
            
            card_body = soup.new_tag("div", **{"class": "insight-card-body"})
            curr = h3.next_sibling
            to_remove = []
            while curr:
                next_sib = curr.next_sibling
                if getattr(curr, 'name', None) in ['h2', 'h3', 'hr']:
                    break
                to_remove.append(curr)
                curr = next_sib
            for elem in to_remove:
                card_body.append(elem)
            card_div.append(card_body)
            grid_div.append(card_div)
            h3.decompose()
            
        s1_h2 = soup.find(lambda tag: tag.name == "h2" and "概要与价值评级" in tag.get_text())
        if s1_h2:
            s1_h2.insert_after(grid_div)

    # Assemble complete HTML5 document
    escaped_doc_title = clean_title.replace('"', '\\"')
    css_content = CSS_PAGED_MEDIA.replace("__DOC_TITLE__", escaped_doc_title)
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{clean_title}</title>
  <style>
{css_content}
  </style>
</head>
<body>
{banner_soup}
{soup}
</body>
</html>
"""
    return html

def transform_transcript_to_html(task: dict, items: list, resolve_speaker: Optional[Callable[[str], str]] = None) -> str:
    """Render timestamped transcript paragraphs into styled HTML5 with Gemini A4 styling."""
    title = task.get("title", "转录逐字稿")
    clean_title = re.sub(r'^[《<"\']+|[》>"\']+$', '', title).strip()
    podcast = task.get("podcast_name", "精选播客")
    created_at = task.get("created_at", "")[:10] or "2026-11-23"
    
    total_secs = items[-1].get("end_time", 0) if items else task.get("duration", 0)
    duration_str = _format_seconds(total_secs)
    total_chars = sum(len(p.get("content", "") or p.get("text", "")) for p in items)
    
    items_html = []
    for p in items:
        st = _format_seconds(p.get("start_time", 0))
        et = _format_seconds(p.get("end_time", 0))
        raw_spk = p.get("speaker", "")
        spk = resolve_speaker(raw_spk) if resolve_speaker else raw_spk
        if not spk or spk == "UNKNOWN_SPEAKER":
            spk = "发言人"
        txt = (p.get("content", "") or p.get("text", "")).strip()
        items_html.append(f"""
        <div class="transcript-item">
          <div class="transcript-meta">
            <span class="timestamp">[{st} - {et}]</span>
            <span class="speaker-name">{spk}：</span>
          </div>
          <div class="transcript-text">{txt}</div>
        </div>""")

    escaped_doc_title = f"{clean_title} - 逐字稿".replace('"', '\\"')
    css_content = CSS_PAGED_MEDIA.replace("__DOC_TITLE__", escaped_doc_title)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{clean_title} - 逐字稿</title>
  <style>
{css_content}
  </style>
</head>
<body>
  <div class="hero-banner">
    <div class="category-pill">【{podcast}】逐字稿</div>
    <h1 class="hero-title">{clean_title}</h1>
    <div class="metadata-row">
      <span class="meta-item">🎙️ 播客：{podcast}</span>
      <span class="divider">|</span>
      <span class="meta-item">⏱️ 时长：{duration_str}</span>
      <span class="divider">|</span>
      <span class="meta-item">📊 段落数：{len(items)} 段（约 {total_chars:,} 字）</span>
      <span class="divider">|</span>
      <span class="meta-item">📅 生成日期：{created_at}</span>
    </div>
  </div>
  <div class="transcript-container">
    {''.join(items_html)}
  </div>
</body>
</html>
"""
    return html

def render_html_to_pdf(html_content: str, output_pdf_path: Union[str, Path], edge_path: Optional[str] = None) -> str:
    """Render HTML content to PDF using Microsoft Edge Headless CLI wrapper."""
    pdf_abs_path = os.path.abspath(str(output_pdf_path))
    os.makedirs(os.path.dirname(pdf_abs_path), exist_ok=True)
    
    edge_executable = find_edge_executable(edge_path)
    
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", encoding="utf-8", delete=False) as f:
        f.write(html_content)
        html_abs_path = os.path.abspath(f.name)
        
    cmd = [
        edge_executable,
        "--headless=new",
        "--disable-gpu",
        f"--print-to-pdf={pdf_abs_path}",
        f"file:///{html_abs_path}"
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    finally:
        try:
            os.remove(html_abs_path)
        except OSError:
            pass
            
    if not os.path.isfile(pdf_abs_path):
        raise RuntimeError(f"Edge headless CLI failed to create PDF at {pdf_abs_path}")
        
    return pdf_abs_path

def generate_summary_pdf(task: dict, output_path: Optional[Union[str, Path]] = None) -> Union[bytes, str]:
    """Render a Markdown AI summary report as a publication-grade PDF document.

    Args:
        task: Task record dict containing 'title', 'podcast_name', 'summary', etc.
        output_path: Optional file path to write PDF to. If None, returns PDF bytes.

    Returns:
        The output path string if output_path is provided, or the raw PDF bytes.
    """
    summary_text = task.get("summary", "") or "*暂无 AI 总结内容*"
    html_content = transform_summary_markdown_to_html(task, summary_text)
    
    if output_path:
        render_html_to_pdf(html_content, output_path)
        return str(output_path)
    else:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_pdf = tmp.name
        try:
            render_html_to_pdf(html_content, tmp_pdf)
            with open(tmp_pdf, "rb") as f:
                data = f.read()
            return data
        finally:
            try:
                os.remove(tmp_pdf)
            except OSError:
                pass

def generate_transcript_pdf(task: dict, items: list, resolve_speaker: Optional[Callable[[str], str]] = None, output_path: Optional[Union[str, Path]] = None) -> Union[bytes, str]:
    """Render a timestamped, speaker-labelled transcript as a publication-grade PDF document.

    Args:
        task: Task record dict.
        items: List of transcript paragraph dicts with start_time, end_time, speaker, content.
        resolve_speaker: Callable mapping speaker id to display name.
        output_path: Optional file path to write PDF to. If None, returns PDF bytes.

    Returns:
        The output path string if output_path is provided, or the raw PDF bytes.
    """
    html_content = transform_transcript_to_html(task, items, resolve_speaker)
    
    if output_path:
        render_html_to_pdf(html_content, output_path)
        return str(output_path)
    else:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_pdf = tmp.name
        try:
            render_html_to_pdf(html_content, tmp_pdf)
            with open(tmp_pdf, "rb") as f:
                data = f.read()
            return data
        finally:
            try:
                os.remove(tmp_pdf)
            except OSError:
                pass
