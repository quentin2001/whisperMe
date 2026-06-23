"""
网易云音乐播客适配模块
支持从 music.163.com 提取播客音频 URL 和元数据。

URL 格式：
  - 单集: https://music.163.com/program?id={programId}
  - 频道: https://music.163.com/radio?id={radioId}
  - 新格式: https://music.163.com/podcast/{id}

API 端点（无需登录）：
  - GET /api/dj/program/detail?id={programId}  → 单集详情
  - GET /api/dj/program?rid={radioId}          → 频道节目列表
  - 重定向: /song/media/outer/url?id={songId}.mp3 → 音频文件
"""
import re
from typing import Optional
import httpx

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
BASE_URL = "https://music.163.com"


def _netease_request(path: str, params: dict = None) -> Optional[dict]:
    """发起网易云音乐 API 请求"""
    url = f"{BASE_URL}{path}"
    headers = {
        "User-Agent": UA,
        "Referer": f"{BASE_URL}/",
    }
    try:
        with httpx.Client(timeout=15.0, trust_env=True, follow_redirects=True) as client:
            resp = client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200 or "program" in data:
                    return data
                print(f"[LOG] NetEase API returned code={data.get('code')}: {data.get('message', '')}")
    except Exception as e:
        print(f"[LOG] NetEase API request failed: {e}")
    return None


def parse_netease_url(url: str) -> Optional[dict]:
    """
    解析网易云音乐播客 URL，提取 programId 或 radioId。
    Returns:
        {"type": "program"|"radio", "id": str}
    """
    # /program?id=xxx
    m = re.search(r'[?&]id=(\d+)', url)
    if '/program' in url and m:
        return {"type": "program", "id": m.group(1)}

    # /radio?id=xxx
    if '/radio' in url and m:
        return {"type": "radio", "id": m.group(1)}

    # /podcast/xxx — 新格式，可能是 radioId
    m2 = re.search(r'/podcast/(\d+)', url)
    if m2:
        return {"type": "radio", "id": m2.group(1)}

    return None


def get_program_detail(program_id: str) -> Optional[dict]:
    """获取单集详情（含音频 URL）"""
    data = _netease_request("/api/dj/program/detail", {"id": program_id})
    if not data:
        return None

    program = data.get("program")
    if not program:
        return None

    main_song = program.get("mainSong", {})
    song_id = main_song.get("id")

    # 构建音频重定向 URL
    audio_url = ""
    if song_id:
        audio_url = f"{BASE_URL}/song/media/outer/url?id={song_id}.mp3"

    # 封面
    cover = program.get("coverUrl", "")

    # 时长（毫秒 → 毫秒字符串）
    duration_ms = program.get("duration", 0)
    duration_str = ""
    if duration_ms:
        total_sec = duration_ms // 1000
        h, remainder = divmod(total_sec, 3600)
        m, s = divmod(remainder, 60)
        duration_str = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    return {
        "title": program.get("name", ""),
        "description": program.get("description", ""),
        "audio_url": audio_url,
        "duration": duration_str,
        "cover": cover,
        "radio_name": program.get("radio", {}).get("name", ""),
        "radio_id": program.get("radio", {}).get("id", ""),
        "pub_date": "",
        "song_id": song_id,
    }


def get_radio_programs(radio_id: str, limit: int = 1) -> list[dict]:
    """获取频道的节目列表"""
    data = _netease_request("/api/dj/program", {"rid": radio_id, "limit": limit, "asc": "false"})
    if not data:
        return []

    programs = data.get("programs", [])
    results = []
    for p in programs:
        main_song = p.get("mainSong", {})
        song_id = main_song.get("id")
        audio_url = f"{BASE_URL}/song/media/outer/url?id={song_id}.mp3" if song_id else ""

        duration_ms = p.get("duration", 0)
        duration_str = ""
        if duration_ms:
            total_sec = duration_ms // 1000
            h, remainder = divmod(total_sec, 3600)
            m, s = divmod(remainder, 60)
            duration_str = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

        results.append({
            "title": p.get("name", ""),
            "description": p.get("description", ""),
            "audio_url": audio_url,
            "duration": duration_str,
            "cover": p.get("coverUrl", ""),
            "radio_name": p.get("radio", {}).get("name", ""),
            "program_id": str(p.get("id", "")),
            "song_id": song_id,
        })

    return results


def resolve_netease_podcast(url: str) -> Optional[dict]:
    """
    统一入口：解析网易云音乐播客 URL，返回标准 metadata dict。
    """
    parsed = parse_netease_url(url)
    if not parsed:
        return None

    if parsed["type"] == "program":
        detail = get_program_detail(parsed["id"])
        if not detail:
            return None
        return _to_standard_metadata(detail)

    elif parsed["type"] == "radio":
        programs = get_radio_programs(parsed["id"], limit=1)
        if not programs:
            return None
        return _to_standard_metadata(programs[0])

    return None


def _to_standard_metadata(info: dict) -> dict:
    """转换为 whisperMe 标准 metadata 格式"""
    return {
        "title": info.get("title", ""),
        "podcast_name": info.get("radio_name", ""),
        "audio_url": info.get("audio_url", ""),
        "shownotes": info.get("description", ""),
        "like_count": 0,
        "comment_count": 0,
        "comments": [],
        "image_url": info.get("cover", ""),
        "source": "netease_podcast",
        "pub_date": info.get("pub_date", ""),
    }
