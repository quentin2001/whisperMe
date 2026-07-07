"""
Custom HTTP ASR Provider — 通用 HTTP 适配器
用户自行配置 endpoint、请求格式、响应解析路径。
支持 {{audio_base64}} 占位符模板和 JSONPath 响应提取。
"""
import os
import re
import json
import math
import httpx
from app.config import config, get_short_path_name
from app.core.asr_providers.base import ASRProvider
from app.core.network import doh_dns_bypass


class CustomHTTPProvider(ASRProvider):
    """自定义 HTTP ASR — 用户配置 endpoint 和响应映射"""

    def get_display_name(self) -> str:
        return "自定义 HTTP ASR"

    def transcribe(self, wav_path: str, diarization_segments: list[dict],
                   progress_callback=None) -> list[dict]:
        endpoint = config.get("custom_asr_endpoint", "").strip()
        if not endpoint:
            raise Exception("自定义 HTTP ASR 已启用，但尚未配置 API Endpoint。")

        method = config.get("custom_asr_method", "POST").upper()
        headers_str = config.get("custom_asr_headers", "{}").strip()
        body_template = config.get("custom_asr_body_template", "").strip()
        text_path = config.get("custom_asr_response_jsonpath", "$.data.text").strip()
        ts_path = config.get("custom_asr_timestamp_jsonpath", "").strip()
        audio_format = config.get("custom_asr_audio_format", "mp3").strip()
        chunk_duration = int(config.get("custom_asr_chunk_duration", 60))

        # 解析自定义 headers
        try:
            custom_headers = json.loads(headers_str) if headers_str else {}
        except json.JSONDecodeError:
            custom_headers = {}
            print("⚠️ [LOG] 自定义 ASR Headers JSON 解析失败，使用空 headers")

        # 确保 Content-Type
        if "Content-Type" not in custom_headers:
            custom_headers["Content-Type"] = "application/json"

        api_key = config.get("online_api_key", "").strip()
        if api_key and "Authorization" not in custom_headers:
            custom_headers["Authorization"] = f"Bearer {api_key}"

        audio_duration = self.get_audio_duration(wav_path)
        print(f"📡 [LOG] 正在使用自定义 HTTP ASR 进行识别。Endpoint: {endpoint}")
        print(f"📦 [LOG] 音频总时长: {audio_duration:.2f} 秒 | 分片: {chunk_duration}s | 格式: {audio_format}")

        num_chunks = max(1, int(math.ceil(audio_duration / chunk_duration)))
        
        # Phase 1: 串行提取所有分片
        chunk_tasks = []
        for i in range(num_chunks):
            start_offset = i * chunk_duration
            slice_duration = min(chunk_duration, audio_duration - start_offset)
            if slice_duration <= 0.1:
                continue
                
            chunk_path = None
            try:
                print(f"✂️ [LOG] 自定义 ASR 提取分片 {i+1}/{num_chunks}: {start_offset:.1f}s ~ {start_offset + slice_duration:.1f}s")
                if audio_format == "wav":
                    chunk_path = self.extract_chunk_as_wav(wav_path, start_offset, slice_duration, i)
                else:
                    chunk_path = self.extract_chunk_as_mp3(wav_path, start_offset, slice_duration, i)

                audio_b64 = self.audio_file_to_base64(chunk_path)
                chunk_tasks.append({
                    "index": i,
                    "start_offset": start_offset,
                    "slice_duration": slice_duration,
                    "audio_b64": audio_b64,
                    "chunk_path": chunk_path
                })
            except Exception as ex:
                print(f"⚠️ [LOG] 分片 {i+1} 提取失败: {ex}")
                if chunk_path:
                    self.cleanup_temp_file(chunk_path)

        # Phase 2: 并发发送 API 请求
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        max_workers = config.get("max_concurrent_tasks", 4)
        
        results_lock = threading.Lock()
        all_results = []
        progress_lock = threading.Lock()
        last_progress_end = 0.0

        def process_chunk(task):
            i = task["index"]
            start_offset = task["start_offset"]
            slice_duration = task["slice_duration"]
            audio_b64 = task["audio_b64"]
            
            # 构建请求 body
            if body_template:
                body_str = body_template.replace("{{audio_base64}}", audio_b64)
                body_str = body_str.replace("{{audio_format}}", audio_format)
                body_str = body_str.replace("{{chunk_index}}", str(i))
                body_str = body_str.replace("{{start_offset}}", str(start_offset))
                try:
                    body = json.loads(body_str)
                except json.JSONDecodeError:
                    body = body_str
            else:
                body = {
                    "audio": audio_b64,
                    "format": audio_format,
                    "language": "zh"
                }

            # 发送请求
            response = self._send_request(endpoint, method, custom_headers, body)
            result = response.json()

            # 提取文本
            text = self._extract_by_path(result, text_path)
            if not text:
                print(f"⚠️ [LOG] 分片 {i+1} 响应中未提取到文本 (jsonpath: {text_path})，跳过")
                return None

            # 提取时间戳（可选）
            timestamps = None
            if ts_path:
                timestamps = self._extract_by_path(result, ts_path)

            chunk_segments = []
            if timestamps and isinstance(timestamps, list) and len(timestamps) > 0:
                for ts_item in timestamps:
                    if isinstance(ts_item, dict):
                        seg_text = ts_item.get("text", "").strip()
                        seg_start = ts_item.get("start", 0.0) + start_offset
                        seg_end = ts_item.get("end", seg_start + 1.0) + start_offset
                    elif isinstance(ts_item, list) and len(ts_item) >= 2:
                        seg_text = text  # fallback
                        seg_start = ts_item[0] / 1000.0 + start_offset
                        seg_end = ts_item[1] / 1000.0 + start_offset
                    else:
                        continue
                    if seg_text:
                        chunk_segments.append({
                            "start": seg_start,
                            "end": seg_end,
                            "text": seg_text
                        })
            else:
                # 无时间戳 — 使用字符比例估算
                sentences = self.split_text_to_sentences(text)
                sentences = self.deduplicate_sentences(sentences)
                chunk_end = start_offset + slice_duration
                mapped = self.map_sentences_to_timestamps(
                    sentences, diarization_segments, start_offset, chunk_end
                )
                chunk_segments.extend(mapped)

            # 进度回调
            if progress_callback and chunk_segments:
                nonlocal last_progress_end
                with progress_lock:
                    if chunk_segments[-1]["end"] > last_progress_end:
                        last_progress_end = chunk_segments[-1]["end"]
                        progress = 60.0 + (last_progress_end / max(audio_duration, 1.0)) * 15.0
                        progress = min(progress, 75.0)
                        try:
                            progress_callback(progress)
                        except Exception as pe:
                            if str(pe) == "TASK_CANCELLED":
                                raise pe
                            
            return (task["index"], chunk_segments)
            
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_chunk, t): t for t in chunk_tasks}
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        with results_lock:
                            all_results.append(result)
                except Exception as e:
                    if str(e) == "TASK_CANCELLED":
                        raise e
                    task = futures[future]
                    print(f"❌ [LOG] 分片 {task['index']+1} 请求失败: {e}")
                    
        all_results.sort(key=lambda x: x[0])
        all_segments = []
        for _, segs in all_results:
            all_segments.extend(segs)

        # 清理临时文件
        for task in chunk_tasks:
            if task["chunk_path"]:
                self.cleanup_temp_file(task["chunk_path"])

        print(f"🟢 [LOG] 自定义 HTTP ASR 识别成功！共 {len(all_segments)} 段。")
        return all_segments

    def _send_request(self, url: str, method: str, headers: dict, body) -> httpx.Response:
        """HTTP 请求（代理 + DoH 直连）"""
        response = None

        try:
            with httpx.Client(timeout=600.0, trust_env=True) as client:
                if method == "GET":
                    response = client.get(url, headers=headers, params=body if isinstance(body, dict) else {})
                else:
                    response = client.post(url, headers=headers, json=body if isinstance(body, (dict, list)) else body)
                if response.status_code == 200:
                    return response
        except Exception as e:
            print(f"⚠️ [LOG] 自定义 ASR 代理请求失败: {e}")

        try:
            with doh_dns_bypass(url):
                with httpx.Client(timeout=600.0, trust_env=False) as client:
                    if method == "GET":
                        response = client.get(url, headers=headers, params=body if isinstance(body, dict) else {})
                    else:
                        response = client.post(url, headers=headers, json=body if isinstance(body, (dict, list)) else body)
                    if response.status_code == 200:
                        return response
        except Exception as e:
            print(f"❌ [LOG] 自定义 ASR 直连请求失败: {e}")

        if response is None:
            raise Exception("自定义 HTTP ASR 调用失败：无响应")
        raise Exception(f"自定义 HTTP ASR 状态码: {response.status_code}。详情: {response.text}")

    @staticmethod
    def _extract_by_path(data, path: str):
        """
        简易 JSONPath 提取，支持 $.a.b.c 格式和数组索引 $.a[0].b。
        """
        if not path or not path.startswith("$"):
            return data

        parts = path.replace("$", "").strip(".").split(".")
        current = data

        for part in parts:
            if current is None:
                return None

            # 处理数组索引: a[0] -> key=a, index=0
            match = re.match(r'^(\w+)\[(\d+)\]$', part)
            if match:
                key, idx = match.group(1), int(match.group(2))
                if isinstance(current, dict):
                    current = current.get(key)
                if isinstance(current, list) and idx < len(current):
                    current = current[idx]
                else:
                    return None
            elif isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                # 尝试将 part 解析为整数索引
                try:
                    idx = int(part)
                    current = current[idx] if idx < len(current) else None
                except (ValueError, IndexError):
                    return None
            else:
                return None

        return current
