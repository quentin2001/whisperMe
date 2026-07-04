import os
import re
from app.core.strategies.base import DownloaderStrategy
from app.core.rss_parser import resolve_podcast_url
from app.core.network_utils import download_file_with_fallback

class RssStrategy(DownloaderStrategy):
    def can_handle(self, url: str) -> bool:
        rss_indicators = [
            "podcasts.apple.com",
            "itunes.apple.com",
            "pca.st",
            "pocketcasts.com",
            "overcast.fm",
        ]
        for indicator in rss_indicators:
            if indicator in url:
                return True
        rss_patterns = [r'\.xml$', r'\.rss$', r'/feed/?$', r'/rss/?$', r'feeds?\.']
        url_lower = url.lower().split('?')[0]
        for pattern in rss_patterns:
            if re.search(pattern, url_lower):
                return True
        return False

    def parse_metadata(self, url: str) -> dict:
        metadata = resolve_podcast_url(url)
        if metadata and metadata.get("audio_url"):
            return metadata
        raise Exception("RSS/Apple Podcasts 解析失败")

    def download_audio(self, url: str, local_path: str, progress_callback=None) -> dict:
        rss_metadata = self.parse_metadata(url)
        audio_url = rss_metadata["audio_url"]
        
        if os.path.exists(local_path) and os.path.getsize(local_path) > 1024*1024:
            print(f"[LOG] RSS 音频缓存命中: {local_path}")
            if progress_callback:
                progress_callback(100.0)
            return rss_metadata

        print(f"[LOG] 正在从 RSS Feed 下载音频: {audio_url}")
        download_file_with_fallback(audio_url, local_path, progress_callback)
        return rss_metadata
