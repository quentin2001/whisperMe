"""Tests for publication-grade PDF formatting engine (HTML5+CSS3 Paged Media and Edge CLI)."""

import os
import tempfile
from pathlib import Path
import pytest
from bs4 import BeautifulSoup
from app.utils.pdf_formatter import (
    DEFAULT_EDGE_PATH,
    find_edge_executable,
    transform_summary_markdown_to_html,
    transform_transcript_to_html,
    render_html_to_pdf,
    generate_summary_pdf,
    generate_transcript_pdf,
    _format_seconds
)

SAMPLE_MARKDOWN = """# 《毕业就能拿年薪10—100万的大学规划》AI 深度总结与战略分析报告

## 1. 概要与价值评级

### 1.1 核心主旨
本视频系统打破了网络自媒体关于应届生薪资的浮夸叙事。

### 1.2 目标受众
- 在校大学生
- 准应届毕业生

### 1.3 信息价值评级
- 信息密度 (A+)
- 观点独特性 (A+)

## 2. 核心观点与全景脉络

| 薪资阶梯 | 月薪/年薪估算 | 典型代表行业与岗位方向 | 核心门槛与能力要求 | 大学期间关键行动抓手 |
|:---|:---|:---|:---|:---|
| **第一档：年薪10万** | 月薪 7k~8.3k (12~13薪) | 制造业工程师 | 掌握对口硬技能 | 大一通识打底 |
| **第五档：年薪50万** | Base + 股票 + 高额奖金 | 一线互联网核心 SSP Offer | 算法底层调优 | 数理基础极度扎实 |
| **第十档：年薪100万+** | 顶尖科研 Package | 全球顶级量化对冲基金量化研究员 | 独立开辟商业 Alpha | 站在人类认知前沿 |

## 3. 薪资梯队深度拆解与大学行动图谱

#### 【第一档：年薪 10 万】（月薪 7,000 ~ 8,300 元）
- **市场客观定位**：应届生的现实基本盘；
- **大学阶段破局抓手**：尽早确立岗位方向。

#### 【第五档：年薪 50 万】（Base + 股票股权 + 年终重奖）
- **核心逻辑跃迁**：达到不可替代性的分水岭；
- **大学阶段破局抓手**：深入掌握算法底层推导。

#### 【第十档：年薪 100 万+】
- **核心底层逻辑**：超额商业财富的直接分润。

## 4. 论证逻辑链与底层归因分析

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                      应届生薪酬定价的底层三元驱动模型                       │
├───────────────────┬───────────────────────────┬─────────────────────────┤
│    ① 商业造血能力    │      ② 市场替代成本       │     ③ 风险收益比与杠杆   │
│ (你能给企业赚/省多少) │ (市场上找平替需要花多少代价)  │ (你的决策失误带来多大损失)│
└───────────────────┴───────────────────────────┴─────────────────────────┘
```

## 5. 行业现实与避坑指南

### 5.1 严防“年薪总包 Package”的三大文字游戏
在求职过程中，企业 HR 报出的“年薪”往往与实际到手收入存在偏差：

```text
┌───────────────────────────────────────────────────────────────────────┐
│                    真实企业年包（Package）结构拆解                      │
├─────────────────┬─────────────────┬─────────────────┬─────────────────┤
│  1. Base (底薪) │ 2. 绩效奖金     │ 3. 股票/期权    │ 4. 签字费/补贴  │
│  (月薪 × 12)   │ (浮动系数 0~6)  │ (分 3~4 年成熟) │ (仅限入职第一年)│
│  【唯一确定性】  │ 【与考核强挂钩】 │ 【受股价/上市锁】│ 【一次性不可持续】│
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
```
"""

SAMPLE_TASK = {
    "title": "毕业就能拿年薪10—100万的大学规划",
    "podcast_name": "冤种小徐",
    "duration": 803,
    "created_at": "2026-11-22 16:15:00"
}

SAMPLE_PARAGRAPHS = [
    {"start_time": 0.0, "end_time": 1.16, "speaker": "冤种小徐", "content": "如果你还在上大学"},
    {"start_time": 1.16, "end_time": 2.50, "speaker": "冤种小徐", "content": "但不知道自己毕业以后能赚多少钱"}
]

def test_find_edge_executable(tmp_path):
    # 1. 自定义路径直接命中测试
    dummy = tmp_path / "msedge.exe"
    dummy.write_text("dummy")
    assert find_edge_executable(str(dummy)) == str(dummy)

    # 2. 系统路径探测（Windows 上若有 Edge 则验证存在，CI Linux 无 Edge 环境则验证优雅兜底回退字符串）
    path = find_edge_executable()
    assert isinstance(path, str) and len(path) > 0
    if os.path.isfile(DEFAULT_EDGE_PATH):
        assert os.path.isfile(path)

