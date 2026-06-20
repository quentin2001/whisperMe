import os
import sys
import torch
import subprocess
import socket
from urllib.parse import urlparse
from contextlib import contextmanager
import httpx
from app.config import (
    SHORT_LOCAL_WHISPER_MODEL_PATH, 
    HF_TOKEN, 
    get_short_path_name,
    FFMPEG_PATH
)

def resolve_host_via_doh(host: str) -> str:
    if not host:
        return None
    
    # 硬编码的常用域名静态 IP 兜底，防止 Clash DNS 劫持和 DoH 本身也被拦截导致的双重失效
    STATIC_IP_MAPS = {
        "token-plan-sgp.xiaomimimo.com": "8.222.147.102"
    }
    
    # 尝试 DoH 解析
    doh_urls = [
        "https://dns.alidns.com/resolve",
        "https://doh.pub/dns-query"
    ]
    for doh_base in doh_urls:
        try:
            params = {"name": host, "type": "1"}
            with httpx.Client(trust_env=False, timeout=5.0) as client:
                resp = client.get(doh_base, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    answers = data.get("Answer", [])
                    for ans in answers:
                        if ans.get("type") == 1:
                            ip = ans.get("data")
                            if ip and not ip.startswith("198.18."):
                                return ip
        except Exception:
            pass
            
    # 尝试系统 DNS 解析
    try:
        ips = socket.getaddrinfo(host, None)
        if ips:
            ip = ips[0][4][0]
            if ip and not ip.startswith("198.18."):
                return ip
    except Exception:
        pass
        
    # 如果解析失败或者是 Clash 劫持的 fake-IP (198.18.*.*)，则使用静态 IP 兜底
    if host in STATIC_IP_MAPS:
        print(f"⚠️ [LOG] {host} 解析失败或被 Clash DNS 劫持，使用静态 IP 兜底: {STATIC_IP_MAPS[host]}")
        return STATIC_IP_MAPS[host]
        
    return None

@contextmanager
def doh_dns_bypass(url: str):
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or (80 if parsed.scheme == "http" else 443)
    except Exception:
        host = None
        port = None

    if not host:
        yield
        return

    real_ip = resolve_host_via_doh(host)
    if real_ip and real_ip != "198.18.0.46":
        print(f"🎯 [LOG] DoH 拦截 DNS 成功 -> 将域名 {host} 直接映射至公网 IP {real_ip} 进行直连")
        original_getaddrinfo = socket.getaddrinfo
        def custom_getaddrinfo(*args, **kwargs):
            h = args[0] if args else kwargs.get("host")
            if h == host:
                p = args[1] if len(args) > 1 else kwargs.get("port")
                target_port = p
                if target_port is None: target_port = port
                try: target_port = int(target_port)
                except ValueError: target_port = port
                return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (real_ip, target_port))]
            return original_getaddrinfo(*args, **kwargs)
        
        socket.getaddrinfo = custom_getaddrinfo
        try:
            yield
        finally:
            socket.getaddrinfo = original_getaddrinfo
    else:
        yield


class WhisperSegmentDummy:
    def __init__(self, start, end, text):
        self.start = start
        self.end = end
        self.text = text


