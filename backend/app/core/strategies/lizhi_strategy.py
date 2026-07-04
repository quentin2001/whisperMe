import os
from app.core.strategies.base import DownloaderStrategy
from app.core.lizhi_fm import resolve_lizhi_podcast
from app.core.network_utils import download_file_with_fallback

class LizhiStrategy(DownloaderStrategy):
    def can_handle(self, url: str) -> bool:
        return "lizhi.fm" in url or "lzfm.com" in url

    def parse_metadata(self, url: str) -> dict:
        metadata = resolve_lizhi_podcast(url)
        if metadata and metadata.get("audio_url"):
            return metadata
        raise Exception("荔枝FM解析失败")

    def download_audio(self, url: str, local_path: str, progress_callback=None) -> dict:
        lizhi_meta = self.parse_metadata(url)
        audio_url = lizhi_meta["audio_url"]
        
        if os.path.exists(local_path) and os.path.getsize(local_path) > 1024*1024:
            print(f"[LOG] 荔枝FM音频缓存命中: {local_path}")
            if progress_callback:
                progress_callback(100.0)
            return lizhi_meta

        print(f"[LOG] 正在下载荔枝FM音频: {audio_url[:80]}")
        download_file_with_fallback(audio_url, local_path, progress_callback)
        return lizhi_meta
