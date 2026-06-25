"""
MiMo ASR Provider — 基准线实现
小米 MiMo ASR 的 chat/completions + input_audio 格式。
从 transcriber.py 的 online 分支完整迁移，保持行为零变化。
"""
import os
import re
import time
import httpx
from app.config import config, get_short_path_name
from app.core.asr_providers.base import ASRProvider
from app.core.network import doh_dns_bypass


class MiMoASRProvider(ASRProvider):
    """小米 MiMo ASR — chat/completions + input_audio 格式"""

    def get_display_name(self) -> str:
        return "MiMo ASR"

    def transcribe(self, wav_path: str, diarization_segments: list[dict],
                   progress_callback=None) -> list[dict]:
        from app.config import config

        online_api_key = config.get("online_api_key", "").strip()
        online_base_url = config.get("online_base_url", "https://token-plan-sgp.xiaomimimo.com/v1").strip()
        online_model = config.get("online_model", "mimo-v2.5-asr").strip()

        if not online_api_key:
            raise Exception("在线转录模式已启用，但尚未在系统设置中配置 Mimo API Key，请先配置参数。")

        audio_duration = self.get_audio_duration(wav_path)
        print(f"📡 [LOG] 正在使用 MiMo ASR 进行识别。目标 API: {online_base_url} | 模型: {online_model}")
        print(f"📦 [LOG] 音频总时长: {audio_duration:.2f} 秒")

        chunk_length = 60.0
        num_chunks = max(1, int((audio_duration + chunk_length - 1) // chunk_length))
        all_segments = []

        for i in range(num_chunks):
            start_offset = i * chunk_length
            slice_duration = min(chunk_length, audio_duration - start_offset)
            if slice_duration <= 0.1:
                continue

            chunk_mp3_path = None
            try:
                print(f"✂️ [LOG] 正在提取分片 {i+1}/{num_chunks}: 从 {start_offset:.2f}s 开始，时长 {slice_duration:.2f}s...")
                chunk_mp3_path = self.extract_chunk_as_mp3(wav_path, start_offset, slice_duration, i)
                audio_base64 = self.audio_file_to_base64(chunk_mp3_path)

                # 发起 MiMo API 请求
                url = f"{online_base_url.rstrip('/')}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {online_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": online_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "input_audio",
                                    "input_audio": {
                                        "data": audio_base64,
                                        "format": "mp3"
                                    }
                                }
                            ]
                        }
                    ]
                }

                print(f"⏳ [LOG] 正在发送分片 {i+1}/{num_chunks} 请求到 MiMo API...")
                response = self._send_request(url, headers, payload)

                resp_data = response.json()
                full_text = resp_data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if not full_text:
                    print(f"⚠️ [LOG] 分片 {i+1} 返回识别文本为空，跳过该分片")
                    continue

                # 句子分割 + 去重
                sentences = self.split_text_to_sentences(full_text)
                sentences = self.deduplicate_sentences(sentences)
                if not sentences:
                    continue

                # 映射到物理时间轴
                chunk_end = start_offset + slice_duration
                mapped = self.map_sentences_to_timestamps(
                    sentences, diarization_segments, start_offset, chunk_end
                )
                all_segments.extend(mapped)

                # 进度回调
                if progress_callback and mapped:
                    progress = 60.0 + (mapped[-1]["end"] / audio_duration) * 15.0
                    progress = min(progress, 75.0)
                    try:
                        progress_callback(progress)
                    except Exception as pe:
                        print(f"⚠️ [LOG] 进度回调触发异常: {pe}")

            except Exception as chunk_ex:
                raise chunk_ex
            finally:
                if chunk_mp3_path:
                    self.cleanup_temp_file(chunk_mp3_path)

        print(f"🟢 [LOG] MiMo ASR 识别成功！共拆分出 {len(all_segments)} 段带有时间戳的句子。")
        return all_segments

    def _send_request(self, url: str, headers: dict, payload: dict) -> httpx.Response:
        """4 级自适应网络请求（与原逻辑完全一致）"""
        response = None

        # 1. 系统代理
        try:
            with httpx.Client(timeout=400.0, trust_env=True) as client:
                response = client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    print(f"🟢 [LOG] 通过代理请求成功！")
                    return response
        except Exception as e_proxy:
            print(f"⚠️ [LOG] MiMo ASR 代理请求失败: {e_proxy}。正在尝试直连模式...")

        # 2. DoH DNS 绕过直连
        try:
            with doh_dns_bypass(url):
                with httpx.Client(timeout=400.0, trust_env=False) as client:
                    response = client.post(url, headers=headers, json=payload)
                    if response.status_code == 200:
                        print(f"🟢 [LOG] 通过直连(DoH DNS 绕过)请求成功！")
                        return response
        except Exception as e_doh:
            print(f"❌ [LOG] MiMo ASR 直连(DoH DNS 绕过)请求失败: {e_doh}")

        if response is None:
            raise Exception("MiMo ASR API 调用失败：无响应")
        raise Exception(f"MiMo ASR API 调用失败，状态码: {response.status_code}。详情: {response.text}")
