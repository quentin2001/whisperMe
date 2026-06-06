import os
import re
import json
import hashlib
import subprocess
import httpx
from bs4 import BeautifulSoup
import yt_dlp
from app.config import (
    FFMPEG_PATH, 
    FFMPEG_BIN_DIR, 
    SHORT_DOWNLOADS_DIR, 
    TEMP_SANDBOX_DIR
)

# 递归在嵌套字典/列表中搜索特定键
def find_nested_key(data, target_key):
    if isinstance(data, dict):
        if target_key in data:
            return data[target_key]
        for k, v in data.items():
            res = find_nested_key(v, target_key)
            if res is not None:
                return res
    elif isinstance(data, list):
        for item in data:
            res = find_nested_key(item, target_key)
            if res is not None:
                return res
    return None

# 深度搜索特定路径下的数据，获取小宇宙评论
def extract_xiaoyuzhou_comments(data):
    comments_list = []
    seen = set()
    
    def dfs_search(obj):
        if isinstance(obj, dict):
            if "text" in obj and ("author" in obj or "user" in obj):
                author = obj.get("author", {}).get("nickname", "听友") if isinstance(obj.get("author"), dict) else "听友"
                text = obj.get("text", "")
                likes = obj.get("likeCount", 0)
                if text:
                    key = (author, text)
                    if key not in seen:
                        seen.add(key)
                        comments_list.append({
                            "author": author,
                            "content": text,
                            "likes": likes
                        })
            for k, v in obj.items():
                if k == "replyToComment":
                    continue
                dfs_search(v)
        elif isinstance(obj, list):
            for item in obj:
                dfs_search(item)

    dfs_search(data)
    # 按点赞数降序排序
    comments_list.sort(key=lambda x: x.get("likes", 0), reverse=True)
    return comments_list

