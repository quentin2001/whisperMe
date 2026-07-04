"""
ASR Provider 抽象基类
所有在线 ASR 引擎必须继承此基类并实现 transcribe() 方法。
统一输出格式: list[dict]，每个 dict 包含 {"start": float, "end": float, "text": str}
"""
import os
import re
import subprocess
import math
import base64
from abc import ABC, abstractmethod
from app.config import get_short_path_name, FFMPEG_PATH


class ASRProvider(ABC):
    """在线 ASR Provider 抽象基类"""

    @abstractmethod
    def transcribe(self, wav_path: str, diarization_segments: list[dict],
                   progress_callback=None) -> list[dict]:
        """
        转录音频文件，返回标准格式的转录段落列表。

        Args:
            wav_path: 标准化后的 WAV 音频文件路径
            diarization_segments: pyannote 声纹分割结果 [{"start", "end", "speaker"}, ...]
            progress_callback: 进度回调函数 callback(progress: float)，范围 60.0~75.0

        Returns:
            list[dict]: [{"start": float, "end": float, "text": str}, ...]
        """
        pass

    @abstractmethod
    def get_display_name(self) -> str:
        """返回 Provider 的显示名称，用于前端 UI 展示"""
        pass

    @property
    def supports_native_timestamps(self) -> bool:
        """
        是否原生支持精确到段落/词的时间戳。
        如果为 True 且声纹关闭，流水线将跳过 WAV 预处理，直接分片上传。
        """
        return False

    # ==================== 共享工具方法 ====================

    @staticmethod
    def get_audio_duration(audio_path: str) -> float:
        """读取音频文件总时长（秒），支持 WAV/MP3/AAC 等所有 ffmpeg 兼容格式"""
        # 用 ffmpeg -i 获取时长（输出到 stderr，解析 Duration 行）
        import re as _re
        from app.config import FFMPEG_PATH as _FFMPEG_PATH
        for ffmpeg_cmd in [_FFMPEG_PATH, "ffmpeg", "ffmpeg.exe"]:
            if not ffmpeg_cmd:
                continue
            try:
                cmd = [ffmpeg_cmd, "-i", audio_path]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     creationflags=subprocess.CREATE_NO_WINDOW,
                                     timeout=15)
                stderr = res.stderr.decode("utf-8", errors="ignore")
                match = _re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", stderr)
                if match:
                    h, m, s = float(match.group(1)), float(match.group(2)), float(match.group(3))
                    duration = h * 3600 + m * 60 + s
                    if duration > 0:
                        return duration
            except Exception:
                continue

        # 回退到 Python wave 模块（仅 WAV）
        import wave
        try:
            with wave.open(audio_path, "rb") as w:
                return w.getnframes() / float(w.getframerate())
        except Exception as e:
            print(f"⚠️ [LOG] 读取音频时长失败: {e}")
            return 1.0

    @staticmethod
    def extract_chunk_as_mp3(wav_path: str, start_offset: float, duration: float,
                             chunk_index: int) -> str:
        """从 WAV 中提取指定区间的 MP3 分片，返回分片文件路径"""
        short_wav_path = get_short_path_name(os.path.abspath(wav_path))
        base_name = os.path.splitext(wav_path)[0]
        chunk_mp3_path = f"{base_name}_chunk_{chunk_index}.mp3"
        short_chunk_path = get_short_path_name(chunk_mp3_path)

        for ffmpeg_cmd in [FFMPEG_PATH, "ffmpeg"]:
            cmd = [
                ffmpeg_cmd, "-y",
                "-i", short_wav_path,
                "-ss", str(start_offset),
                "-t", str(duration),
                "-codec:a", "libmp3lame",
                "-b:a", "32k",
                "-ac", "1",
                short_chunk_path
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res.returncode == 0 and os.path.exists(chunk_mp3_path):
                return chunk_mp3_path

        raise Exception(f"FFmpeg 分片提取失败 (chunk {chunk_index})")

    @staticmethod
    def extract_chunk_as_wav(wav_path: str, start_offset: float, duration: float,
                             chunk_index: int) -> str:
        """从 WAV 中提取指定区间的 WAV 分片，返回分片文件路径"""
        short_wav_path = get_short_path_name(os.path.abspath(wav_path))
        base_name = os.path.splitext(wav_path)[0]
        chunk_wav_path = f"{base_name}_chunk_{chunk_index}.wav"
        short_chunk_path = get_short_path_name(chunk_wav_path)

        for ffmpeg_cmd in [FFMPEG_PATH, "ffmpeg"]:
            cmd = [
                ffmpeg_cmd, "-y",
                "-i", short_wav_path,
                "-ss", str(start_offset),
                "-t", str(duration),
                "-ac", "1",
                "-ar", "16000",
                short_chunk_path
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res.returncode == 0 and os.path.exists(chunk_wav_path):
                return chunk_wav_path

        raise Exception(f"FFmpeg WAV 分片提取失败 (chunk {chunk_index})")

    @staticmethod
    def audio_file_to_base64(file_path: str) -> str:
        """读取音频文件并返回 base64 编码字符串（含 data URI 前缀）"""
        ext = os.path.splitext(file_path)[1].lower()
        mime = "audio/mp3" if ext == ".mp3" else "audio/wav"
        with open(file_path, "rb") as f:
            return f"data:{mime};base64," + base64.b64encode(f.read()).decode("utf-8")

    @staticmethod
    def split_text_to_sentences(text: str) -> list[str]:
        """将文本按中英文句号、问号、叹号、分号切割为句子列表，保留标点"""
        raw = re.split(r'([。？！；\n])', text)
        sentences = []
        current = ""
        for item in raw:
            if not item:
                continue
            if item in ["。", "？", "！", "；", "\n"]:
                if current:
                    sentences.append(current + (item if item != "\n" else ""))
                    current = ""
            else:
                current += item
        if current:
            sentences.append(current)
        return [s.strip() for s in sentences if s.strip()]

    @staticmethod
    def deduplicate_sentences(sentences: list[str]) -> list[str]:
        """过滤相邻重复句（防范 ASR 幻觉循环），保留标点差异"""
        def clean(text):
            return re.sub(r'[^\w\s]', '', text).strip()

        result = []
        for s in sentences:
            if not result:
                result.append(s)
            elif clean(s) != clean(result[-1]):
                result.append(s)
        return result

    @staticmethod
    def map_sentences_to_timestamps(sentences: list[str], diarization_segments: list[dict],
                                     chunk_start: float, chunk_end: float) -> list[dict]:
        """
        将无时间戳的句子列表按字符比例映射到物理时间轴（基于 VAD 活跃区间）。
        适用于不返回精确时间戳的 ASR 引擎（如 MiMo）。
        """
        if not sentences:
            return []

        # 提取当前分片范围内的活跃说话段
        active_segs = []
        for d in diarization_segments:
            s_max = max(d["start"], chunk_start)
            e_min = min(d["end"], chunk_end)
            if e_min > s_max + 0.1:
                active_segs.append((s_max, e_min))

        # 合并紧邻段（间隔 < 0.5s）
        active_segs.sort()
        merged = []
        for seg in active_segs:
            if not merged:
                merged.append(seg)
            else:
                last_s, last_e = merged[-1]
                if seg[0] - last_e < 0.5:
                    merged[-1] = (last_s, max(last_e, seg[1]))
                else:
                    merged.append(seg)

        if not merged:
            merged = [(chunk_start, chunk_end)]

        total_speech = sum(e - s for s, e in merged) or 0.1
        total_chars = sum(len(s) for s in sentences) or 1

        def map_speech_to_real(speech_offset):
            temp = speech_offset
            for s, e in merged:
                dur = e - s
                if temp <= dur:
                    return s + temp
                temp -= dur
            return merged[-1][1]

        results = []
        current_speech = 0.0
        for s in sentences:
            ratio = len(s) / total_chars
            s_dur = ratio * total_speech
            start = map_speech_to_real(current_speech)
            end = map_speech_to_real(current_speech + s_dur)
            start = max(chunk_start, min(start, chunk_end))
            end = max(start + 0.1, min(end, chunk_end))
            results.append({"start": start, "end": end, "text": s})
            current_speech += s_dur

        return results

    @staticmethod
    def cleanup_temp_file(path: str):
        """安全删除临时文件"""
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
