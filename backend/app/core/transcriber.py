import os
import sys
import torch
import subprocess
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
from app.config import (
    SHORT_LOCAL_WHISPER_MODEL_PATH, 
    HF_TOKEN, 
    get_short_path_name,
    FFMPEG_PATH
)


class WhisperSegmentDummy:
    def __init__(self, start, end, text):
        self.start = start
        self.end = end
        self.text = text


class PodcastTranscriber:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.compute_type = "float16" if self.device == "cuda" else "float32"
        print(f"🖥️ [LOG] 初始化转录引擎 - 运行设备: {self.device.upper()} | 运算精度: {self.compute_type}")

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

            # 2. 分片处理逻辑 (每片最大 10 分钟 = 600 秒)
            chunk_length = 600.0
            num_chunks = math.ceil(audio_duration / chunk_length)
            
            for i in range(num_chunks):
                start_offset = i * chunk_length
                slice_duration = min(chunk_length, audio_duration - start_offset)
                if slice_duration <= 0.1:
                    continue

                chunk_mp3_path = wav_path.replace(".wav", f"_chunk_{i}.mp3")
                print(f"✂️ [LOG] 正在提取分片 {i+1}/{num_chunks}: 从 {start_offset:.2f}s 开始，时长 {slice_duration:.2f}s...")

                try:
                    # 使用 FFmpeg 提取对应分片并压缩为 32kbps mono MP3
                    cmd = [
                        FFMPEG_PATH, 
                        '-y', 
                        '-ss', str(start_offset),
                        '-t', str(slice_duration),
                        '-i', get_short_path_name(wav_path), 
                        '-codec:a', 'libmp3lame', 
                        '-b:a', '32k', 
                        '-ac', '1', 
                        get_short_path_name(chunk_mp3_path)
                    ]
                    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if res.returncode != 0 or not os.path.exists(chunk_mp3_path):
                        raise Exception(f"FFmpeg slice creation failed for chunk {i}: {res.stderr.decode('utf-8', errors='ignore')}")

                    print(f"🎛️ [LOG] 分片 {i+1} 成功生成并压缩 ({os.path.getsize(chunk_mp3_path) / (1024*1024):.2f} MB)")

                    # 转换为 Base64
                    with open(chunk_mp3_path, "rb") as f:
                        audio_base_64 = "data:audio/mp3;base64," + base64.b64encode(f.read()).decode("utf-8")

                    # 物理清理临时分片 MP3 文件
                    try:
                        os.remove(chunk_mp3_path)
                        print(f"🗑️ [LOG] 已物理清理分片临时文件: {chunk_mp3_path}")
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
                    with httpx.Client(timeout=400.0, trust_env=False) as client:
                        response = client.post(url, headers=headers, json=payload)
                        
                    if response.status_code != 200:
                        raise Exception(f"在线 ASR API 调用失败，状态码: {response.status_code}。详情: {response.text}")
                        
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

                    total_chars = sum(len(s) for s in sentences)
                    if total_chars == 0:
                        total_chars = 1

                    current_chunk_time = 0.0
                    for s in sentences:
                        char_len = len(s)
                        duration_ratio = char_len / total_chars
                        s_duration = duration_ratio * slice_duration
                        start = start_offset + current_chunk_time
                        end = start_offset + current_chunk_time + s_duration
                        
                        whisper_segments.append(WhisperSegmentDummy(start, end, s))
                        current_chunk_time += s_duration

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
            duration = info.duration if info and info.duration else 1.0
        
        has_diarization = len(diarization_segments) > 0
        merged_results = []
        
        print("\n🎧 【实时瀑布流剧本输出展示开始】\n" + "="*50)
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
            
            print(line)  # 控制台实时回显
            
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
        Extract representative 512-dimensional voice embeddings for each unique speaker
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
                
                # We extract embedding from the longest segment (minimum 1.5 seconds)
                best_seg = None
                for seg in sp_segs:
                    duration = seg["end"] - seg["start"]
                    if duration >= 1.5:
                        best_seg = seg
                        break
                else:
                    best_seg = sp_segs[0]  # fallback to longest segment even if short
                
                start = best_seg["start"]
                end = best_seg["end"]
                # Limit duration to max 15 seconds to keep it fast
                if end - start > 15.0:
                    end = start + 15.0
                    
                print(f"⏳ [LOG] 正在提取 {speaker} 的声纹特征 (时间轴: {start:.2f}s - {end:.2f}s)...")
                emb = inference.crop(wav_path, Segment(start, end))
                
                # Convert embedding numpy array to list of floats
                if isinstance(emb, np.ndarray):
                    # Normalize vector
                    norm = np.linalg.norm(emb)
                    if norm > 0:
                        emb = emb / norm
                    speaker_embeddings[speaker] = emb.tolist()
                    
            print(f"🟢 [LOG] 成功完成 {len(speaker_embeddings)} 个发言人的声纹特征提取！")
            return speaker_embeddings

        except Exception as e:
            print(f"⚠️ [LOG 警告] 提取声纹特征特征时出错: {e}")
            return {}