class PodcastTranscriber:
    def __init__(self):
        # 懒加载设备检测，彻底脱离对 torch 的全局依赖
        self.device = "cpu"
        try:
            # 使用原生的命令行探测是否有 NVIDIA 显卡
            subprocess.check_output("nvidia-smi", shell=True, stderr=subprocess.STDOUT)
            self.device = "cuda"
        except Exception:
            pass
        self.compute_type = "float16" if self.device == "cuda" else "float32"
        print(f"🖥️ [LOG] 初始化转录引擎 - 默认运行设备: {self.device.upper()} | 运算精度: {self.compute_type}")

    def run_diarization(self, wav_path: str) -> list[dict]:
        """
        运行 pyannote.audio 进行声纹识别与说话人分割
        """
        # 对路径进行短路径安全处理，防御 C++ 库路径崩溃
        short_wav_path = get_short_path_name(os.path.abspath(wav_path))
        
        # 验证 Hugging Face Token 长度是否合理
        if not HF_TOKEN or len(HF_TOKEN) < 30:
            print("⚠️ [LOG 严重警告] 检测到未配置或无效的 Hugging Face Token。自动触发熔断降级：跳过声纹角色切分，直接进入语音文本识别！")
            return []

        try:
            import torch
            from pyannote.audio import Pipeline
            # 动态可用显存监控，实现硬件级别的热熔断 CPU 降级机制
            device_to_use = self.device
            if device_to_use == "cuda":
                try:
                    free_mem, total_mem = torch.cuda.mem_get_info()
                    free_gb = free_mem / (1024 ** 3)
                    total_gb = total_mem / (1024 ** 3)
                    print(f"ℹ️ [LOG] GPU 显存监控 - 当前可用: {free_gb:.2f} GB / 总计: {total_gb:.2f} GB")
                    if free_gb < 1.5:
                        print(f"⚠️ [LOG] 检测到 GPU 剩余可用显存 ({free_gb:.2f} GB) 小于安全阈值 1.5 GB。为了防止系统卡死及 WDDM 内存交换，声纹分割降级至 CPU 运行。")
                        device_to_use = "cpu"
                except Exception as mem_ex:
                    print(f"⚠️ [LOG] 获取 GPU 显存失败: {mem_ex}")

            print("📡 [LOG] 正在从 hf-mirror 镜像源加载 PyAnnote 3.1 声纹模型管道...")
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1", 
                use_auth_token=HF_TOKEN
            )
            
            # 将模型载入目标设备
            pipeline.to(torch.device(device_to_use))
            
            print(f"⏳ [LOG] 声纹网络分析中... 运行设备: {device_to_use.upper()} | 音频路径: {short_wav_path}")
            diarization = pipeline(short_wav_path)
            
            diarization_list = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                diarization_list.append({
                    "start": turn.start, 
                    "end": turn.end, 
                    "speaker": speaker
                })
                
            unique_speakers = set([d["speaker"] for d in diarization_list])
            print(f"🟢 [LOG] 声纹角色分割顺利完成！检测到 {len(unique_speakers)} 位发言人: {list(unique_speakers)}")
            return diarization_list
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ [🚨 熔断拦截] 声纹分割过程中报错: {e}。系统已自动降级为纯语音转文字，不包含说话人姓名区分。")
            return []

    def transcribe_and_merge(self, wav_path: str, diarization_segments: list[dict], progress_callback=None, asr_mode: str = "local") -> list[dict]:
        """
        运行 faster-whisper 或在线 ASR，并将识别的段落与 pyannote 声纹时间轴交叉重叠合并
        """
        whisper_segments = []
        duration = 1.0

        if asr_mode == "online":
            from app.config import config
            import math
            import httpx
            import base64
            import re
            import wave

            online_api_key = config.get("online_api_key", "").strip()
            online_base_url = config.get("online_base_url", "https://token-plan-sgp.xiaomimimo.com/v1").strip()
            online_model = config.get("online_model", "mimo-v2.5-asr").strip()

            if not online_api_key:
                raise Exception("在线转录模式已启用，但尚未在系统设置中配置 Mimo API Key，请先配置参数。")

            # 1. 读取本地标准化音频的总时长，以确定分片逻辑
            audio_duration = 1.0
            try:
                with wave.open(wav_path, "rb") as w:
                    frames = w.getnframes()
                    rate = w.getframerate()
                    audio_duration = frames / float(rate)
            except Exception as we:
                print(f"⚠️ [LOG] 读取 WAV 时长失败: {we}")

            print(f"📡 [LOG] 正在使用在线 ASR 模式进行识别。目标 API: {online_base_url} | 模型: {online_model}")
            print(f"📦 [LOG] 音频总时长: {audio_duration:.2f} 秒")

            # 2. 分片处理逻辑 (为了提升时间轴对齐精度，每分片设置为 60.0 秒)
            chunk_length = 60.0
            num_chunks = math.ceil(audio_duration / chunk_length)
            
            for i in range(num_chunks):
                start_offset = i * chunk_length
                slice_duration = min(chunk_length, audio_duration - start_offset)
                if slice_duration <= 0.1:
                    continue

                chunk_mp3_path = wav_path.replace(".wav", f"_chunk_{i}.mp3")
                print(f"✂️ [LOG] 正在提取分片 {i+1}/{num_chunks}: 从 {start_offset:.2f}s 开始，时长 {slice_duration:.2f}s...")

                try:
                    # 使用 FFmpeg 提取对应分片并压缩为 32kbps mono MP3，-ss 放在 -i 之后以确保时间轴切片精确
                    cmd = [
                        FFMPEG_PATH, 
                        '-y', 
                        '-i', get_short_path_name(wav_path), 
                        '-ss', str(start_offset),
                        '-t', str(slice_duration),
                        '-codec:a', 'libmp3lame', 
                        '-b:a', '32k', 
                        '-ac', '1', 
                        get_short_path_name(chunk_mp3_path)
                    ]
                    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if res.returncode != 0 or not os.path.exists(chunk_mp3_path):
                        raise Exception(f"FFmpeg slice creation failed for chunk {i}: {res.stderr.decode('utf-8', errors='ignore')}")

                    # 转换为 Base64
                    with open(chunk_mp3_path, "rb") as f:
                        audio_base_64 = "data:audio/mp3;base64," + base64.b64encode(f.read()).decode("utf-8")

                    # 物理清理临时分片 MP3 文件
                    try:
                        os.remove(chunk_mp3_path)
                    except Exception:
                        pass

                    # 发起 API 请求
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
                                            "data": audio_base_64,
                                            "format": "mp3"
                                        }
                                    }
                                ]
                            }
                        ]
                    }

                    print(f"⏳ [LOG] 正在发送分片 {i+1}/{num_chunks} 请求到 {url} 并等待转录结果...")
                    response = None
                    # 1. 优先使用系统默认代理连接
                    try:
                        with httpx.Client(timeout=400.0, trust_env=True) as client:
                            response = client.post(url, headers=headers, json=payload)
                            if response.status_code == 200:
                                print(f"🟢 [LOG] 分片 {i+1} 通过代理请求成功！")
                    except Exception as e_proxy:
                        print(f"⚠️ [LOG] ASR 分片 {i+1} 代理请求失败: {e_proxy}。正在尝试直连模式...")
                        
                    # 2. 直连模式兜底 (结合 DoH 绕过 Clash 劫持)
                    if response is None or response.status_code != 200:
                        try:
                            with doh_dns_bypass(url):
                                with httpx.Client(timeout=400.0, trust_env=False) as client:
                                    response = client.post(url, headers=headers, json=payload)
                                    if response.status_code == 200:
                                        print(f"🟢 [LOG] 分片 {i+1} 通过直连(DoH DNS 绕过)请求成功！")
                        except Exception as e_doh:
                            print(f"❌ [LOG] ASR 分片 {i+1} 直连(DoH DNS 绕过)请求失败: {e_doh}")
                        
                    if response is None or response.status_code != 200:
                        detail_msg = response.text if response is not None else "无响应"
                        status_code = response.status_code if response is not None else "未知"
                        raise Exception(f"在线 ASR API 调用失败，状态码: {status_code}。详情: {detail_msg}")
                        
                    resp_data = response.json()
                    full_text = resp_data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    if not full_text:
                        print(f"⚠️ [LOG] 分片 {i+1} 返回识别文本为空，跳过该分片")
                        continue

                    # 3. 将当前分片文本切割成句子，并按比例估算当前分片内部的相对时间戳，并加上 start_offset 转换为全局时间轴
                    raw_sentences = re.split(r'([。？！；\n])', full_text)
                    
                    sentences = []
                    current_sentence = ""
                    for item in raw_sentences:
                        if not item:
                            continue
                        if item in ["。", "？", "！", "；", "\n"]:
                            if current_sentence:
                                sentences.append(current_sentence + (item if item != "\n" else ""))
                                current_sentence = ""
                        else:
                            current_sentence += item
                    if current_sentence:
                        sentences.append(current_sentence)
                        
                    sentences = [s.strip() for s in sentences if s.strip()]
                    if not sentences:
                        continue

                    # 过滤相邻重复句，防范 ASR 幻觉循环引发的字句重复与时间线漂移
                    import re
                    def clean_txt(text):
                        return re.sub(r'[^\w\s]', '', text).strip()
                    
                    deduped_sentences = []
                    for s in sentences:
                        if not deduped_sentences:
                            deduped_sentences.append(s)
                        else:
                            if clean_txt(s) != clean_txt(deduped_sentences[-1]):
                                deduped_sentences.append(s)
                    sentences = deduped_sentences
                    if not sentences:
                        continue


                    # 按照声纹分割段（语音活动区间 VAD）对句子进行精准时间轴映射，剔除静音期，彻底解决台词偏斜与漂移
                    chunk_start = start_offset
                    chunk_end = start_offset + slice_duration
                    
                    active_segs = []
                    for d in diarization_segments:
                        # 寻找在当前分片范围内的交叉时间段
                        s_max = max(d["start"], chunk_start)
                        e_min = min(d["end"], chunk_end)
                        if e_min > s_max + 0.1: # 至少重叠 100ms 视为有效说话区间
                            active_segs.append((s_max, e_min))
                            
                    # 将紧邻的说话段（间隔小于 0.5s）或重叠段合并成连续的语音块
                    active_segs.sort()
                    merged_segs = []
                    for seg in active_segs:
                        if not merged_segs:
                            merged_segs.append(seg)
                        else:
                            last_s, last_e = merged_segs[-1]
                            curr_s, curr_e = seg
                            if curr_s - last_e < 0.5: # 紧邻合并
                                merged_segs[-1] = (last_s, max(last_e, curr_e))
                            else:
                                merged_segs.append(seg)
                                
                    if not merged_segs:
                        # 声纹列表为空时退化到全分片映射以保持鲁棒兼容
                        merged_segs = [(chunk_start, chunk_end)]
                        
                    total_speech_duration = sum(e - s for s, e in merged_segs)
                    if total_speech_duration <= 0:
                        total_speech_duration = 0.1
                        
                    total_chars = sum(len(s) for s in sentences)
                    if total_chars == 0:
                        total_chars = 1
                        
                    current_speech_time = 0.0
                    
                    # 映射辅助函数：将相对的“语音时间轴”偏移转换为实际的“物理时间轴”时间戳
                    def map_speech_to_real_time(speech_offset):
                        temp_offset = speech_offset
                        for s_start, s_end in merged_segs:
                            seg_dur = s_end - s_start
                            if temp_offset <= seg_dur:
                                return s_start + temp_offset
                            temp_offset -= seg_dur
                        return merged_segs[-1][1]
                        
                    for s in sentences:
                        char_len = len(s)
                        duration_ratio = char_len / total_chars
                        s_speech_duration = duration_ratio * total_speech_duration
                        
                        start = map_speech_to_real_time(current_speech_time)
                        end = map_speech_to_real_time(current_speech_time + s_speech_duration)
                        
                        # 单调性与物理边界约束
                        start = max(chunk_start, min(start, chunk_end))
                        end = max(start + 0.1, min(end, chunk_end))
                        
                        whisper_segments.append(WhisperSegmentDummy(start, end, s))
                        current_speech_time += s_speech_duration

                except Exception as chunk_ex:
                    if os.path.exists(chunk_mp3_path):
                        try:
                            os.remove(chunk_mp3_path)
                        except Exception:
                            pass
                    raise chunk_ex

            duration = audio_duration
            print(f"🟢 [LOG] 在线 ASR 识别成功！所有分片合并完毕，共拆分出 {len(whisper_segments)} 段带有时间戳的句子。")

        else:
            # 本地转录模式
            short_wav_path = get_short_path_name(os.path.abspath(wav_path))
            import torch
            from faster_whisper import WhisperModel
            
            # 动态显存监控与资源控制
            device_to_use = self.device
            compute_type_to_use = self.compute_type
            if device_to_use == "cuda":
                try:
                    free_mem, total_mem = torch.cuda.mem_get_info()
                    free_gb = free_mem / (1024 ** 3)
                    total_gb = total_mem / (1024 ** 3)
                    print(f"ℹ️ [LOG] GPU 显存监控 - 当前可用: {free_gb:.2f} GB / 总计: {total_gb:.2f} GB")
                    if free_gb < 1.5:
                        print(f"⚠️ [LOG] 检测到 GPU 剩余可用显存 ({free_gb:.2f} GB) 小于安全阈值 1.5 GB。为了防止 OOM，Whisper 降级至 CPU 运行。")
                        device_to_use = "cpu"
                        compute_type_to_use = "float32"
                except Exception as mem_ex:
                    print(f"⚠️ [LOG] 获取 GPU 显存失败: {mem_ex}")

            print(f"🚀 [LOG] 正在以 {device_to_use.upper()} 模式加载 Whisper 模型: {SHORT_LOCAL_WHISPER_MODEL_PATH}")
            
            # 载入本地大模型，使用选定的 device 与 precision
            model = WhisperModel(
                SHORT_LOCAL_WHISPER_MODEL_PATH, 
                device=device_to_use, 
                compute_type=compute_type_to_use, 
                local_files_only=True
            )
            
            print("✨ [LOG] Whisper 模型已成功载入显存！开始高效转汉字...")
            whisper_segments_raw, info = model.transcribe(
                short_wav_path, 
                beam_size=5, 
                language="zh"
            )
            whisper_segments = list(whisper_segments_raw)
            # 过滤相邻重复句，防止本地 Whisper 幻觉循环
            def clean_txt(text):
                return re.sub(r'[^\w\s]', '', text).strip()
            
            deduped_whisper_segments = []
            for seg in whisper_segments:
                if not deduped_whisper_segments:
                    deduped_whisper_segments.append(seg)
                else:
                    if clean_txt(seg.text) != clean_txt(deduped_whisper_segments[-1].text):
                        deduped_whisper_segments.append(seg)
                    else:
                        deduped_whisper_segments[-1].end = seg.end
            whisper_segments = deduped_whisper_segments
            duration = info.duration if info and info.duration else 1.0
        
        has_diarization = len(diarization_segments) > 0
        merged_results = []
        
        # print("\n🎧 【实时瀑布流剧本输出展示开始】\n" + "="*50)
        last_progress_int = 60
        
        for seg in whisper_segments:
            current_speaker = "UNKNOWN_SPEAKER"
            if has_diarization:
                # 寻找哪一个声纹切片的区间包含此文本段的中心点
                seg_center = (seg.start + seg.end) / 2
                best_match_speaker = None
                max_overlap = 0.0
                
                for diar_seg in diarization_segments:
                    # 精准包含中心点
                    if diar_seg["start"] <= seg_center <= diar_seg["end"]:
                        current_speaker = diar_seg["speaker"]
                        break
                    
                    # 备选：寻找重合度最高的区间
                    overlap_start = max(seg.start, diar_seg["start"])
                    overlap_end = min(seg.end, diar_seg["end"])
                    overlap_len = overlap_end - overlap_start
                    if overlap_len > max_overlap:
                        max_overlap = overlap_len
                        best_match_speaker = diar_seg["speaker"]
                else:
                    if best_match_speaker:
                        current_speaker = best_match_speaker
            
            # 时间戳计算
            start_min, start_sec = divmod(int(seg.start), 60)
            start_hour, start_min = divmod(start_min, 60)
            timestamp = f"[{start_hour:02d}:{start_min:02d}:{start_sec:02d}]"
            
            speaker_tag = f"【{current_speaker}】"
            line = f"{timestamp} {speaker_tag}: {seg.text}"
            
            # print(line)  # 控制台实时回显
            
            merged_results.append({
                "start": seg.start,
                "end": seg.end,
                "timestamp_str": timestamp,
                "speaker": current_speaker,
                "text": seg.text
            })
            
            # 计算渐进式进度 (从 60.0% 到 75.0%)
            current_progress = 60.0 + (seg.end / duration) * 15.0
            current_progress = min(current_progress, 75.0)
            current_progress_int = int(current_progress)
            if current_progress_int > last_progress_int:
                last_progress_int = current_progress_int
                if progress_callback:
                    try:
                        progress_callback(float(current_progress_int))
                    except Exception as pe:
                        print(f"⚠️ [LOG] 进度回调触发异常: {pe}")
            
        print("="*50 + f"\n🎉 [LOG] 转录与声纹角色合并工作顺利完成！共识别出 {len(merged_results)} 段对话。")
        return merged_results

    def extract_speaker_embeddings(self, wav_path: str, diarization_segments: list[dict]) -> dict[str, list[float]]:
        """
        Extract representative 512-dimensional voice embeddings for each unique speaker.
        Uses multi-segment average pooling for robustness, then performs intra-episode
        clustering correction to merge speakers that are likely the same person.
        """
        if not diarization_segments or not HF_TOKEN or len(HF_TOKEN) < 30:
            return {}

        try:
            from pyannote.audio import Model, Inference
            from pyannote.core import Segment
            import numpy as np

            print("📡 [LOG] 正在加载 PyAnnote 声纹特征提取模型...")
            model = Model.from_pretrained("pyannote/embedding", use_auth_token=HF_TOKEN)
            
            # 动态分配推理计算设备
            device_to_use = self.device
            if device_to_use == "cuda":
                try:
                    free_mem, _ = torch.cuda.mem_get_info()
                    if free_mem / (1024 ** 3) < 1.5:
                        device_to_use = "cpu"
                except Exception:
                    pass
            inference = Inference(model, window="whole", device=torch.device(device_to_use))
            
            # Find unique speakers
            speakers = set(seg["speaker"] for seg in diarization_segments if "speaker" in seg)
            speaker_embeddings = {}
            
            for speaker in speakers:
                # Find all segments for this speaker
                sp_segs = [s for s in diarization_segments if s.get("speaker") == speaker]
                if not sp_segs:
                    continue
                
                # Sort segments by duration descending
                sp_segs = sorted(sp_segs, key=lambda s: s["end"] - s["start"], reverse=True)
                
                # ====== 多段均值池化策略 ======
                # 筛选出 3-5 段清晰、时长适中（1.5s-10s）的片段，分别提取 Embedding 后取平均
                candidate_segs = []
                for seg in sp_segs:
                    duration = seg["end"] - seg["start"]
                    if duration >= 1.5:
                        candidate_segs.append(seg)
                    if len(candidate_segs) >= 5:
                        break
                
                # 如果没有 >= 1.5s 的段，fallback 到最长的那个
                if not candidate_segs:
                    candidate_segs = [sp_segs[0]]
                
                embeddings_list = []
                for seg in candidate_segs:
                    start = seg["start"]
                    end = seg["end"]
                    # 将每段限制为最长 10 秒，避免噪声区间过长
                    if end - start > 10.0:
                        end = start + 10.0
                    
                    try:
                        emb = inference.crop(wav_path, Segment(start, end))
                        if isinstance(emb, np.ndarray):
                            emb = np.nan_to_num(emb)
                            norm = np.linalg.norm(emb)
                            if norm > 0:
                                embeddings_list.append(emb / norm)
                    except Exception as seg_ex:
                        print(f"⚠️ [LOG] 提取 {speaker} 片段 ({start:.2f}s-{end:.2f}s) 声纹失败: {seg_ex}")
                        continue
                
                if not embeddings_list:
                    print(f"⚠️ [LOG] {speaker} 无法提取任何有效声纹片段，跳过")
                    continue
                
                # Average Pooling: 取所有片段 Embedding 的平均值，再 L2 归一化
                avg_emb = np.mean(embeddings_list, axis=0)
                norm = np.linalg.norm(avg_emb)
                if norm > 0:
                    avg_emb = avg_emb / norm
                
                speaker_embeddings[speaker] = avg_emb.tolist()
                print(f"✅ [LOG] {speaker} 声纹特征提取完成 (使用 {len(embeddings_list)} 段均值池化)")
            
            print(f"🟢 [LOG] 成功完成 {len(speaker_embeddings)} 个发言人的声纹特征提取！")
            
            # ====== 单集内声纹聚类修正 ======
            # 如果两个 SPEAKER 的余弦相似度 >= 0.92，认为是同一人被误切分，自动合并
            if len(speaker_embeddings) >= 2:
                merge_map = {}  # {被合并的 SPEAKER: 合并目标 SPEAKER}
                sp_ids = sorted(speaker_embeddings.keys())
                
                for i in range(len(sp_ids)):
                    if sp_ids[i] in merge_map:
                        continue  # 已被合并，跳过
                    for j in range(i + 1, len(sp_ids)):
                        if sp_ids[j] in merge_map:
                            continue
                        
                        emb_i = np.array(speaker_embeddings[sp_ids[i]])
                        emb_j = np.array(speaker_embeddings[sp_ids[j]])
                        
                        norm_i = np.linalg.norm(emb_i)
                        norm_j = np.linalg.norm(emb_j)
                        if norm_i > 0 and norm_j > 0:
                            sim = np.dot(emb_i, emb_j) / (norm_i * norm_j)
                            if sim >= 0.92:
                                merge_map[sp_ids[j]] = sp_ids[i]
                                print(f"🔗 [LOG] 声纹聚类修正: {sp_ids[j]} 与 {sp_ids[i]} 高度相似 (cos={sim:.4f})，合并为 {sp_ids[i]}")
                
                if merge_map:
                    # 更新 diarization_segments 中的 speaker 标签（原地修改）
                    for seg in diarization_segments:
                        old_sp = seg.get("speaker")
                        if old_sp in merge_map:
                            seg["speaker"] = merge_map[old_sp]
                    
                    # 从 embeddings 中移除被合并的 speaker
                    for merged_sp in merge_map:
                        if merged_sp in speaker_embeddings:
                            del speaker_embeddings[merged_sp]
                    
                    print(f"🎯 [LOG] 聚类修正完成，合并了 {len(merge_map)} 个重复发言人，当前剩余 {len(speaker_embeddings)} 个独立发言人")
            
            return speaker_embeddings

        except Exception as e:
            print(f"⚠️ [LOG 警告] 提取声纹特征特征时出错: {e}")
            return {}

    def cluster_segments_to_paragraphs(self, podcast_id: str, segments: list[dict]) -> list[dict]:
        import json
        if not segments:
            return []
        
        # 1. 规则层 (Rule-based clustering with length constraints)
        clustered = []
        current_cluster = {
            "speaker": segments[0].get("speaker", "UNKNOWN_SPEAKER"),
            "texts": [segments[0].get("text", "")],
            "start": segments[0].get("start", 0.0),
            "end": segments[0].get("end", 0.0),
            "segments": [segments[0]]
        }
        
        sentence_endings = {"。", "！", "？", ".", "!", "?", "”", "\"", "」", "；", ";"}
        
        for seg in segments[1:]:
            seg_speaker = seg.get("speaker", "UNKNOWN_SPEAKER")
            seg_text = seg.get("text", "")
            seg_start = seg.get("start", 0.0)
            seg_end = seg.get("end", 0.0)
            
            # Calculate current cumulative character length
            current_len = sum(len(t) for t in current_cluster["texts"])
            
            # Check if we should split the paragraph
            should_split = False
            
            # Condition 1: Speaker changed
            if seg_speaker != current_cluster["speaker"]:
                should_split = True
            # Condition 2: Time gap between segments is too large (>= 1.2 seconds)
            elif (seg_start - current_cluster["end"]) >= 1.2:
                should_split = True
            # Condition 3: Paragraph is already long, split on next sentence ending
            elif current_len >= 220:
                last_text = current_cluster["texts"][-1].strip()
                if last_text and last_text[-1] in sentence_endings:
                    should_split = True
                # Condition 4: Hard limit to prevent extremely long paragraphs
                elif current_len >= 320:
                    should_split = True
            
            if not should_split:
                current_cluster["texts"].append(seg_text)
                current_cluster["end"] = seg_end
                current_cluster["segments"].append(seg)
            else:
                clustered.append(current_cluster)
                current_cluster = {
                    "speaker": seg_speaker,
                    "texts": [seg_text],
                    "start": seg_start,
                    "end": seg_end,
                    "segments": [seg]
                }
        clustered.append(current_cluster)
        
        # Convert texts to a single string and retain sentence list
        paragraphs = []
        for idx, cl in enumerate(clustered):
            raw_content = "".join(cl["texts"]) if any(ord(c) > 127 for c in "".join(cl["texts"])) else " ".join(cl["texts"])
            
            # Build list of original sentences
            sentences_list = []
            for s in cl["segments"]:
                sentences_list.append({
                    "text": s.get("text", ""),
                    "start": round(s.get("start", 0.0), 2),
                    "end": round(s.get("end", 0.0), 2)
                })
                
            paragraphs.append({
                "id": f"{podcast_id}-p{idx}",
                "podcast_id": podcast_id,
                "speaker": cl["speaker"],
                "content": raw_content.strip(),
                "start_time": round(cl["start"], 2),
                "end_time": round(cl["end"], 2),
                "sentences": sentences_list
            })
            
        # 2. LLM 语义缝合 (Optional LLM Sewing)
        from app.config import config
        enable_llm_sewing = config.get("enable_llm_semantic_sewing", False)
        
        if enable_llm_sewing and len(paragraphs) > 0:
            print(f"🤖 [LOG] 启动 LLM 语义段落缝合，共 {len(paragraphs)} 个初步段落...")
            try:
                # To prevent overloading LLM context and avoid timeout, we batch calls (e.g. 20 paragraphs per batch)
                batch_size = 20
                for i in range(0, len(paragraphs), batch_size):
                    batch = paragraphs[i:i+batch_size]
                    
                    # Prepare input JSON
                    llm_input = [{"index": idx, "speaker": p["speaker"], "raw_content": p["content"]} for idx, p in enumerate(batch)]
                    
                    prompt = f"""你是一个专业的速记文本整理助手。
下面是一份播客转录的初步拼接段落列表（以 JSON 数组形式给出，每个元素包含 index、speaker 和 raw_content）。
请在【绝对不改变、不添加、不删减任何原字词】的前提下，对每个段落进行“语义缝合”：
1. 仅理顺标点符号，将口语中的语气词或停顿转换为合适的标点（如逗号、句号、问号、叹号）。
2. 确保绝对不改变任何原文的字词顺序或内容，不添加解释性文字，也不要合并不同的 index 段落。
3. 【关键】如果发现原 speaker 为 'UNKNOWN_SPEAKER'，请根据上下文语境（如问答、陈述、语气风格），推断出最合适的讲话人角色（例如：主持人、嘉宾A、嘉宾B 等），如果无法推断，请保留原样。
4. 输出格式必须为标准的 JSON 数组，每个元素包含 index（数字）、speaker（字符串）和 sewn_content（缝合后的段落内容文本）字段，与输入的 index 一一对应。

输入：
{json.dumps(llm_input, ensure_ascii=False, indent=2)}

请直接输出 JSON 数组内容，不要包含 ```json 或 ``` 格式块，不要包含任何 markdown 语法或前言后语。"""

                    sewn_json_str = self._call_llm(prompt)
                    
                    # Try to parse the output
                    # Strip code blocks if LLM still included them
                    cleaned_str = sewn_json_str.strip()
                    if cleaned_str.startswith("```json"):
                        cleaned_str = cleaned_str[7:]
                    if cleaned_str.startswith("```"):
                        cleaned_str = cleaned_str[3:]
                    if cleaned_str.endswith("```"):
                        cleaned_str = cleaned_str[:-3]
                    cleaned_str = cleaned_str.strip()
                    
                    try:
                        sewn_results = json.loads(cleaned_str)
                        for item in sewn_results:
                            idx = item.get("index")
                            content = item.get("sewn_content")
                            inferred_speaker = item.get("speaker")
                            if idx is not None and 0 <= idx < len(batch) and content:
                                batch[idx]["content"] = content
                                if inferred_speaker:
                                    batch[idx]["speaker"] = inferred_speaker
                        print(f"✅ [LOG] 批量语义缝合与角色推理成功 (段落 {i} 到 {i+len(batch)})")
                    except Exception as parse_err:
                        print(f"⚠️ [LOG] 解析 LLM 语义缝合输出失败: {parse_err}，此批次将保留原始规则拼接内容。")
                        print(f"原始输出: {sewn_json_str[:300]}...")
            except Exception as llm_err:
                print(f"❌ [LOG] 语义段落缝合出错: {llm_err}，系统自动降级回纯规则拼接模式。")
                
        return paragraphs

    def _call_llm(self, prompt: str) -> str:
        from app.config import config
        import httpx
        
        summary_mode = config.get("summary_mode", "local")
        if summary_mode == "online":
            api_key = config.get("online_summary_api_key", "").strip()
            base_url = config.get("online_summary_base_url", "https://api.openai.com/v1").strip()
            target_model = config.get("online_summary_model", "gpt-4o-mini").strip()
            api_url = f"{base_url.rstrip('/')}/chat/completions"
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
        else:
            ollama_url = config.get("ollama_url", "http://localhost:11434").strip()
            target_model = config.get("ollama_model", "qwen2.5:7b-instruct").strip()
            base_url = ollama_url.rstrip('/')
            api_url = f"{base_url}/v1/chat/completions" if '/v1' not in base_url else f"{base_url}/chat/completions"
            headers = {"Content-Type": "application/json"}
            
        payload = {
            "model": target_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "temperature": 0.1
        }
        
        response = None
        # 1. 优先使用系统代理
        try:
            with httpx.Client(timeout=120.0, trust_env=True) as client:
                response = client.post(api_url, json=payload, headers=headers)
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e_proxy:
            print(f"⚠️ [LOG] LLM 语义缝合接口代理请求失败: {e_proxy}。尝试直连...")
            
        # 2. 直连兜底 (结合 DoH 绕过)
        try:
            with doh_dns_bypass(api_url):
                with httpx.Client(timeout=120.0, trust_env=False) as client:
                    response = client.post(api_url, json=payload, headers=headers)
                    if response.status_code == 200:
                        result = response.json()
                        return result["choices"][0]["message"]["content"].strip()
        except Exception as e_doh:
            print(f"❌ [LOG] LLM 语义缝合直连(DoH DNS 绕过)请求失败: {e_doh}")
            
        if response is None or response.status_code != 200:
            detail_msg = response.text if response is not None else "无响应"
            status_code = response.status_code if response is not None else "未知"
            raise Exception(f"LLM API error (code {status_code}): {detail_msg}")
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()


