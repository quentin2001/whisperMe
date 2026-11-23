import os
import re
import json
import httpx
import subprocess
from app.core.strategies.base import DownloaderStrategy
from app.core.network_utils import safe_httpx_request
from app.config import FFMPEG_PATH

class DouyinStrategy(DownloaderStrategy):
    """
    抖音超高速下载策略
    支持 douyin.com 网页链接、v.douyin.com 短链接（302重定向追踪）与 iesdouyin.com 移动端链接
    极速直接提取原生音频/视频流并在 1-2 秒内完成下载，规避风控 403 与无头浏览器开销
    """

    APP_USER_AGENT = "com.ss.android.ugc.aweme/160101 (Linux; U; Android 10; zh_CN; Pixel 3; Build/QQ3A.200805.001; Cronet/TTNetVersion:073b64ab 2021-03-24 QuicVersion:47946d2a 2020-10-14)"
    MOBILE_USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    DESKTOP_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def can_handle(self, url: str) -> bool:
        """判断是否为抖音相关链接"""
        return "douyin.com" in url or "iesdouyin.com" in url

    def _resolve_aweme_id(self, url: str) -> str:
        """
        从文本或链接中提取抖音 aweme_id (纯数字视频 ID)
        支持短链接 302 重定向解析
        """
        # 1. 尝试直接从传入的字符串中正则提取视频 ID
        direct_match = re.search(r"(?:/video/|/note/|/share/video/|modal_id=|item_ids?=)(\d+)", url)
        if direct_match:
            return direct_match.group(1)

        # 2. 如果包含 v.douyin.com 短链接，追踪 302 重定向
        shortlink_match = re.search(r"https?://v\.douyin\.com/[a-zA-Z0-9\-_]+/?", url)
        if shortlink_match:
            short_url = shortlink_match.group(0)
            try:
                headers = {
                    "User-Agent": self.MOBILE_USER_AGENT,
                    "Referer": "https://www.douyin.com/"
                }
                resp = safe_httpx_request("GET", short_url, headers=headers, follow_redirects=True, timeout=10.0)
                final_url = str(resp.url)
                redirect_match = re.search(r"(?:/video/|/note/|/share/video/|modal_id=|item_ids?=)(\d+)", final_url)
                if redirect_match:
                    return redirect_match.group(1)
            except Exception as e:
                print(f"⚠️ [LOG] 抖音短链接重定向解析失败: {e}")

        # 3. 兜底匹配任意 15~21 位的连续纯数字
        generic_match = re.search(r"\b(\d{15,21})\b", url)
        if generic_match:
            return generic_match.group(1)

        raise Exception("未能从链接中解析出抖音视频 ID")

    def _fetch_aweme_detail(self, aweme_id: str) -> dict:
        """
        通过抖音原生 Feed API 接口获取视频详情及媒体直链
        毫秒级极速响应，无需浏览器环境和验证码拦截
        """
        api_endpoints = [
            f"https://api.amemv.com/aweme/v1/feed/?aweme_id={aweme_id}",
            f"https://api3-normal-c-hl.amemv.com/aweme/v1/feed/?aweme_id={aweme_id}",
            f"https://api5-core-c-hl.amemv.com/aweme/v1/feed/?aweme_id={aweme_id}"
        ]

        headers = {
            "User-Agent": self.APP_USER_AGENT,
            "Referer": "https://www.douyin.com/"
        }

        last_error = None
        for endpoint in api_endpoints:
            try:
                r = safe_httpx_request("GET", endpoint, headers=headers, timeout=8.0)
                if r.status_code == 200:
                    data = r.json()
                    aweme_list = data.get("aweme_list") or []
                    if aweme_list:
                        return aweme_list[0]
            except Exception as e:
                last_error = e
                continue

        raise Exception(f"未能通过原生 Feed API 解析抖音视频详情: {last_error or '无可用数据'}")

    def _format_duration(self, duration_ms: int) -> str:
        """格式化毫秒为 MM:SS 或 HH:MM:SS"""
        total_seconds = max(0, duration_ms // 1000)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def parse_metadata(self, url: str) -> dict:
        """
        仅抓取并解析链接元数据而不下载音频文件
        提取标题、创作者、时长、封面图、标签等
        """
        aweme_id = self._resolve_aweme_id(url)
        print(f"🎬 [LOG] 识别到抖音视频 ID: {aweme_id}，正在获取视频元数据...")
        aweme = self._fetch_aweme_detail(aweme_id)

        title = aweme.get("desc") or aweme.get("share_info", {}).get("share_title") or f"抖音视频_{aweme_id}"
        author = aweme.get("author", {}).get("nickname", "抖音创作者")
        duration_ms = aweme.get("duration", 0)
        duration_str = self._format_duration(duration_ms)

        # 封面图提取
        cover_url = ""
        cover_candidates = (
            aweme.get("video", {}).get("cover", {}).get("url_list", []) or
            aweme.get("video", {}).get("origin_cover", {}).get("url_list", []) or
            aweme.get("video", {}).get("dynamic_cover", {}).get("url_list", [])
        )
        if cover_candidates:
            cover_url = cover_candidates[0]

        # 标签提取 (text_extra 或正文中的 #标签)
        tags = []
        for t in aweme.get("text_extra", []):
            hashtag = t.get("hashtag_name")
            if hashtag and hashtag not in tags:
                tags.append(hashtag)
        # 正则补充正文中的 #xxx
        for hash_match in re.findall(r"#([^\s#]+)", title):
            if hash_match not in tags:
                tags.append(hash_match)

        # 提取原生音频直链（优先 music 原生音频，其次 video 媒体流）
        music_urls = aweme.get("music", {}).get("play_url", {}).get("url_list", [])
        audio_url = music_urls[0] if music_urls else ""

        # 提取视频流直链作为备选
        video_urls = aweme.get("video", {}).get("play_addr", {}).get("url_list", [])
        video_url = video_urls[0] if video_urls else ""

        if not audio_url and not video_url:
            raise Exception("未能提取到抖音媒体播放直链")

        return {
            "title": title,
            "podcast_name": author,
            "audio_url": audio_url or video_url,
            "video_url": video_url,
            "shownotes": aweme.get("desc", ""),
            "duration": duration_str,
            "like_count": aweme.get("statistics", {}).get("digg_count", 0),
            "comment_count": aweme.get("statistics", {}).get("comment_count", 0),
            "comments": [],
            "image_url": cover_url,
            "tags": tags,
            "aweme_id": aweme_id,
            "source": "douyin"
        }

    def download_audio(self, url: str, local_path: str, progress_callback=None) -> dict:
        """
        执行极速音频下载逻辑并写入 local_path
        必须在 1-2 秒内完成，无浏览器开销，无 403 阻断
        """
        if os.path.exists(local_path) and os.path.getsize(local_path) > 1024 * 1024:
            print(f"🎯 [LOG] 检测到本地抖音音频已存在，跳过下载: {local_path}")
            metadata = self.parse_metadata(url)
            if progress_callback:
                progress_callback(100.0)
            return metadata

        print("⚡ [LOG] 启动抖音超高速下载引擎...")
        metadata = self.parse_metadata(url)
        audio_stream_url = metadata.get("audio_url")
        video_stream_url = metadata.get("video_url")

        download_headers = {
            "User-Agent": self.DESKTOP_USER_AGENT,
            "Referer": "https://www.douyin.com/"
        }

        # 优先使用原生单独音频流 (MP3 直链，通常仅 10-15MB，1-2秒内即可拉取完成)
        audio_downloaded = False
        if audio_stream_url and audio_stream_url.endswith(".mp3"):
            try:
                print(f"🟢 [LOG] 检测到原生音频直链，开始秒级直下 -> {local_path}")
                os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
                downloaded = 0
                with open(local_path, "wb") as f:
                    with httpx.Client(trust_env=False, follow_redirects=True, timeout=20.0) as client:
                        with client.stream("GET", audio_stream_url, headers=download_headers) as response:
                            if response.status_code == 200:
                                total_bytes = int(response.headers.get("content-length", 0))
                                for chunk in response.iter_bytes(chunk_size=65536):
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    if progress_callback and total_bytes > 0:
                                        percent = min(95.0, (downloaded / total_bytes) * 90.0)
                                        progress_callback(percent)
                                audio_downloaded = os.path.exists(local_path) and os.path.getsize(local_path) > 10240
            except Exception as e:
                print(f"⚠️ [LOG] 原生音频流直连下载异常: {e}，回退至视频流转换模式")
                if os.path.exists(local_path):
                    try:
                        os.remove(local_path)
                    except Exception:
                        pass
                audio_downloaded = False

        # 如果无原生单独音频流或下载失败，从视频媒体流下载并通过本地 ffmpeg 提取音频
        if not audio_downloaded:
            target_stream_url = video_stream_url or audio_stream_url
            if not target_stream_url:
                raise Exception("未找到有效的媒体下载直链")

            temp_mp4 = local_path.replace(".mp3", ".mp4")
            if not temp_mp4.endswith(".mp4"):
                temp_mp4 += ".mp4"

            print(f"🟢 [LOG] 开始高速拉取媒体流 -> {temp_mp4}")
            downloaded = 0
            with open(temp_mp4, "wb") as f:
                with httpx.Client(trust_env=False, follow_redirects=True, timeout=30.0) as client:
                    with client.stream("GET", target_stream_url, headers=download_headers) as response:
                        if response.status_code != 200:
                            raise Exception(f"媒体流 HTTP 请求失败: {response.status_code}")
                        total_bytes = int(response.headers.get("content-length", 0))
                        for chunk in response.iter_bytes(chunk_size=65536):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback and total_bytes > 0:
                                percent = min(80.0, (downloaded / total_bytes) * 75.0)
                                progress_callback(percent)

            print(f"🎛️ [LOG] FFmpeg 快速提取纯音频 -> {local_path}")
            ffmpeg_cmd = [FFMPEG_PATH, "-y", "-i", temp_mp4, "-vn", "-acodec", "libmp3lame", "-ab", "128k", local_path]
            res = subprocess.run(ffmpeg_cmd, capture_output=True)
            if res.returncode != 0:
                print("⚠️ [LOG 警告] 使用指定 FFMPEG_PATH 提取失败，尝试系统全局 ffmpeg 兜底...")
                res_fallback = subprocess.run(
                    ["ffmpeg", "-y", "-i", temp_mp4, "-vn", "-acodec", "libmp3lame", "-ab", "128k", local_path],
                    capture_output=True
                )
                if res_fallback.returncode != 0:
                    if os.path.exists(temp_mp4):
                        try:
                            os.remove(temp_mp4)
                        except Exception:
                            pass
                    raise Exception(f"FFmpeg 音频提取失败: {res.stderr.decode('utf-8', errors='ignore')}")

            if os.path.exists(temp_mp4):
                try:
                    os.remove(temp_mp4)
                except Exception:
                    pass

        if progress_callback:
            progress_callback(100.0)

        return metadata
