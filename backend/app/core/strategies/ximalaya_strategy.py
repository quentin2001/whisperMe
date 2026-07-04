import os
from app.core.strategies.base import DownloaderStrategy
from app.core.ximalaya import resolve_ximalaya_podcast
from app.core.network_utils import download_file_with_fallback

class XimalayaStrategy(DownloaderStrategy):
    def can_handle(self, url: str) -> bool:
        return "ximalaya.com" in url or "xima.tv" in url

    def parse_metadata(self, url: str) -> dict:
        metadata = resolve_ximalaya_podcast(url)
        if metadata and metadata.get("audio_url"):
            return metadata
        raise Exception("喜马拉雅解析失败")

    def download_audio(self, url: str, local_path: str, progress_callback=None) -> dict:
        ximalaya_meta = self.parse_metadata(url)
        audio_url = ximalaya_meta["audio_url"]
        
        if os.path.exists(local_path) and os.path.getsize(local_path) > 1024*1024:
            print(f"[LOG] 喜马拉雅音频缓存命中: {local_path}")
            if progress_callback:
                progress_callback(100.0)
            return ximalaya_meta

        print(f"[LOG] 正在下载喜马拉雅音频: {audio_url[:80]}")
        download_file_with_fallback(audio_url, local_path, progress_callback)
        return ximalaya_meta
