"""
FunASR Provider — 阿里达摩院开源 ASR
支持两种模式:
  1. 本地 FunASR Server (WebSocket)
  2. 阿里云 API (HTTP)
"""
import os
import re
import json
import math
import httpx
import struct
from app.config import config, get_short_path_name
from app.core.asr_providers.base import ASRProvider
from app.core.network import doh_dns_bypass


class FunASRProvider(ASRProvider):
    """FunASR — 阿里达摩院语音识别"""

    def get_display_name(self) -> str:
        return "FunASR (阿里达摩院)"

    @property
    def supports_native_timestamps(self) -> bool:
        online_base_url = config.get("online_base_url", "ws://localhost:10095").strip()
        return online_base_url.startswith("ws://") or online_base_url.startswith("wss://")

    def transcribe(self, wav_path: str, diarization_segments: list[dict],
                   progress_callback=None) -> list[dict]:
        online_base_url = config.get("online_base_url", "ws://localhost:10095").strip()
        online_api_key = config.get("online_api_key", "").strip()

        audio_duration = self.get_audio_duration(wav_path)
        print(f"📡 [LOG] 正在使用 FunASR 进行识别。目标: {online_base_url}")
        print(f"📦 [LOG] 音频总时长: {audio_duration:.2f} 秒")

        # 根据 URL scheme 判断使用 WebSocket 还是 HTTP
        if online_base_url.startswith("ws://") or online_base_url.startswith("wss://"):
            segments = self._transcribe_websocket(wav_path, online_base_url, audio_duration)
        else:
            segments = self._transcribe_http(wav_path, online_base_url, online_api_key,
                                             diarization_segments, audio_duration, progress_callback)

        print(f"🟢 [LOG] FunASR 识别成功！共 {len(segments)} 段。")
        return segments

    def _transcribe_websocket(self, wav_path: str, ws_url: str,
                               audio_duration: float) -> list[dict]:
        """本地 FunASR Server — WebSocket 协议"""
        try:
            import websocket
        except ImportError:
            raise Exception("FunASR WebSocket 模式需要 websocket-client 库，请执行: pip install websocket-client")

        short_path = get_short_path_name(os.path.abspath(wav_path))

        # 读取 WAV 音频数据（跳过 44 字节头）
        with open(short_path, "rb") as f:
            wav_header = f.read(44)
            audio_data = f.read()

        # 读取采样率
        sample_rate = struct.unpack_from('<I', wav_header, 24)[0] if len(wav_header) >= 28 else 16000

        all_results = []
        ws = websocket.create_connection(ws_url, timeout=600)

        try:
            # 发送初始配置
            init_msg = json.dumps({
                "mode": "online",
                "chunk_size": [5, 10, 5],
                "wav_name": os.path.basename(wav_path),
                "is_speaking": True,
                "wav_format": "pcm",
                "audio_fs": sample_rate
            })
            ws.send(init_msg)

            # 分块发送音频（每帧 9600 字节 ≈ 0.3s @16kHz）
            chunk_size = 9600
            for offset in range(0, len(audio_data), chunk_size):
                chunk = audio_data[offset:offset + chunk_size]
                is_last = (offset + chunk_size >= len(audio_data))
                ws.send_binary(chunk)
                if is_last:
                    ws.send(json.dumps({"is_speaking": False}))

            # 接收结果
            while True:
                try:
                    msg = ws.recv()
                    if isinstance(msg, str):
                        data = json.loads(msg)
                        text = data.get("text", "")
                        mode = data.get("mode", "")
                        if text and mode == "2pass-sentence":
                            seg_start = data.get("timestamp", [[0]])[0][0] / 1000.0 if data.get("timestamp") else 0.0
                            seg_end = data.get("timestamp", [[0]])[-1][-1] / 1000.0 if data.get("timestamp") else seg_start + 1.0
                            all_results.append({
                                "start": seg_start,
                                "end": seg_end,
                                "text": text.strip()
                            })
                        if data.get("is_final", False):
                            break
                except Exception:
                    break
        finally:
            ws.close()

        return all_results

    def _transcribe_http(self, wav_path: str, base_url: str, api_key: str,
                          diarization_segments: list[dict], audio_duration: float,
                          progress_callback=None) -> list[dict]:
        """阿里云 FunASR HTTP API — 分片上传"""
        chunk_length = 60.0
        num_chunks = max(1, int(math.ceil(audio_duration / chunk_length)))
        all_segments = []

        for i in range(num_chunks):
            start_offset = i * chunk_length
            slice_duration = min(chunk_length, audio_duration - start_offset)
            if slice_duration <= 0.1:
                continue

            chunk_path = None
            try:
                print(f"✂️ [LOG] FunASR 分片 {i+1}/{num_chunks}: {start_offset:.1f}s ~ {start_offset + slice_duration:.1f}s")
                chunk_path = self.extract_chunk_as_wav(wav_path, start_offset, slice_duration, i)
                short_chunk = get_short_path_name(os.path.abspath(chunk_path))

                url = f"{base_url.rstrip('/')}/api/v1/asr"
                headers = {"Content-Type": "application/octet-stream"}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"

                with open(short_chunk, "rb") as f:
                    audio_data = f.read()

                response = self._send_http_request(url, headers, audio_data)
                result = response.json()

                # FunASR HTTP 返回格式: {"result": [{"text": "...", "timestamp": [[s,e], ...]}]}
                results = result.get("result", result.get("data", []))
                if isinstance(results, list):
                    for item in results:
                        text = item.get("text", "").strip()
                        ts = item.get("timestamp", [])
                        if text:
                            if ts and len(ts) > 0:
                                seg_start = ts[0][0] / 1000.0 + start_offset
                                seg_end = ts[-1][-1] / 1000.0 + start_offset
                            else:
                                seg_start = start_offset
                                seg_end = start_offset + slice_duration
                            all_segments.append({
                                "start": seg_start,
                                "end": seg_end,
                                "text": text
                            })
                elif isinstance(results, str) and results.strip():
                    # 某些版本直接返回文本
                    sentences = self.split_text_to_sentences(results)
                    sentences = self.deduplicate_sentences(sentences)
                    mapped = self.map_sentences_to_timestamps(
                        sentences, diarization_segments, start_offset,
                        start_offset + slice_duration
                    )
                    all_segments.extend(mapped)

                if progress_callback:
                    progress = 60.0 + ((start_offset + slice_duration) / audio_duration) * 15.0
                    progress = min(progress, 75.0)
                    try:
                        progress_callback(progress)
                    except Exception:
                        pass

            finally:
                if chunk_path:
                    self.cleanup_temp_file(chunk_path)

        return all_segments

    def _send_http_request(self, url: str, headers: dict, data: bytes) -> httpx.Response:
        """HTTP 请求（代理 + DoH 直连）"""
        response = None

        try:
            with httpx.Client(timeout=400.0, trust_env=True) as client:
                response = client.post(url, headers=headers, content=data)
                if response.status_code == 200:
                    return response
        except Exception as e:
            print(f"⚠️ [LOG] FunASR HTTP 代理请求失败: {e}")

        try:
            with doh_dns_bypass(url):
                with httpx.Client(timeout=400.0, trust_env=False) as client:
                    response = client.post(url, headers=headers, content=data)
                    if response.status_code == 200:
                        return response
        except Exception as e:
            print(f"❌ [LOG] FunASR HTTP 直连请求失败: {e}")

        if response is None:
            raise Exception("FunASR HTTP API 调用失败：无响应")
        raise Exception(f"FunASR HTTP API 状态码: {response.status_code}。详情: {response.text}")
