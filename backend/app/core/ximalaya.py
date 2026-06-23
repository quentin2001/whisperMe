"""
喜马拉雅适配模块
从 ximalaya.com / xima.tv 提取音频 URL 和元数据。

API:
  - GET /mobile/track/detail?trackId={id}  → 完整单集信息 + 多种音频 URL
  - GET /revision/track/simple?trackId={id} → 基本信息（无音频 URL，但有标题/时长）
"""
import re
from typing import Optional
import httpx

UA = "ting_v10.0.0_c10 (iPhone; iOS 16.0; Scale/3.00)"
UA_WEB = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


def resolve_ximalaya_url(url: str) -> Optional[str]:
    """
    解析喜马拉雅 URL，提取 trackId。
    支持:
      - https://xima.tv/1_zw5Z5B  (短链，需跟踪重定向)
      - https://www.ximalaya.com/sound/991419824
      - https://m.ximalaya.com/gatekeeper/podcast-share/sound/991419824?...
    """
    # 短链 → 跟踪重定向
    if "xima.tv" in url:
        try:
            with httpx.Client(timeout=15.0, trust_env=True, follow_redirects=True) as client:
                resp = client.get(url, headers={"User-Agent": UA_WEB})
                final_url = str(resp.url)
                # 从重定向后的 URL 提取 sound ID
                m = re.search(r'/sound/(\d+)', final_url)
                if m:
                    return m.group(1)
        except Exception as e:
            print(f"[LOG] Ximalaya short link redirect failed: {e}")
        return None

    # 标准 URL → 直接提取
    m = re.search(r'/sound/(\d+)', url)
    if m:
        return m.group(1)

    # trackId 参数
    m = re.search(r'[?&]trackId=(\d+)', url)
    if m:
        return m.group(1)

    # /track/xxx
    m = re.search(r'/track/(\d+)', url)
    if m:
        return m.group(1)

    return None


def get_ximalaya_track_detail(track_id: str) -> Optional[dict]:
    """调用移动端 API 获取完整单集信息"""
    url = f"https://mobile.ximalaya.com/mobile/track/detail"
    params = {"trackId": track_id}
    headers = {"User-Agent": UA}

    try:
        with httpx.Client(timeout=15.0, trust_env=True, follow_redirects=True) as client:
            resp = client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        print(f"[LOG] Ximalaya mobile API failed: {e}")

    # 降级到桌面端 API
    try:
        with httpx.Client(timeout=15.0, trust_env=True, follow_redirects=True) as client:
            resp = client.get(
                "https://www.ximalaya.com/revision/track/simple",
                params={"trackId": track_id},
                headers={"User-Agent": UA_WEB}
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                return data.get("trackInfo", {})
    except Exception as e:
        print(f"[LOG] Ximalaya desktop API failed: {e}")

    return None


def resolve_ximalaya_podcast(url: str) -> Optional[dict]:
    """
    统一入口：解析喜马拉雅 URL，返回标准 metadata dict。
    """
    track_id = resolve_ximalaya_url(url)
    if not track_id:
        print(f"[LOG] Could not extract trackId from: {url}")
        return None

    data = get_ximalaya_track_detail(track_id)
    if not data:
        return None

    # 选择最佳音频 URL（优先 MP3 64k，其次 AAC 224k，最后下载链接）
    audio_url = (
        data.get("playUrl64")
        or data.get("playUrl32")
        or data.get("playPathAacv224")
        or data.get("playPathAacv164")
        or data.get("downloadUrl")
        or data.get("downloadAacUrl")
        or ""
    )

    if not audio_url:
        print(f"[LOG] No audio URL found in Ximalaya response for track {track_id}")
        return None

    # 时长（秒 → HH:MM:SS）
    duration_sec = data.get("duration", 0)
    duration_str = ""
    if duration_sec:
        h, remainder = divmod(int(duration_sec), 3600)
        m, s = divmod(remainder, 60)
        duration_str = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    return {
        "title": data.get("title", ""),
        "podcast_name": data.get("albumTitle", ""),
        "audio_url": audio_url,
        "shownotes": data.get("intro", "") or data.get("shortRichIntro", ""),
        "like_count": data.get("likes", 0),
        "comment_count": data.get("comments", 0),
        "comments": [],
        "image_url": data.get("coverLarge") or data.get("coverMiddle") or data.get("coverSmall") or data.get("albumImage", ""),
        "source": "ximalaya",
        "pub_date": data.get("createdAt", ""),
    }
