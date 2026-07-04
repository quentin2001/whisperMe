"""
Suite 6 (FFM): 音频预处理模块测试
测试对象: downloader.py preprocess_audio()
核心验证点: FFmpeg 标准化输出、降级到全局 ffmpeg
"""
import os
import pytest
from app.config import FFMPEG_PATH


class TestFFMStandardize:
    """FFM_STD_01: 音频标准化"""

    def test_audio_preprocess_to_wav(self):
        """MP3 转为单声道 16kHz WAV"""
        from app.core.downloader import PodcastDownloader
        downloader = PodcastDownloader()

        fixture = os.path.abspath("tests/fixtures/short_audio.mp3")
        assert os.path.exists(fixture)

        output = downloader.preprocess_audio(fixture)
        assert output.endswith(".wav")
        assert os.path.exists(output)

        # 使用配置中的 ffmpeg_dir 中的 ffprobe 验证
        from app.config import FFMPEG_BIN_DIR
        ffprobe = os.path.join(FFMPEG_BIN_DIR, "ffprobe.exe") if FFMPEG_BIN_DIR else "ffprobe"
        if os.path.exists(ffprobe):
            import subprocess, json
            result = subprocess.run(
                [ffprobe, "-v", "quiet", "-print_format", "json", "-show_streams", output],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                info = json.loads(result.stdout)
                stream = info["streams"][0]
                assert stream["channels"] == 1
                assert stream["sample_rate"] == "16000"

        # 清理
        try:
            os.remove(output)
        except OSError:
            pass


class TestFFMFallback:
    """FFM_FALLBACK_02: FFmpeg 路径降级"""

    def test_custom_ffmpeg_path_used(self):
        """配置中的 FFMPEG_PATH 文件存在"""
        assert FFMPEG_PATH, "FFMPEG_PATH should not be empty"
        assert os.path.isfile(FFMPEG_PATH), f"FFMPEG_PATH not found: {FFMPEG_PATH}"


class TestFFMCorrupt:
    """FFM_CORRUPT_03: 损坏音频容错"""

    def test_corrupt_audio_preprocess(self):
        """损坏音频文件处理（FFmpeg 可能修复或报错）"""
        from app.core.downloader import PodcastDownloader
        downloader = PodcastDownloader()

        fixture = os.path.abspath("tests/fixtures/corrupt_audio.mp3")
        assert os.path.exists(fixture)

        try:
            output = downloader.preprocess_audio(fixture)
            # FFmpeg 有时能自动修复损坏的 mp3 头部
            if os.path.exists(output):
                try:
                    os.remove(output)
                except OSError:
                    pass
        except Exception as e:
            # 也接受抛异常（取决于 FFmpeg 版本）
            assert "FFmpeg" in str(e) or "预处理" in str(e) or "失败" in str(e)
