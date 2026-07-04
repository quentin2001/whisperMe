import os
import hashlib
import subprocess
from app.config import (
    FFMPEG_PATH,
    SHORT_DOWNLOADS_DIR,
    TEMP_SANDBOX_DIR,
    get_short_path_name
)
from app.core.network_utils import get_audio_duration_str

from app.core.strategies.local_strategy import LocalStrategy
from app.core.strategies.xiaoyuzhou_strategy import XiaoyuzhouStrategy
from app.core.strategies.bilibili_strategy import BilibiliStrategy
from app.core.strategies.netease_strategy import NeteaseStrategy
from app.core.strategies.ximalaya_strategy import XimalayaStrategy
from app.core.strategies.lizhi_strategy import LizhiStrategy
from app.core.strategies.rss_strategy import RssStrategy
from app.core.strategies.ytdlp_strategy import YtDlpStrategy

class PodcastDownloader:
    def __init__(self):
        # 无状态策略实例化
        self.strategies = [
            LocalStrategy(),
            XiaoyuzhouStrategy(),
            BilibiliStrategy(),
            NeteaseStrategy(),
            XimalayaStrategy(),
            LizhiStrategy(),
            RssStrategy(),
            YtDlpStrategy() # 兜底策略必须放在最后
        ]

    def _get_strategy(self, url: str):
        """寻找第一个能处理此 URL 的无状态策略"""
        for strategy in self.strategies:
            if strategy.can_handle(url):
                return strategy
        # 由于有 YtDlpStrategy 兜底，理论上不会走到这里
        raise Exception("未找到适用于该链接的下载策略")

    def parse_metadata(self, url: str) -> dict:
        """
        仅抓取并解析链接元数据而不下载音频文件
        """
        strategy = self._get_strategy(url)
        print(f"[LOG] 使用策略解析元数据: {strategy.__class__.__name__}")
        return strategy.parse_metadata(url)

    def download_url_audio(self, url: str, progress_callback=None) -> tuple[str, dict]:
        """
        下载链接音频，调用对应的策略类
        返回: (本地下载文件路径, 播客元数据字典)
        """
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        local_filename = os.path.join(SHORT_DOWNLOADS_DIR, f"{url_hash}.mp3")

        strategy = self._get_strategy(url)
        print(f"[LOG] 使用策略下载音频: {strategy.__class__.__name__}")
        
        # 针对本地文件策略，传入的其实是原始路径
        if isinstance(strategy, LocalStrategy):
            local_filename = url

        metadata = strategy.download_audio(url, local_filename, progress_callback)
        
        # 注入音频时长
        if local_filename and os.path.exists(local_filename):
            duration_str = get_audio_duration_str(local_filename)
            metadata["duration"] = duration_str
        else:
            metadata["duration"] = "00:00"

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
            print("⚠️ [LOG 警告] 使用指定 FFMPEG_PATH 预处理失败，尝试全局 ffmpeg 兜底...")
            cmd_fallback = [
                'ffmpeg', 
                '-y', 
                '-i', short_input, 
                '-ac', '1', 
                '-ar', '16000', 
                short_output
            ]
            res_fallback = subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res_fallback.returncode != 0:
                err_msg = res_fallback.stderr.decode('utf-8', errors='ignore')
                raise Exception(f"FFmpeg 音频预处理失败 (含全局兜底尝试): {err_msg}")
            
        return output_wav
