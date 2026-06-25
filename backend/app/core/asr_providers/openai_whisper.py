"""
OpenAI Whisper API Provider
支持 OpenAI 官方 /audio/transcriptions 端点及兼容 API（如 Groq、Together 等）。
API 返回 verbose_json 格式，包含段落级精确时间戳，无需字符比例估算。
"""
import os
import math
import httpx
from app.config import config, get_short_path_name
from app.core.asr_providers.base import ASRProvider
from app.core.network import doh_dns_bypass


class OpenAIWhisperProvider(ASRProvider):
    """OpenAI Whisper API — multipart 上传，返回精确时间戳"""

    def get_display_name(self) -> str:
        return "OpenAI Whisper API"

    def transcribe(self, wav_path: str, diarization_segments: list[dict],
                   progress_callback=None) -> list[dict]:
        online_api_key = config.get("online_api_key", "").strip()
        online_base_url = config.get("online_base_url", "https://api.openai.com/v1").strip()
        online_model = config.get("online_model", "whisper-1").strip()

        if not online_api_key:
            raise Exception("OpenAI Whisper 模式已启用，但尚未配置 API Key。")

        audio_duration = self.get_audio_duration(wav_path)
        print(f"📡 [LOG] 正在使用 OpenAI Whisper API 进行识别。目标: {online_base_url} | 模型: {online_model}")
        print(f"📦 [LOG] 音频总时长: {audio_duration:.2f} 秒")

        # OpenAI Whisper API 限制 25MB，超过需分片
        file_size = os.path.getsize(wav_path)
        max_size = 24 * 1024 * 1024  # 24MB 安全阈值

        if file_size <= max_size:
            # 整段上传
            all_segments = self._transcribe_single_file(
                wav_path, online_api_key, online_base_url, online_model, 0.0
            )
        else:
            # 按 5 分钟切片上传
            chunk_duration = 300.0
            num_chunks = max(1, int(math.ceil(audio_duration / chunk_duration)))
            all_segments = []

            for i in range(num_chunks):
                start_offset = i * chunk_duration
                slice_dur = min(chunk_duration, audio_duration - start_offset)
                if slice_dur <= 0.1:
                    continue

                chunk_path = None
                try:
                    print(f"✂️ [LOG] OpenAI Whisper 分片 {i+1}/{num_chunks}: {start_offset:.1f}s ~ {start_offset + slice_dur:.1f}s")
                    chunk_path = self.extract_chunk_as_wav(wav_path, start_offset, slice_dur, i)
                    segs = self._transcribe_single_file(
                        chunk_path, online_api_key, online_base_url, online_model, start_offset
                    )
                    all_segments.extend(segs)

                    if progress_callback and segs:
                        progress = 60.0 + (segs[-1]["end"] / audio_duration) * 15.0
                        progress = min(progress, 75.0)
                        try:
                            progress_callback(progress)
                        except Exception:
                            pass
                finally:
                    if chunk_path:
                        self.cleanup_temp_file(chunk_path)

        # 去重（跨分片可能有重叠）
        all_segments = self._deduplicate_segments(all_segments)
        print(f"🟢 [LOG] OpenAI Whisper API 识别成功！共 {len(all_segments)} 段。")
        return all_segments

    def _transcribe_single_file(self, file_path: str, api_key: str,
                                 base_url: str, model: str,
                                 time_offset: float) -> list[dict]:
        """上传单个音频文件到 OpenAI Whisper API"""
        url = f"{base_url.rstrip('/')}/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}

        short_path = get_short_path_name(os.path.abspath(file_path))

        with open(short_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "audio/wav")}
            data = {
                "model": model,
                "response_format": "verbose_json",
                "language": "zh",
            }
            response = self._send_request(url, headers, files=files, data=data)

        result = response.json()
        segments = []

        # OpenAI verbose_json 返回 segments 字段
        if "segments" in result:
            for seg in result["segments"]:
                segments.append({
                    "start": seg.get("start", 0.0) + time_offset,
                    "end": seg.get("end", 0.0) + time_offset,
                    "text": seg.get("text", "").strip()
                })
        elif "text" in result:
            # 某些兼容 API 只返回 text，无时间戳
            sentences = self.split_text_to_sentences(result["text"])
            sentences = self.deduplicate_sentences(sentences)
            for s in sentences:
                segments.append({
                    "start": time_offset,
                    "end": time_offset + 1.0,
                    "text": s
                })

        return segments

    def _send_request(self, url: str, headers: dict,
                      files: dict = None, data: dict = None) -> httpx.Response:
        """4 级自适应网络请求"""
        response = None

        # 1. 系统代理
        try:
            with httpx.Client(timeout=600.0, trust_env=True) as client:
                response = client.post(url, headers=headers, files=files, data=data)
                if response.status_code == 200:
                    print("🟢 [LOG] OpenAI Whisper 代理请求成功！")
                    return response
        except Exception as e:
            print(f"⚠️ [LOG] OpenAI Whisper 代理请求失败: {e}")

        # 2. DoH 直连
        try:
            with doh_dns_bypass(url):
                with httpx.Client(timeout=600.0, trust_env=False) as client:
                    response = client.post(url, headers=headers, files=files, data=data)
                    if response.status_code == 200:
                        print("🟢 [LOG] OpenAI Whisper 直连请求成功！")
                        return response
        except Exception as e:
            print(f"❌ [LOG] OpenAI Whisper 直连请求失败: {e}")

        if response is None:
            raise Exception("OpenAI Whisper API 调用失败：无响应")
        raise Exception(f"OpenAI Whisper API 状态码: {response.status_code}。详情: {response.text}")

    @staticmethod
    def _deduplicate_segments(segments: list[dict]) -> list[dict]:
        """跨分片去重（基于文本内容）"""
        import re
        def clean(t):
            return re.sub(r'[^\w\s]', '', t).strip()

        result = []
        for seg in segments:
            if not result:
                result.append(seg)
            elif clean(seg["text"]) != clean(result[-1]["text"]):
                result.append(seg)
            else:
                result[-1]["end"] = seg["end"]
        return result
