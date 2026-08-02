import os
import re
import json
import httpx
import subprocess
from app.core.strategies.base import DownloaderStrategy
from app.core.network_utils import safe_httpx_request
from app.config import FFMPEG_PATH

class BilibiliStrategy(DownloaderStrategy):
    def can_handle(self, url: str) -> bool:
        return "bilibili.com" in url or "b23.tv" in url

    def _resolve_bvid(self, url: str) -> str:
        """从 URL 中提取 BV 号，支持 b23.tv 短链接"""
        real_url = url
        if "b23.tv" in url:
            try:
                resp = safe_httpx_request("HEAD", url, follow_redirects=True, timeout=5.0)
                real_url = str(resp.url)
            except Exception as e:
                print(f"⚠️ [LOG] 还原 Bilibili 短链接失败: {e}")
        
        bv_match = re.search(r"(BV[a-zA-Z0-9]+)", real_url)
        if not bv_match:
            raise Exception("未能在链接中解析出 Bilibili BV 号")
        return bv_match.group(1)

    def _fetch_video_info_api(self, bvid: str) -> dict | None:
        """通过 Bilibili Web API 获取视频元数据（更稳定可靠）"""
        try:
            api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.bilibili.com/"
            }
            r = safe_httpx_request("GET", api_url, headers=headers, timeout=10.0)
            if r.status_code != 200:
                print(f"⚠️ [LOG] Bilibili API 请求失败: HTTP {r.status_code}")
                return None
            
            result = r.json()
            if result.get("code") != 0:
                print(f"⚠️ [LOG] Bilibili API 返回错误: {result.get('message', 'unknown')}")
                return None
            
            data = result.get("data", {})
            return {
                "title": data.get("title", "未知 Bilibili 视频"),
                "desc": data.get("desc", ""),
                "uploader": data.get("owner", {}).get("name", "B站UP主"),
                "pic": data.get("pic", ""),
                "aid": data.get("aid"),
                "cid": data.get("cid"),
                "like_count": data.get("stat", {}).get("like", 0),
                "comment_count": data.get("stat", {}).get("reply", 0),
            }
        except Exception as e:
            print(f"⚠️ [LOG] Bilibili API 获取视频信息失败: {e}")
            return None

    def _fetch_hot_comments(self, aid) -> list:
        """通过 Bilibili 评论 API 获取热门评论"""
        if not aid:
            return []
        try:
            api_url = f"https://api.bilibili.com/x/v2/reply/main?type=1&oid={aid}&mode=3&ps=20"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.bilibili.com/"
            }
            r = safe_httpx_request("GET", api_url, headers=headers, timeout=10.0)
            if r.status_code != 200:
                print(f"⚠️ [LOG] Bilibili 评论 API 请求失败: HTTP {r.status_code}")
                return []
            
            result = r.json()
            if result.get("code") != 0:
                print(f"⚠️ [LOG] Bilibili 评论 API 返回错误: {result.get('message', 'unknown')}")
                return []
            
            replies = result.get("data", {}).get("replies") or []
            comments = []
            for reply in replies:
                try:
                    comments.append({
                        "author": reply.get("member", {}).get("uname", "匿名用户"),
                        "content": reply.get("content", {}).get("message", ""),
                        "likes": reply.get("like", 0),
                    })
                except Exception:
                    continue
            
            comments.sort(key=lambda x: x.get("likes", 0), reverse=True)
            print(f"🟢 [LOG] 成功获取 {len(comments)} 条 Bilibili 热门评论")
            return comments[:30]
        except Exception as e:
            print(f"⚠️ [LOG] Bilibili 评论获取失败: {e}")
            return []

    def _fetch_metadata_mobile_fallback(self, bvid: str) -> dict:
        """移动端 HTML 解析 fallback（当 API 不可用时）"""
        mobile_url = f"https://m.bilibili.com/video/{bvid}"
        mobile_headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "Referer": "https://m.bilibili.com/"
        }
        
        r = safe_httpx_request("GET", mobile_url, headers=mobile_headers, timeout=15.0)
        if r.status_code != 200:
            raise Exception(f"请求 Bilibili 移动端网页失败: HTTP {r.status_code}")

        html = r.text
        state_match = re.search(r"window\.__INITIAL_STATE__\s*=\s*({.*?});", html)
        if not state_match:
            raise Exception("未能从 Bilibili 移动端网页中解析 window.__INITIAL_STATE__")

        state = json.loads(state_match.group(1))
        view_info = state.get("video", {}).get("viewInfo", {})
        return {
            "title": view_info.get("title", "未知 Bilibili 视频"),
            "desc": view_info.get("desc", ""),
            "uploader": view_info.get("owner", {}).get("name", "B站UP主"),
            "pic": view_info.get("pic", ""),
            "aid": view_info.get("aid"),
            "cid": view_info.get("cid"),
            "like_count": view_info.get("stat", {}).get("like", 0),
            "comment_count": view_info.get("stat", {}).get("reply", 0),
        }

    def parse_metadata(self, url: str) -> dict:
        bvid = self._resolve_bvid(url)
        
        # 优先使用 API 获取元数据
        info = self._fetch_video_info_api(bvid)
        if not info:
            print("🔄 [LOG] API 获取失败，回退到移动端 HTML 解析...")
            info = self._fetch_metadata_mobile_fallback(bvid)
        
        # 获取热门评论
        comments = self._fetch_hot_comments(info.get("aid"))

        return {
            "title": info["title"],
            "podcast_name": info["uploader"],
            "audio_url": url,
            "shownotes": info["desc"],
            "like_count": info.get("like_count", 0),
            "comment_count": info.get("comment_count", 0),
            "comments": comments,
            "image_url": info.get("pic", ""),
            "source": "bilibili_private"
        }

    def download_audio(self, url: str, local_path: str, progress_callback=None) -> dict:
        if os.path.exists(local_path) and os.path.getsize(local_path) > 1024*1024:
            print(f"🎯 [LOG] 检测到本地 Bilibili 音频文件已存在，跳过下载与提取: {local_path}")
            metadata = self.parse_metadata(url)
            if progress_callback:
                progress_callback(100.0)
            return metadata

        print("🎬 [LOG] 检测到 Bilibili 链接，启动私有高性能下载引擎...")
        bvid = self._resolve_bvid(url)
        
        # 优先使用 API 获取视频信息
        info = self._fetch_video_info_api(bvid)
        if info and info.get("aid") and info.get("cid"):
            aid = info["aid"]
            cid = info["cid"]
            title = info["title"]
            desc = info["desc"]
            uploader = info["uploader"]
            print(f"🟢 [LOG] 通过 API 获取视频信息成功: {title}")
        else:
            # Fallback 到移动端 HTML 解析
            print("🔄 [LOG] API 获取失败，回退到移动端 HTML 解析...")
            info = self._fetch_metadata_mobile_fallback(bvid)
            aid = info.get("aid")
            cid = info.get("cid")
            title = info["title"]
            desc = info["desc"]
            uploader = info["uploader"]
        
        if not aid or not cid:
            raise Exception("解析 Bilibili 视频 aid 或 cid 失败")
        
        playurl_api = f"https://api.bilibili.com/x/player/playurl?avid={aid}&cid={cid}&qn=16&type=&otype=json&platform=html5&high_quality=1"
        print(f"🟢 [LOG] 请求 Playurl API...")
        api_headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15",
            "Referer": f"https://www.bilibili.com/video/{bvid}/"
        }
        
        r_api = safe_httpx_request("GET", playurl_api, headers=api_headers, timeout=10.0)
        if r_api.status_code != 200:
            raise Exception(f"Playurl API 请求失败: HTTP {r_api.status_code}")

        api_data = r_api.json()
        if api_data.get("code") != 0:
            raise Exception(f"Playurl API 错误 ({api_data.get('code')}): {api_data.get('message')}")

        durl = api_data.get("data", {}).get("durl", [])
        if not durl:
            raise Exception("未找到 Bilibili 流媒体下载地址")

        play_url = durl[0].get("url")

        # Create temporary mp4 file beside local_path
        temp_mp4 = local_path.replace(".mp3", ".mp4")
        if not temp_mp4.endswith(".mp4"):
            temp_mp4 += ".mp4"
            
        print(f"🟢 [LOG] 开始下载媒体流 -> {temp_mp4}")
        stream_headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15",
            "Referer": f"https://www.bilibili.com/video/{bvid}/"
        }

        downloaded = 0
        total_bytes = durl[0].get("size", 0)

        download_stream_success = False

        try:
            with open(temp_mp4, "wb") as f:
                with httpx.Client(trust_env=True) as stream_client:
                    with stream_client.stream("GET", play_url, headers=stream_headers, timeout=30.0) as response:
                        if response.status_code != 200:
                            raise Exception(f"HTTP status code {response.status_code}")
                        for chunk in response.iter_bytes(chunk_size=16384):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback and total_bytes > 0:
                                percent = (downloaded / total_bytes) * 90.0
                                progress_callback(percent)
            download_stream_success = True
        except Exception as e_stream_proxy:
            print(f"⚠️ [LOG] Bilibili 媒体流代理下载失败: {e_stream_proxy}。尝试直连下载...")
            downloaded = 0
            if os.path.exists(temp_mp4):
                try:
                    os.remove(temp_mp4)
                except Exception:
                    pass

        if not download_stream_success:
            try:
                with open(temp_mp4, "wb") as f:
                    with httpx.Client(trust_env=False) as stream_client:
                        with stream_client.stream("GET", play_url, headers=stream_headers, timeout=30.0) as response:
                            if response.status_code != 200:
                                raise Exception(f"HTTP status code {response.status_code}")
                            for chunk in response.iter_bytes(chunk_size=16384):
                                f.write(chunk)
                                downloaded += len(chunk)
                                if progress_callback and total_bytes > 0:
                                    percent = (downloaded / total_bytes) * 90.0
                                    progress_callback(percent)
                download_stream_success = True
            except Exception as e_stream_direct:
                print(f"❌ [LOG] Bilibili 媒体流直连下载失败: {e_stream_direct}")
                if os.path.exists(temp_mp4):
                    try:
                        os.remove(temp_mp4)
                    except Exception:
                        pass
                raise e_stream_direct
                            
        print(f"🟢 [LOG] 提取音频 -> {local_path}")
        
        ffmpeg_cmd = [FFMPEG_PATH, "-y", "-i", temp_mp4, "-vn", "-acodec", "libmp3lame", "-ab", "128k", local_path]
        res = subprocess.run(ffmpeg_cmd, capture_output=True)
        
        if res.returncode != 0:
            print("⚠️ [LOG 警告] 使用指定 FFMPEG_PATH 提取失败，尝试全局 ffmpeg 兜底...")
            res_fallback = subprocess.run(["ffmpeg", "-y", "-i", temp_mp4, "-vn", "-acodec", "libmp3lame", "-ab", "128k", local_path], capture_output=True)
            if res_fallback.returncode != 0:
                if os.path.exists(temp_mp4):
                    try:
                        os.remove(temp_mp4)
                    except Exception:
                        pass
                raise Exception(f"FFmpeg 提取音频失败: {res.stderr.decode('utf-8', errors='ignore')}")
        
        if os.path.exists(temp_mp4):
            try:
                os.remove(temp_mp4)
            except Exception:
                pass
        
        # 获取热门评论
        comments = self._fetch_hot_comments(aid)
        
        metadata = {
            "title": title,
            "podcast_name": uploader,
            "audio_url": url,
            "shownotes": desc,
            "like_count": info.get("like_count", 0) if info else 0,
            "comment_count": info.get("comment_count", 0) if info else 0,
            "comments": comments,
            "image_url": info.get("pic", "") if info else "",
            "source": "bilibili_private"
        }
        
        if progress_callback:
            progress_callback(100.0)
        return metadata
