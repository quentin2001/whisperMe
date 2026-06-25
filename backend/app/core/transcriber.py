import os
import sys
import re
import socket
import threading
import time
import httpx
from app.config import (
    config,
    SHORT_LOCAL_WHISPER_MODEL_PATH,
    HF_TOKEN,
    get_short_path_name,
    FFMPEG_PATH
)
from app.core.network import doh_dns_bypass


class ModelCacheManager:
    def __init__(self):
        self.cached_model = None
        self.model_path = None
        self.device = None
        self.compute_type = None
        self.last_used_time = 0.0
        self.lock = threading.Lock()
        self._watcher_thread = None
        self.running = False

    def start_watcher(self):
        with self.lock:
            if self.running:
                return
            self.running = True
            self._watcher_thread = threading.Thread(target=self._watch_idle, daemon=True)
            self._watcher_thread.start()
            print("⚙️ [LOG] WhisperModel VRAM/内存闲置回收监控线程已启动。")

    def _watch_idle(self):
        while self.running:
            time.sleep(10)
            with self.lock:
                if self.cached_model is not None:
                    timeout = int(config.get("local_model_idle_timeout", 300))
                    if time.time() - self.last_used_time > timeout:
                        print(f"🧹 [LOG] WhisperModel 闲置超时 ({timeout}s)，自动释放显存/内存...")
                        self.cached_model = None
                        self.model_path = None
                        self.device = None
                        self.compute_type = None
                        
                        import gc
                        import sys
                        gc.collect()
                        if 'torch' in sys.modules:
                            import torch
                            if torch.cuda.is_available():
                                torch.cuda.empty_cache()
                                print("🧹 [LOG] 已清空 PyTorch CUDA 显存缓存")

    def get_model(self, model_path_or_size: str, device: str, compute_type: str):
        self.start_watcher()
        with self.lock:
            if (self.cached_model is not None and 
                self.model_path == model_path_or_size and 
                self.device == device and 
                self.compute_type == compute_type):
                print("🎯 [LOG] 命中 WhisperModel 内存常驻缓存，复用已有实例！")
                self.last_used_time = time.time()
                return self.cached_model

            print(f"🚀 [LOG] 正在加载 Whisper 模型: {model_path_or_size} (设备: {device.upper()} | 精度: {compute_type})")
            from faster_whisper import WhisperModel

            # CPU 模式下优化 CTranslate2 线程参数
            model_kwargs = dict(
                device=device,
                compute_type=compute_type,
            )
            if device == "cpu":
                model_kwargs["cpu_threads"] = 6  # R5 5600 物理核心数，通用甜点值
                model_kwargs["num_workers"] = 1

            try:
                # 尝试以 local_files_only=True 加载本地配置路径
                model = WhisperModel(
                    model_path_or_size,
                    **model_kwargs,
                    local_files_only=True
                )
            except Exception as e:
                # 如果失败，可能是 HuggingFace model 标识符，尝试在线加载
                print(f"⚠️ [LOG] 从本地加载模型失败: {e}。尝试从 Hugging Face 在线下载并载入...")
                model = WhisperModel(
                    model_path_or_size,
                    **model_kwargs,
                    local_files_only=False
                )

            self.cached_model = model
            self.model_path = model_path_or_size
            self.device = device
            self.compute_type = compute_type
            self.last_used_time = time.time()
            return model

