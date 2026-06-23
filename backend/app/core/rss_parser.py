"""
RSS Feed 解析模块
解析标准 Podcast RSS XML，提取音频 URL、标题、shownotes、作者、封面等元数据。
支持：
  - 标准 RSS 2.0 + iTunes 扩展
  - Atom 格式
  - Apple Podcasts URL → iTunes Lookup API → RSS Feed
  - Pocket Casts / Overcast 等聚合器分享链接
"""
import re
import xml.etree.ElementTree as ET
from typing import Optional
import httpx


# iTunes Lookup API
ITUNES_LOOKUP_URL = "https://itunes.apple.com/lookup"

# 常用 User-Agent
UA = "whisperMe/1.0 (Podcast Transcription Tool)"


def resolve_apple_podcast_id(url: str) -> Optional[str]:
    """
    从 Apple Podcasts URL 中提取播客 ID。
    支持格式：
      https://podcasts.apple.com/us/podcast/name/id1234567890
      https://podcasts.apple.com/podcast/name/id1234567890
      https://itunes.apple.com/us/podcast/name/id1234567890
    """
    patterns = [
        r'/id(\d+)',
        r'/podcast/[^/]+/id(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def lookup_apple_podcast(podcast_id: str) -> Optional[dict]:
    """
    调用 iTunes Lookup API 获取播客信息（包括 RSS Feed URL）。
    Returns:
        {"feedUrl": str, "trackName": str, "artistName": str, "artworkUrl100": str, ...}
    """
    try:
        with httpx.Client(timeout=15.0, trust_env=True) as client:
            resp = client.get(ITUNES_LOOKUP_URL, params={
                "id": podcast_id,
                "entity": "podcast"
            }, headers={"User-Agent": UA})
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    return results[0]
    except Exception as e:
        print(f"[LOG] iTunes Lookup failed for ID {podcast_id}: {e}")
    return None


def resolve_apple_episode_url(url: str) -> Optional[str]:
    """
    从 Apple Podcasts 单集链接中提取 RSS Feed URL。
    流程：提取播客 ID → iTunes Lookup → feedUrl
    如果 URL 包含 episode 参数 (i=xxx)，也会返回该 episode 的 guid。
    """
    podcast_id = resolve_apple_podcast_id(url)
    if not podcast_id:
        return None

    info = lookup_apple_podcast(podcast_id)
    if not info:
        return None

    feed_url = info.get("feedUrl")
    if not feed_url:
        return None

    # 提取 episode guid (i= 参数)
    episode_guid = None
    i_match = re.search(r'[?&]i=(\d+)', url)
    if i_match:
        episode_guid = i_match.group(1)

    return {
        "feed_url": feed_url,
        "podcast_name": info.get("trackName", ""),
        "author": info.get("artistName", ""),
        "image_url": info.get("artworkUrl100", "").replace("100x100", "600x600"),
        "episode_guid": episode_guid,
        "source": "apple_podcasts"
    }


def _safe_get_text(element, tag: str) -> str:
    """安全获取 XML 元素文本"""
    if element is None:
        return ""
    el = element.find(tag)
    if el is not None and el.text:
        return el.text.strip()
    return ""


def _parse_rss_item_to_episode(item, ns: dict, channel_info: dict) -> dict:
    """将单个 RSS <item> 解析为标准 episode 字典"""
    # 音频 URL — 从 <enclosure> 标签获取
    enclosure = item.find("enclosure")
    audio_url = ""
    audio_type = ""
    if enclosure is not None:
        audio_url = enclosure.get("url", "")
        audio_type = enclosure.get("type", "")

    if not audio_url:
        return None

    # 标题
    title = _safe_get_text(item, "title")

    # 描述 / shownotes — 优先 <content:encoded>（HTML），其次 <description>
    content_encoded = item.find("content:encoded")
    if content_encoded is not None and content_encoded.text:
        shownotes = content_encoded.text.strip()
    else:
        shownotes = _safe_get_text(item, "description")

    # 清理 HTML 标签为纯文本（保留结构）
    if shownotes:
        shownotes = _clean_html(shownotes)

    # 发布日期
    pub_date = _safe_get_text(item, "pubDate")

    # 时长
    itunes_duration = ""
    dur_el = item.find("itunes:duration")
    if dur_el is not None and dur_el.text:
        itunes_duration = dur_el.text.strip()

    # GUID
    guid_el = item.find("guid")
    guid = ""
    if guid_el is not None and guid_el.text:
        guid = guid_el.text.strip()

    # 单集封面
    episode_image = ""
    ep_img_el = item.find("itunes:image")
    if ep_img_el is not None:
        episode_image = ep_img_el.get("href", "")
    if not episode_image:
        episode_image = channel_info.get("image_url", "")

    return {
        "title": title,
        "audio_url": audio_url,
        "audio_type": audio_type,
        "shownotes": shownotes,
        "pub_date": pub_date,
        "duration": itunes_duration,
        "guid": guid,
        "image_url": episode_image,
        "podcast_name": channel_info.get("podcast_name", ""),
        "author": channel_info.get("author", ""),
    }


def _clean_html(html: str) -> str:
    """清理 HTML 标签，保留文本内容和基本结构"""
    if not html:
        return ""
    # 移除 script/style 标签及内容
    html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # 将 <br> <p> 转换为换行
    html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</p>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</div>', '\n', html, flags=re.IGNORECASE)
    # 移除所有其他标签
    html = re.sub(r'<[^>]+>', '', html)
    # 清理多余空白
    html = re.sub(r'\n{3,}', '\n\n', html)
    html = re.sub(r' {2,}', ' ', html)
    return html.strip()


def parse_rss_feed(feed_url: str, target_guid: str = None) -> Optional[dict]:
    """
    解析标准 Podcast RSS Feed。
    如果指定 target_guid，则只返回匹配的单集；否则返回最新一集。

    Args:
        feed_url: RSS Feed URL
        target_guid: 可选，要查找的特定 episode GUID

    Returns:
        dict: {
            "podcast_name": str,
            "author": str,
            "image_url": str,
            "description": str,
            "episode": {
                "title": str,
                "audio_url": str,
                "shownotes": str,
                "pub_date": str,
                "duration": str,
                "guid": str,
                "image_url": str,
            }
        }
    """
    # 命名空间
    ns = {
        "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
        "content": "http://purl.org/rss/1.0/modules/content/",
        "atom": "http://www.w3.org/2005/Atom",
    }

    try:
        # 下载 RSS XML
        with httpx.Client(timeout=30.0, trust_env=True, follow_redirects=True) as client:
            resp = client.get(feed_url, headers={"User-Agent": UA})
            if resp.status_code != 200:
                print(f"[LOG] RSS feed returned status {resp.status_code}: {feed_url}")
                return None
            xml_content = resp.text
    except Exception as e:
        print(f"[LOG] Failed to fetch RSS feed: {e}")
        return None

    try:
        # 注册命名空间以避免 ns0: 前缀
        for prefix, uri in ns.items():
            ET.register_namespace(prefix, uri)

        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        print(f"[LOG] RSS XML parse error: {e}")
        return None

    # 找到 <channel> — 兼容 RSS 2.0 和 Atom
    channel = root.find("channel")
    if channel is None:
        # Atom 格式：<feed> 本身就是 channel
        channel = root

    # 播客级别的元数据
    channel_info = {
        "podcast_name": _safe_get_text(channel, "title"),
        "author": "",
        "image_url": "",
        "description": _safe_get_text(channel, "description"),
    }

    # iTunes author
    author_el = channel.find("itunes:author")
    if author_el is not None and author_el.text:
        channel_info["author"] = author_el.text.strip()

    # iTunes image
    img_el = channel.find("itunes:image")
    if img_el is not None:
        channel_info["image_url"] = img_el.get("href", "")
    if not channel_info["image_url"]:
        # 标准 RSS image
        img_el2 = channel.find("image/url")
        if img_el2 is not None and img_el2.text:
            channel_info["image_url"] = img_el2.text.strip()

    # 遍历 <item> 列表
    items = channel.findall("item")
    if not items:
        print(f"[LOG] No <item> found in RSS feed")
        return None

    episodes = []
    for item in items:
        ep = _parse_rss_item_to_episode(item, ns, channel_info)
        if ep and ep.get("audio_url"):
            episodes.append(ep)

    if not episodes:
        print(f"[LOG] No episodes with audio found in RSS feed")
        return None

    # 查找目标 episode
    target_episode = None
    if target_guid:
        for ep in episodes:
            if ep.get("guid") == target_guid or target_guid in ep.get("audio_url", ""):
                target_episode = ep
                break

    # 如果没找到目标，取最新一集
    if not target_episode:
        target_episode = episodes[0]

    return {
        "podcast_name": channel_info["podcast_name"],
        "author": channel_info["author"],
        "image_url": target_episode.get("image_url") or channel_info["image_url"],
        "description": channel_info["description"],
        "episode": target_episode
    }


def resolve_podcast_url(url: str) -> Optional[dict]:
    """
    统一入口：根据 URL 类型自动解析为标准播客元数据。
    支持：
      - Apple Podcasts 链接
      - 直接 RSS Feed URL
      - Pocket Casts / Overcast 等聚合器链接

    Returns:
        dict: {
            "title": str,
            "podcast_name": str,
            "audio_url": str,
            "shownotes": str,
            "like_count": int,
            "comment_count": int,
            "comments": list,
            "image_url": str,
            "source": str,
            "pub_date": str,
        }
    """
    result = None

    # 1. Apple Podcasts
    if "podcasts.apple.com" in url or "itunes.apple.com" in url:
        apple_info = resolve_apple_episode_url(url)
        if apple_info and apple_info.get("feed_url"):
            result = parse_rss_feed(
                apple_info["feed_url"],
                target_guid=apple_info.get("episode_guid")
            )
            if result:
                result["source"] = "apple_podcasts"

    # 2. Pocket Casts (分享链接含 RSS 信息)
    elif "pca.st" in url or "pocketcasts.com" in url:
        # Pocket Casts 分享链接会重定向到 RSS 或播客页面
        try:
            with httpx.Client(timeout=15.0, trust_env=True, follow_redirects=True) as client:
                resp = client.get(url, headers={"User-Agent": UA})
                # 检查是否重定向到 RSS
                final_url = str(resp.url)
                if resp.headers.get("content-type", "").startswith("application/rss"):
                    result = parse_rss_feed(final_url)
                elif "podcasts.apple.com" in final_url:
                    # 重定向到 Apple Podcasts
                    apple_info = resolve_apple_episode_url(final_url)
                    if apple_info and apple_info.get("feed_url"):
                        result = parse_rss_feed(apple_info["feed_url"])
                else:
                    # 尝试在页面中查找 RSS 链接
                    rss_match = re.search(r'href="(https?://[^"]+/feed[^"]*)"', resp.text)
                    if rss_match:
                        result = parse_rss_feed(rss_match.group(1))
        except Exception as e:
            print(f"[LOG] Pocket Casts resolution failed: {e}")

    # 3. Overcast
    elif "overcast.fm" in url:
        try:
            with httpx.Client(timeout=15.0, trust_env=True, follow_redirects=True) as client:
                resp = client.get(url, headers={"User-Agent": UA})
                # Overcast 页面包含 iTunes 链接
                apple_match = re.search(r'podcasts\.apple\.com/[^"]+/id(\d+)', resp.text)
                if apple_match:
                    podcast_id = apple_match.group(1)
                    info = lookup_apple_podcast(podcast_id)
                    if info and info.get("feedUrl"):
                        result = parse_rss_feed(info["feedUrl"])
        except Exception as e:
            print(f"[LOG] Overcast resolution failed: {e}")

    # 4. 直接 RSS Feed URL (以 .xml, .rss, /feed 结尾，或 content-type 为 RSS)
    elif _looks_like_rss_url(url):
        result = parse_rss_feed(url)

    # 5. 尝试作为 RSS Feed 处理（某些 URL 可能直接返回 RSS XML）
    if result is None:
        try:
            with httpx.Client(timeout=10.0, trust_env=True, follow_redirects=True) as client:
                resp = client.head(url, headers={"User-Agent": UA})
                ct = resp.headers.get("content-type", "")
                if "rss" in ct or "xml" in ct or "atom" in ct:
                    result = parse_rss_feed(url)
        except Exception:
            pass

    if result is None:
        return None

    # 构建标准 metadata dict
    episode = result.get("episode", {})
    return {
        "title": episode.get("title", result.get("podcast_name", "")),
        "podcast_name": result.get("podcast_name", ""),
        "audio_url": episode.get("audio_url", ""),
        "shownotes": episode.get("shownotes", result.get("description", "")),
        "like_count": 0,
        "comment_count": 0,
        "comments": [],
        "image_url": result.get("image_url", ""),
        "source": result.get("source", "rss"),
        "pub_date": episode.get("pub_date", ""),
    }


def _looks_like_rss_url(url: str) -> bool:
    """判断 URL 是否可能是 RSS Feed"""
    rss_patterns = [
        r'\.xml$',
        r'\.rss$',
        r'/feed/?$',
        r'/rss/?$',
        r'/podcast\.xml',
        r'feeds?\.',
        r'rssfeeds\.',
    ]
    url_lower = url.lower().split('?')[0]
    return any(re.search(p, url_lower) for p in rss_patterns)