class PodcastDownloader:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def parse_xiaoyuzhou(self, url: str) -> dict:
        """
        抓取并解析小宇宙播客单集页面
        """
        # 使用 curl.exe 绕过 Cloudflare TLS 校验与代理拦截，确保 100% 成功抓取 HTML
        print(f"📡 [LOG] 正在使用 curl.exe 绕过 Cloudflare 抓取小宇宙页面: {url}")
        res = subprocess.run(["curl.exe", "-k", "-s", url], capture_output=True, text=True, encoding="utf-8")
        if res.returncode != 0:
            raise Exception(f"curl.exe 抓取页面失败，返回码: {res.returncode}")
        
        html = res.stdout
        soup = BeautifulSoup(html, 'html.parser')
        next_data_tag = soup.find('script', id='__NEXT_DATA__')
        if not next_data_tag:
            raise Exception("无法在页面中找到 __NEXT_DATA__ 数据标签")
        
        data = json.loads(next_data_tag.string)
        
        # 使用递归方法弹性搜索核心字段，防止 NextJS props 结构变动
        episode_data = find_nested_key(data, "episode")
        
        if not episode_data:
            # 备用方案：在整个 JSON 中搜索音频地址和标题
            audio_url = find_nested_key(data, "audioUrl")
            if not audio_url:
                enclosure = find_nested_key(data, "enclosure")
                if isinstance(enclosure, dict):
                    audio_url = enclosure.get("url")
            title = find_nested_key(data, "title") or "未命名播客"
            shownotes = find_nested_key(data, "shownotes") or find_nested_key(data, "description") or ""
            podcast_name = "未知播客"
            podcast_data = find_nested_key(data, "podcast")
            if podcast_data and "title" in podcast_data:
                podcast_name = podcast_data["title"]
            like_count = find_nested_key(data, "likeCount") or 0
            comment_count = find_nested_key(data, "commentCount") or 0
        else:
            audio_url = episode_data.get("audioUrl")
            if not audio_url and "enclosure" in episode_data:
                enclosure = episode_data.get("enclosure")
                if isinstance(enclosure, dict):
                    audio_url = enclosure.get("url")
            if not audio_url and "media" in episode_data:
                media = episode_data.get("media")
                if isinstance(media, dict):
                    audio_url = media.get("source", {}).get("url")
                    
            title = episode_data.get("title", "未命名播客")
            shownotes = episode_data.get("shownotes") or episode_data.get("description") or ""
            podcast_name = episode_data.get("podcast", {}).get("title", "未知播客")
            like_count = episode_data.get("likeCount", 0)
            comment_count = episode_data.get("commentCount", 0)

        if not audio_url:
            raise Exception("解析失败，未能在网页中找到音频下载直链")

        # 抓取评论列表
        comments = extract_xiaoyuzhou_comments(data)

        # 获取 Shownotes 中的文本（去除 HTML 标签）
        clean_shownotes = BeautifulSoup(shownotes, "html.parser").get_text(separator="\n") if shownotes else ""

        return {
            "title": title,
            "podcast_name": podcast_name,
            "audio_url": audio_url,
            "shownotes": clean_shownotes,
            "like_count": like_count,
            "comment_count": comment_count,
            "comments": comments[:30],  # 取前 30 条热门评论进行情感/含金量分析
            "source": "xiaoyuzhou"
        }

    def download_url_audio(self, url: str, progress_callback=None) -> tuple[str, dict]:
        """
        下载链接音频，支持本地路径绕过、小宇宙解析和 yt-dlp 兜底
        返回: (本地下载文件路径, 播客元数据字典)
        """
        # 1. 物理安全护城河：如果是本地已存在的音频文件，直接豁免网络请求，秒级导入
        if os.path.exists(url) and os.path.isfile(url):
            print(f"📁 [LOG] 识别为本地文件路径，跳过网络请求直接导入: {url}")
            filename = os.path.basename(url)
            name_without_ext = os.path.splitext(filename)[0]
            metadata = {
                "title": name_without_ext,
                "podcast_name": "本地导入",
                "audio_url": url,
                "shownotes": "本地导入的音频文件，完全离线处理。",
                "like_count": 0,
                "comment_count": 0,
                "comments": [],
                "source": "local"
            }
            return url, metadata

        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        
        # 判断是否为小宇宙链接
        if "xiaoyuzhoufm.com" in url:
            print("🎙️ [LOG] 识别为小宇宙链接，启动专有轻量级解析引擎...")
            metadata = self.parse_xiaoyuzhou(url)
            audio_url = metadata["audio_url"]
            file_ext = "mp3"
            
            # 如果音频链接有具体的后缀，进行截取
            match_ext = re.search(r'\.(\w+)(?:\?|$)', audio_url)
            if match_ext:
                file_ext = match_ext.group(1)
                
            local_filename = os.path.join(SHORT_DOWNLOADS_DIR, f"{url_hash}.{file_ext}")
            
            # 优先使用 Python httpx (禁用代理) 进行流式高速下载，实时回传进度以优化用户界面体验
            print(f"📡 [LOG] 正在从直链直连下载音频 (httpx): {audio_url} -> {local_filename}")
            try:
                with httpx.Client(headers=self.headers, verify=False, trust_env=False, timeout=120.0) as client:
                    with client.stream("GET", audio_url) as r:
                        if r.status_code != 200:
                            raise Exception(f"HTTP status code {r.status_code}")
                        total_bytes = int(r.headers.get("content-length", 0))
                        downloaded_bytes = 0
                        with open(local_filename, "wb") as f:
                            for chunk in r.iter_bytes(chunk_size=1024*1024):
                                f.write(chunk)
                                downloaded_bytes += len(chunk)
                                if progress_callback and total_bytes > 0:
                                    percent = (downloaded_bytes / total_bytes) * 100.0
                                    progress_callback(percent)
                print(f"🟢 [LOG] 音频下载完成 (httpx) -> {local_filename}")
            except Exception as e:
                print(f"⚠️ [LOG 警告] httpx 下载失败: {e}，正在切换为 curl.exe 进行兜底下载...")
                # 物理清除可能损坏的未完成文件
                if os.path.exists(local_filename):
                    try:
                        os.remove(local_filename)
                    except Exception:
                        pass
                # 兜底使用 curl.exe
                res = subprocess.run(["curl.exe", "--noproxy", "*", "-k", "-L", "-s", "-o", local_filename, audio_url], capture_output=True)
                if res.returncode != 0:
                    raise Exception(f"curl.exe 下载音频失败，返回码: {res.returncode}")
            
            if progress_callback:
                progress_callback(100.0)
            return local_filename, metadata
        else:
            # 使用 yt-dlp 下载通用播客（如 Bilibili、YouTube 等）
            print("🎬 [LOG] 识别为通用媒体链接，启动 yt-dlp 抓取...")
            safe_outtmpl = os.path.join(SHORT_DOWNLOADS_DIR, f"{url_hash}.%(ext)s")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': safe_outtmpl,
                'ffmpeg_location': FFMPEG_BIN_DIR,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '128',
                }],
                'quiet': True,
                'nocheckcertificate': True,  # 忽略 SSL 证书校验
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', '未知音频')
                metadata = {
                    "title": title,
                    "podcast_name": info.get('uploader', '未知上传者'),
                    "audio_url": url,
                    "shownotes": info.get('description', ''),
                    "like_count": info.get('like_count', 0),
                    "comment_count": info.get('comment_count', 0),
                    "comments": [],
                    "source": "ytdlp"
                }
                
            local_filename = os.path.join(SHORT_DOWNLOADS_DIR, f"{url_hash}.mp3")
            return local_filename, metadata

    def preprocess_audio(self, input_path: str) -> str:
        """
        使用 FFmpeg 将音频文件标准化为单声道、16kHz WAV 格式
        这是 Whisper & PyAnnote 声纹的最优输入格式
        """
        filename = os.path.basename(input_path)
        name_without_ext = os.path.splitext(filename)[0]
        output_wav = os.path.join(TEMP_SANDBOX_DIR, f"{name_without_ext}_standardized.wav")
        
        # 统一转成 8.3 格式
        from app.config import get_short_path_name
        short_input = get_short_path_name(input_path)
        short_output = get_short_path_name(output_wav)
        
        print(f"🎛️ [LOG] 本地 FFmpeg 启动预处理 -> {short_output}")
        # -ac 1 (单声道), -ar 16000 (16000Hz 采样率)
        cmd = [
            FFMPEG_PATH, 
            '-y', 
            '-i', short_input, 
            '-ac', '1', 
            '-ar', '16000', 
            short_output
        ]
        
        # 运行 FFmpeg 并隐藏输出
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            err_msg = res.stderr.decode('utf-8', errors='ignore')
            raise Exception(f"FFmpeg 音频预处理失败: {err_msg}")
            
        return output_wav