model_cache_manager = ModelCacheManager()


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
        # 自适应精度策略：基于 GPU 总显存（不是 free）智能选择 compute_type
        if self.device == "cuda":
            try:
                import torch
                free_bytes, total_bytes = torch.cuda.mem_get_info()
                total_gb = total_bytes / (1024 ** 3)
                if total_gb >= 10:
                    self.compute_type = "float16"
                elif total_gb >= 4:
                    self.compute_type = "int8_float16"  # RTX 3070 8GB 甜点值
                else:
                    self.compute_type = "int8"
                print(f"🖥️ [LOG] GPU 总显存: {total_gb:.1f}GB → compute_type={self.compute_type}")
            except Exception:
                self.compute_type = "float16"  # 无法检测时保守选择
        else:
            self.compute_type = "int8"  # CPU 上用 INT8 加速
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

    def _find_speaker(self, seg, diarization_segments: list[dict]) -> str:
        """Match a transcript segment to the closest diarization speaker."""
        if not diarization_segments:
            return "UNKNOWN_SPEAKER"

        seg_center = (seg.start + seg.end) / 2
        best_match = None
        max_overlap = 0.0

        for d in diarization_segments:
            # Exact center containment
            if d["start"] <= seg_center <= d["end"]:
                return d["speaker"]
            # Fallback: highest overlap
            overlap_start = max(seg.start, d["start"])
            overlap_end = min(seg.end, d["end"])
            overlap_len = overlap_end - overlap_start
            if overlap_len > max_overlap:
                max_overlap = overlap_len
                best_match = d["speaker"]

        return best_match or "UNKNOWN_SPEAKER"

    def transcribe_and_merge(self, wav_path: str, diarization_segments: list[dict],
                             progress_callback=None, asr_mode: str = "local",
                             on_segment_batch=None) -> list[dict]:
        """
        运行 faster-whisper 或在线 ASR，并将识别的段落与 pyannote 声纹时间轴交叉重叠合并
        """
        merged_results = []
        last_progress_int = 60

        if asr_mode == "online":
            from app.config import config
            from app.core.asr_providers import get_provider

            provider_name = config.get("online_asr_provider", "mimo")
            provider = get_provider(provider_name)

            print(f"[LOG] Using online ASR provider: {provider.get_display_name()} ({provider_name})")

            # Provider handles chunking, API calls, and response parsing
            # Returns standardized format: [{"start": float, "end": float, "text": str}]
            provider_segments = provider.transcribe(wav_path, diarization_segments, progress_callback)

            # Convert to WhisperSegmentDummy for downstream compatibility
            whisper_segments = []
            for seg in provider_segments:
                whisper_segments.append(WhisperSegmentDummy(seg["start"], seg["end"], seg["text"]))

            # Calculate duration
            if whisper_segments:
                duration = max(seg.end for seg in whisper_segments)
            else:
                import wave as _wave
                try:
                    with _wave.open(wav_path, "rb") as w:
                        duration = w.getnframes() / float(w.getframerate())
                except Exception:
                    duration = 1.0

            print(f"[LOG] Online ASR completed: {len(whisper_segments)} segments.")

            # Online ASR: merge with diarization and batch callback
            batch_buffer = []
            for seg in whisper_segments:
                current_speaker = self._find_speaker(seg, diarization_segments)

                start_min, start_sec = divmod(int(seg.start), 60)
                start_hour, start_min = divmod(start_min, 60)
                timestamp = f"[{start_hour:02d}:{start_min:02d}:{start_sec:02d}]"

                merged_seg = {
                    "start": seg.start,
                    "end": seg.end,
                    "timestamp_str": timestamp,
                    "speaker": current_speaker,
                    "text": seg.text
                }
                merged_results.append(merged_seg)
                batch_buffer.append(merged_seg)

                if on_segment_batch and len(batch_buffer) >= 10:
                    try:
                        on_segment_batch(list(batch_buffer))
                    except Exception as batch_ex:
                        print(f"⚠️ [LOG] Incremental paragraph batch failed: {batch_ex}")
                    batch_buffer = []

            if on_segment_batch and batch_buffer:
                try:
                    on_segment_batch(list(batch_buffer))
                except Exception as batch_ex:
                    print(f"⚠️ [LOG] Final paragraph batch failed: {batch_ex}")

            # Progress callback for online mode
            if progress_callback:
                try:
                    progress_callback(75.0)
                except Exception:
                    pass

            print("="*50 + f"\n🎉 [LOG] 转录与声纹角色合并工作顺利完成！共识别出 {len(merged_results)} 段对话。")
            return merged_results

        else:
            # 本地转录模式
            short_wav_path = get_short_path_name(os.path.abspath(wav_path))
            import torch

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

            # 解析选定的本地模型大小规格
            MODEL_SIZE_MAPPING = {
                "large-v3": "Systran/faster-whisper-large-v3",
                "large-v3-turbo": "Systran/faster-whisper-large-v3-turbo",
                "medium": "Systran/faster-whisper-medium",
                "small": "Systran/faster-whisper-small",
            }
            model_size = config.get("local_whisper_model_size", "large-v3")
            model_path_or_size = SHORT_LOCAL_WHISPER_MODEL_PATH
            if not model_path_or_size or not os.path.exists(model_path_or_size):
                model_path_or_size = MODEL_SIZE_MAPPING.get(model_size, model_size)

            model = model_cache_manager.get_model(
                model_path_or_size,
                device=device_to_use,
                compute_type=compute_type_to_use
            )

            print("✨ [LOG] Whisper 模型已就绪！开始高效转汉字...")
            whisper_segments_raw, info = model.transcribe(
                short_wav_path,
                beam_size=5,
                language="zh",
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 500},
            )

            # 过滤相邻重复句，防止本地 Whisper 幻觉循环
            def clean_txt(text):
                return re.sub(r'[^\w\s]', '', text).strip()

            dedup_prev_text = ""
            duration = info.duration if info and info.duration else 1.0
            batch_buffer = []

            for seg in whisper_segments_raw:
                # Adjacent deduplication
                cleaned = clean_txt(seg.text)
                if cleaned == dedup_prev_text:
                    if merged_results:
                        merged_results[-1]["end"] = seg.end
                    continue
                dedup_prev_text = cleaned

                # Speaker matching via helper
                current_speaker = self._find_speaker(seg, diarization_segments)

                # Timestamp
                start_min, start_sec = divmod(int(seg.start), 60)
                start_hour, start_min = divmod(start_min, 60)
                timestamp = f"[{start_hour:02d}:{start_min:02d}:{start_sec:02d}]"

                merged_seg = {
                    "start": seg.start,
                    "end": seg.end,
                    "timestamp_str": timestamp,
                    "speaker": current_speaker,
                    "text": seg.text
                }
                merged_results.append(merged_seg)
                batch_buffer.append(merged_seg)

                # Incremental batch callback every 10 segments
                if on_segment_batch and len(batch_buffer) >= 10:
                    try:
                        on_segment_batch(list(batch_buffer))
                    except Exception as batch_ex:
                        print(f"⚠️ [LOG] Incremental paragraph batch failed: {batch_ex}")
                    batch_buffer = []

                # Progress update
                current_progress = 60.0 + (seg.end / max(duration, 1.0)) * 15.0
                current_progress = min(current_progress, 75.0)
                current_progress_int = int(current_progress)
                if current_progress_int > last_progress_int:
                    last_progress_int = current_progress_int
                    if progress_callback:
                        try:
                            progress_callback(float(current_progress_int))
                        except Exception as pe:
                            print(f"⚠️ [LOG] 进度回调触发异常: {pe}")

            # Flush remaining segments
            if on_segment_batch and batch_buffer:
                try:
                    on_segment_batch(list(batch_buffer))
                except Exception as batch_ex:
                    print(f"⚠️ [LOG] Final paragraph batch failed: {batch_ex}")

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

    def cluster_segments_to_paragraphs(self, podcast_id: str, segments: list[dict], id_offset: int = 0) -> list[dict]:
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
                "id": f"{podcast_id}-p{id_offset + idx}",
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


