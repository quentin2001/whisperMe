from abc import ABC, abstractmethod

class DownloaderStrategy(ABC):
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """判断该策略是否适用于此链接"""
        pass

    @abstractmethod
    def parse_metadata(self, url: str) -> dict:
        """仅解析播客/视频的元数据，不下载音频"""
        pass

    @abstractmethod
    def download_audio(self, url: str, local_path: str, progress_callback=None) -> dict:
        """
        执行下载逻辑并写入 local_path
        返回 metadata
        """
        pass
