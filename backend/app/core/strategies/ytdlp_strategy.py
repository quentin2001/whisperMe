import os
import yt_dlp
from app.core.strategies.base import DownloaderStrategy
from app.config import FFMPEG_BIN_DIR, SHORT_DOWNLOADS_DIR

class YtDlpStrategy(DownloaderStrategy):
    def can_handle(self, url: str) -> bool:
        return True # Generic fallback

    def parse_metadata(self, url: str) -> dict:
        ydl_opts = {
            'ffmpeg_location': FFMPEG_BIN_DIR,
            'quiet': True,
            'nocheckcertificate': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                raise Exception("yt-dlp 无法解析此链接")
            title = info.get('title', '未知音频')
            return {
                "title": title,
                "podcast_name": info.get('uploader', '未知上传者'),
                "audio_url": url,
                "shownotes": info.get('description', ''),
                "like_count": info.get('like_count', 0),
                "comment_count": info.get('comment_count', 0),
                "comments": [],
                "image_url": info.get('thumbnail', ''),
                "source": "ytdlp"
            }

    def download_audio(self, url: str, local_path: str, progress_callback=None) -> dict:
        if os.path.exists(local_path) and os.path.getsize(local_path) > 1024*1024:
            print(f"🎯 [LOG] 检测到本地通用音频已存在，跳过 yt-dlp 下载: {local_path}")
            metadata = self.parse_metadata(url)
            if progress_callback:
                progress_callback(100.0)
            return metadata

        print("🎬 [LOG] 识别为通用媒体链接，启动 yt-dlp 抓取...")
        # yt-dlp needs an outtmpl to place the file
        # We replace the local_path extension with %(ext)s
        base_path, _ = os.path.splitext(local_path)
        safe_outtmpl = f"{base_path}.%(ext)s"
        
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
            'nocheckcertificate': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                raise Exception("yt-dlp 无法解析此链接")
            title = info.get('title', '未知音频')
            metadata = {
                "title": title,
                "podcast_name": info.get('uploader', '未知上传者'),
                "audio_url": url,
                "shownotes": info.get('description', ''),
                "like_count": info.get('like_count', 0),
                "comment_count": info.get('comment_count', 0),
                "comments": [],
                "image_url": info.get('thumbnail', ''),
                "source": "ytdlp"
            }
            
        if progress_callback:
            progress_callback(100.0)
        return metadata