def test_format_seconds():
    assert _format_seconds(0) == "00:00"
    assert _format_seconds(65) == "01:05"
    assert _format_seconds(3665) == "01:01:05"
    # String duration support
    assert _format_seconds("51:24") == "51:24"
    assert _format_seconds("01:05:30") == "01:05:30"
    assert _format_seconds("803") == "13:23"
    assert _format_seconds(None) == "00:00"
    assert _format_seconds("invalid") == "00:00"

def test_duration_string_in_summary_and_transcript():
    task_with_str_dur = dict(SAMPLE_TASK)
    task_with_str_dur["duration"] = "51:24"
    html = transform_summary_markdown_to_html(task_with_str_dur, SAMPLE_MARKDOWN)
    assert "51:24" in html
    
    html_trans = transform_transcript_to_html(task_with_str_dur, SAMPLE_PARAGRAPHS)
    assert html_trans is not None

def test_transform_summary_markdown_elements():
    html = transform_summary_markdown_to_html(SAMPLE_TASK, SAMPLE_MARKDOWN)
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Hero Header Banner
    banner = soup.find("div", class_="hero-banner")
    assert banner is not None
    pill = banner.find("div", class_="category-pill")
    assert "冤种小徐" in pill.get_text()
    assert "毕业就能拿年薪10—100万的大学规划" in banner.find("h1", class_="hero-title").get_text()
    meta = banner.find("div", class_="metadata-row")
    assert meta is not None and "13 分钟" in meta.get_text()
    
    # 2. Section Titles
    h2_list = soup.find_all("h2", class_="section-title")
    assert len(h2_list) >= 5
    
    # 3. 3-column Insight Grid Cards
    grids = soup.find_all("div", class_="insight-grid")
    assert len(grids) >= 1
    cards = soup.find_all("div", class_="insight-card")
    assert len(cards) >= 3
    
    # 4. Multi-tier zebra table
    table = soup.find("table", class_="zebra-table")
    assert table is not None
    # Badges for blue, amber, red
    blue_badges = soup.find_all("span", class_="tier-badge-blue")
    amber_badges = soup.find_all("span", class_="tier-badge-amber")
    red_badges = soup.find_all("span", class_="tier-badge-red")
    assert len(blue_badges) >= 1
    assert len(amber_badges) >= 1
    assert len(red_badges) >= 1
    
    # 5. Vertical progression card stack
    prog_cards = soup.find_all("div", class_="progression-card")
    assert len(prog_cards) >= 3
    
    # 6. Bottom warning/caution callout box
    callout = soup.find("div", class_="callout-warning")
    assert callout is not None
    assert "文字游戏" in callout.get_text()
    
    # 7. CSS3 Paged Media Running Footer
    assert "@bottom-left" in html
    assert "@bottom-right" in html
    assert "counter(page)" in html

def test_transform_transcript_elements():
    html = transform_transcript_to_html(SAMPLE_TASK, SAMPLE_PARAGRAPHS)
    soup = BeautifulSoup(html, "html.parser")
    
    banner = soup.find("div", class_="hero-banner")
    assert banner is not None
    assert "逐字稿" in banner.get_text()
    
    items = soup.find_all("div", class_="transcript-item")
    assert len(items) == 2
    assert "冤种小徐" in items[0].get_text()
    assert "如果你还在上大学" in items[0].get_text()
    ts = items[0].find("span", class_="timestamp")
    assert ts is not None and "[00:00 - 00:01]" in ts.get_text()

@pytest.mark.skipif(not os.path.isfile(DEFAULT_EDGE_PATH), reason="Edge headless required")
def test_render_html_to_pdf():
    html = "<html><body><h1>Test Headless Edge</h1></body></html>"
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        out_path = tmp.name
        
    try:
        res = render_html_to_pdf(html, out_path)
        assert os.path.isfile(res)
        assert os.path.getsize(res) > 1000
        with open(res, "rb") as f:
            header = f.read(5)
            assert header == b"%PDF-"
    finally:
        try:
            os.remove(out_path)
        except OSError:
            pass

@pytest.mark.skipif(not os.path.isfile(DEFAULT_EDGE_PATH), reason="Edge headless required")
def test_generate_summary_pdf():
    task = dict(SAMPLE_TASK)
    task["summary"] = SAMPLE_MARKDOWN
    pdf_bytes = generate_summary_pdf(task)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 5000
    assert pdf_bytes.startswith(b"%PDF-")

@pytest.mark.skipif(not os.path.isfile(DEFAULT_EDGE_PATH), reason="Edge headless required")
def test_generate_transcript_pdf():
    pdf_bytes = generate_transcript_pdf(SAMPLE_TASK, SAMPLE_PARAGRAPHS)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 5000
    assert pdf_bytes.startswith(b"%PDF-")
