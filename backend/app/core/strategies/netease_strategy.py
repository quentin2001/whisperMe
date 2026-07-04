import os
from app.core.strategies.base import DownloaderStrategy
from app.core.netease_podcast import resolve_netease_podcast
from app.core.network_utils import download_file_with_fallback

class NeteaseStrategy(DownloaderStrategy):
    def can_handle(self, url: str) -> bool:
        return "music.163.com" in url and ("/program" in url or "/radio" in url or "/podcast" in url)

    def parse_metadata(self, url: str) -> dict:
        metadata = resolve_netease_podcast(url)
        if metadata and metadata.get("audio_url"):
            return metadata
        raise Exception("网易云音乐解析失败")

    def download_audio(self, url: str, local_path: str, progress_callback=None) -> dict:
        netease_meta = self.parse_metadata(url)
        audio_url = netease_meta["audio_url"]
        
        if os.path.exists(local_path) and os.path.getsize(local_path) > 1024*1024:
            print(f"[LOG] 网易云音乐音频缓存命中: {local_path}")
            if progress_callback:
                progress_callback(100.0)
            return netease_meta

        print(f"[LOG] 正在下载网易云音乐音频: {audio_url}")
        download_file_with_fallback(audio_url, local_path, progress_callback)
        return netease_meta
