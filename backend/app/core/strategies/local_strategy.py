import os
from app.core.strategies.base import DownloaderStrategy

class LocalStrategy(DownloaderStrategy):
    def can_handle(self, url: str) -> bool:
        return os.path.exists(url) and os.path.isfile(url)

    def parse_metadata(self, url: str) -> dict:
        filename = os.path.basename(url)
        name_without_ext = os.path.splitext(filename)[0]
        return {
            "title": name_without_ext,
            "podcast_name": "本地导入",
            "audio_url": url,
            "shownotes": "本地导入的音频文件，完全离线处理。",
            "like_count": 0,
            "comment_count": 0,
            "comments": [],
            "source": "local"
        }

    def download_audio(self, url: str, local_path: str, progress_callback=None) -> dict:
        print(f"📁 [LOG] 识别为本地文件路径，跳过网络请求直接导入: {url}")
        # The calling code expects to use `url` directly instead of copying, 
        # or we just let it use the original path by bypassing local_path.
        # But we need to return the new 'local_path' which is essentially `url`.
        # However, interface returns dict metadata, and the outer downloader 
        # is responsible for returning (path, meta).
        
        # We can just return the metadata, and outer will return (url, meta)
        # We will adjust outer downloader logic to check if source == 'local'
        if progress_callback:
            progress_callback(100.0)
        return self.parse_metadata(url)
