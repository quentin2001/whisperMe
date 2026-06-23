"""
荔枝FM适配模块
从 lizhi.fm 提取音频 URL 和元数据。

页面结构：音频 URL 直接嵌入在 HTML 中（cdn*.lizhi.fm/audio/...）。
注意：荔枝FM CDN (TencentEdgeOne) 会屏蔽 httpx，需用 curl 兜底。
"""
import re
import subprocess
import sys
from typing import Optional
import httpx

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


def parse_lizhi_url(url: str) -> Optional[dict]:
    """
    解析荔枝FM URL，提取 radioId 和 episodeId。
    支持格式：
      - https://www.lizhi.fm/200604875/3218046949873271302
      - https://www.lizhi.fm/radio/xxx
    """
    # /radioId/episodeId
    m = re.search(r'lizhi\.fm/(\d+)/(\d+)', url)
    if m:
        return {"radio_id": m.group(1), "episode_id": m.group(2)}

    # /radio/xxx
    m = re.search(r'lizhi\.fm/radio/(\d+)', url)
    if m:
        return {"radio_id": m.group(1), "episode_id": None}

    return None


def resolve_lizhi_podcast(url: str) -> Optional[dict]:
    """
    统一入口：解析荔枝FM URL，返回标准 metadata dict。
    通过抓取页面 HTML 提取音频 URL 和元数据。
    """
    parsed = parse_lizhi_url(url)
    if not parsed:
        return None

    # 构造标准 URL（去掉查询参数）
    clean_url = f"https://www.lizhi.fm/{parsed['radio_id']}/{parsed['episode_id'] or ''}".rstrip('/')

    headers = {"User-Agent": UA}
    html = ""

    # 1. 尝试 httpx
    try:
        with httpx.Client(timeout=15.0, trust_env=True, follow_redirects=True) as client:
            resp = client.get(clean_url, headers=headers)
            if resp.status_code == 200 and len(resp.text) > 1000:
                html = resp.text
    except Exception:
        pass

    # 2. curl 兜底（荔枝FM CDN 屏蔽 httpx 但允许 curl）
    if not html:
        try:
            cmd = [
                "curl.exe", "-s", "-L", "-o", "-",
                "-H", f"User-Agent: {UA}",
                "-H", "Accept: text/html",
                clean_url
            ]
            if sys.platform != "win32":
                cmd[0] = "curl"
            res = subprocess.run(cmd, capture_output=True, timeout=20)
            if res.returncode == 0:
                html = res.stdout.decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"[LOG] Lizhi FM curl fallback failed: {e}")

    if not html or len(html) < 1000:
        print(f"[LOG] Lizhi FM: could not fetch page")
        return None

    # 提取音频 URL — 直接从 HTML 中的 CDN 链接
    audio_urls = re.findall(r'(https?://cdn\d*\.lizhi\.fm/audio/[^"\'\\]+\.(?:mp3|m4a|aac))', html)
    if not audio_urls:
        # 降级：搜索更宽泛的音频 URL
        audio_urls = re.findall(r'(https?://[^"\'\\]*lizhi[^"\'\\]*\.(?:mp3|m4a|aac))', html)

    audio_url = ""
    if audio_urls:
        # 去重，优先选择 _hd 版本
        unique_urls = list(set(audio_urls))
        hd_urls = [u for u in unique_urls if '_hd' in u]
        audio_url = hd_urls[0] if hd_urls else unique_urls[0]
        # 清理转义字符
        audio_url = audio_url.replace('\\/', '/').replace('\\', '')

    if not audio_url:
        print(f"[LOG] No audio URL found in Lizhi FM page")
        return None

    # 提取标题
    title = ""
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html)
    if title_match:
        title = title_match.group(1).strip()
        # 清理 " - 荔枝FM" 后缀
        title = re.sub(r'\s*[-–—]\s*荔枝FM.*$', '', title)

    # 提取电台名称
    radio_name = ""
    radio_match = re.search(r'radioName["\':\s]+([^"\']+)', html)
    if radio_match:
        radio_name = radio_match.group(1)

    # 提取封面
    cover = ""
    cover_match = re.findall(r'(https?://[^\"\'\\]*lizhi[^\"\'\\]*\.(?:jpg|jpeg|png|webp))', html)
    if cover_match:
        cover = cover_match[0].replace('\\/', '/')

    # 提取描述
    description = ""
    desc_match = re.search(r'<meta[^>]*name=\"description\"[^>]*content=\"([^\"]+)\"', html)
    if desc_match:
        description = desc_match.group(1).strip()

    return {
        "title": title,
        "podcast_name": radio_name,
        "audio_url": audio_url,
        "shownotes": description,
        "like_count": 0,
        "comment_count": 0,
        "comments": [],
        "image_url": cover,
        "source": "lizhi_fm",
        "pub_date": "",
    }
