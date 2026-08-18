import os
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
import sys
import re
import socket
import threading
import time
import httpx
import subprocess
import shutil
from typing import Dict, List, Optional
import traceback
from app.core import logger
from app.config import (
    config,
    SHORT_LOCAL_WHISPER_MODEL_PATH,
    HF_TOKEN,
    get_short_path_name,
    FFMPEG_PATH,
    PROJECT_DIR
)
from app.core.network import doh_dns_bypass


def clean_sensevoice_text(text: str) -> str:
    """
    清洗 SenseVoice 输出的富文本标签，返回纯净逐字稿文本。
    - 移除 <|zh|>, <|HAPPY|>, <|Speech|>, <|withitn|> 等内部标记
    - 移除占位符 (如 'The.')
    - 规范化多余空白
    """
    if not text:
        return ""
    # 移除 <|...|> 特殊 token
    t = re.sub(r"<\|[^\>]+?\|>", "", text)
    # 移除模型占位符
    t = t.replace("The.", "")
    # 规范化连续空格
    return re.sub(r"[ \t]+", " ", t).strip()


def detect_funasr_model_type(model_path_or_name: str) -> str:
    """
    判断 FunASR 模型类别: 'sensevoice' 或 'paraformer'
    """
    if not model_path_or_name:
        return "paraformer"

    path_str = str(model_path_or_name)
    path_lower = path_str.lower().replace("\\", "/")
    if "sensevoice" in path_lower:
        return "sensevoice"

    if os.path.isdir(path_str):
        if os.path.exists(os.path.join(path_str, "chn_jpn_yue_eng_ko_spectok.bpe.model")) or os.path.exists(os.path.join(path_str, "am.mvn")):
            return "sensevoice"
        for root, dirs, files in os.walk(path_str):
            if any("sensevoice" in d.lower() for d in dirs):
                return "sensevoice"
            if "chn_jpn_yue_eng_ko_spectok.bpe.model" in files:
                return "sensevoice"
            break

    return "paraformer"


class ModelCacheManager:
    def __init__(self):
        self.cached_model = None
        self.model_path = None
        self.device = None
        self.compute_type = None
        self.last_used_time = 0.0
        
        self.pyannote_diarization = None
        self.pyannote_embedding = None
        self.funasr_model = None
        self.funasr_model_type = None
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
            pass

    def _watch_idle(self):
        while self.running:
            time.sleep(10)
            with self.lock:
                if self.cached_model is not None:
                    timeout = int(config.get("local_model_idle_timeout", 300))
                    if time.time() - self.last_used_time > timeout:
                        pass
                        self.cached_model = None
                        self.model_path = None
                        self.device = None
                        self.compute_type = None
                        
                        self.pyannote_diarization = None
                        self.pyannote_embedding = None
                        self.funasr_model = None
                        self.funasr_model_type = None
                        
                        import gc
                        import sys
                        gc.collect()
                        if 'torch' in sys.modules:
                            import torch
                            if torch.cuda.is_available():
                                torch.cuda.empty_cache()
                                pass

    def get_model(self, model_path_or_size: str, device: str, compute_type: str):
        actual_device = "cpu" if device == "mps" else device
        self.start_watcher()
        with self.lock:
            if (self.cached_model is not None and 
                self.model_path == model_path_or_size and 
                self.device == actual_device and 
                self.compute_type == compute_type):
                pass
                self.last_used_time = time.time()
                return self.cached_model

            print("⏩ 正在加载 Whisper 模型进行语音转录...")
            from faster_whisper import WhisperModel

            # CPU 模式下优化 CTranslate2 线程参数
            model_kwargs = dict(
                device=actual_device,
                compute_type=compute_type,
            )
            if actual_device == "cpu":
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
            self.device = actual_device
            self.compute_type = compute_type
            self.last_used_time = time.time()
            return model

    def get_pyannote_diarization(self, device: str):
        self.start_watcher()
        with self.lock:
            if self.pyannote_diarization is not None:
                pass
                self.last_used_time = time.time()
                import torch
                self.pyannote_diarization.to(torch.device(device))
                return self.pyannote_diarization
            
            pass
            import torch
            from pyannote.audio import Pipeline
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1", 
                use_auth_token=HF_TOKEN
            )
            pipeline.to(torch.device(device))
            self.pyannote_diarization = pipeline
            self.last_used_time = time.time()
            return pipeline

    def get_pyannote_embedding(self, device: str):
        self.start_watcher()
        with self.lock:
            if self.pyannote_embedding is not None:
                pass
                self.last_used_time = time.time()
                import torch
                # Embedding model's Inference object wraps the Model, we recreate Inference later
                # We just cache the Model
                return self.pyannote_embedding
                
            pass
            from pyannote.audio import Model
            model = Model.from_pretrained("pyannote/embedding", use_auth_token=HF_TOKEN)
            self.pyannote_embedding = model
            self.last_used_time = time.time()
            return model
            
    def get_funasr_model(self, device: str):
        self.start_watcher()
        with self.lock:
            custom_path = config.get("local_whisper_model_path", "")
            models_dir = os.path.join(PROJECT_DIR, "models", "funasr")
            os.environ["MODELSCOPE_CACHE"] = models_dir

            # 智能检测模型类别 ('sensevoice' 或 'paraformer')
            model_type = detect_funasr_model_type(custom_path)

            if self.funasr_model is not None and getattr(self, "funasr_model_type", None) == model_type:
                self.last_used_time = time.time()
                return self.funasr_model, model_type
            
            from funasr import AutoModel

            if device == "cuda":
                device_str = "cuda:0"
            elif device == "mps":
                device_str = "mps"
            else:
                device_str = "cpu"

            if model_type == "sensevoice":
                # SenseVoice 专用解析逻辑（内聚标点，无需外挂 punc）
                sv_model = "iic/SenseVoiceSmall"
                if custom_path:
                    custom_path_abs = custom_path if os.path.isabs(custom_path) else os.path.abspath(os.path.join(PROJECT_DIR, custom_path))
                    if os.path.isdir(custom_path_abs):
                        if os.path.exists(os.path.join(custom_path_abs, "configuration.json")) or os.path.exists(os.path.join(custom_path_abs, "model.pt")):
                            sv_model = custom_path_abs
                        else:
                            nested_sv = os.path.join(custom_path_abs, "iic", "SenseVoiceSmall")
                            if os.path.exists(nested_sv) and os.path.isdir(nested_sv):
                                sv_model = nested_sv
                    else:
                        sv_model = custom_path
                else:
                    default_sv1 = os.path.join(PROJECT_DIR, "models", "SenseVoiceSmall")
                    default_sv2 = os.path.join(models_dir, "iic", "SenseVoiceSmall")
                    if os.path.exists(default_sv1) and os.path.isdir(default_sv1):
                        sv_model = default_sv1
                    elif os.path.exists(default_sv2) and os.path.isdir(default_sv2):
                        sv_model = default_sv2

                local_vad_dir = os.path.join(models_dir, "iic", "speech_fsmn_vad_zh-cn-16k-common-pytorch")
                vad_param = local_vad_dir if (os.path.exists(local_vad_dir) and os.path.isdir(local_vad_dir)) else "fsmn-vad"

                print(f"⏩ [LOG] 正在加载 FunASR SenseVoiceSmall 模型: {sv_model}")
                try:
                    model = AutoModel(
                        model=sv_model,
                        vad_model=vad_param,
                        vad_kwargs={"max_single_segment_time": 30000},
                        device=device_str,
                        disable_update=True,
                        hub="ms"
                    )
                except Exception as ms_ex:
                    model = AutoModel(
                        model=sv_model,
                        vad_model="fsmn-vad",
                        vad_kwargs={"max_single_segment_time": 30000},
                        device=device_str,
                        disable_update=True,
                        hub="hf"
                    )
            else:
                # Paraformer 默认加载逻辑 (保持原有完全向后兼容)
                ms_model = "iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
                hf_model = "funasr/paraformer-zh"
                
                local_ms_model_dir = os.path.join(models_dir, "iic", "speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch")
                local_vad_dir = os.path.join(models_dir, "iic", "speech_fsmn_vad_zh-cn-16k-common-pytorch")
                local_punc_dir = os.path.join(models_dir, "iic", "punc_ct-transformer_cn-en-common-vocab471067-large")
                
                vad_param = "fsmn-vad"
                punc_param = "ct-punc"
                
                if custom_path:
                    custom_path_abs = custom_path if os.path.isabs(custom_path) else os.path.abspath(os.path.join(PROJECT_DIR, custom_path))
                    if os.path.isdir(custom_path_abs):
                        if os.path.exists(os.path.join(custom_path_abs, "configuration.json")) or os.path.exists(os.path.join(custom_path_abs, "model.onnx")):
                            ms_model = custom_path_abs
                            hf_model = custom_path_abs
                        else:
                            potential_ms = os.path.join(custom_path_abs, "iic", "speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch")
                            if os.path.exists(potential_ms) and os.path.isdir(potential_ms):
                                ms_model = potential_ms
                                potential_vad = os.path.join(custom_path_abs, "iic", "speech_fsmn_vad_zh-cn-16k-common-pytorch")
                                if os.path.exists(potential_vad) and os.path.isdir(potential_vad):
                                    vad_param = potential_vad
                                potential_punc = os.path.join(custom_path_abs, "iic", "punc_ct-transformer_cn-en-common-vocab471067-large")
                                if os.path.exists(potential_punc) and os.path.isdir(potential_punc):
                                    punc_param = potential_punc
                            else:
                                ms_model = custom_path
                                hf_model = custom_path
                    else:
                        if "paraformer" in custom_path.lower():
                            if os.path.exists(local_ms_model_dir) and os.path.isdir(local_ms_model_dir):
                                ms_model = local_ms_model_dir
                            if os.path.exists(local_vad_dir) and os.path.isdir(local_vad_dir):
                                vad_param = local_vad_dir
                            if os.path.exists(local_punc_dir) and os.path.isdir(local_punc_dir):
                                punc_param = local_punc_dir
                        else:
                            ms_model = custom_path
                            hf_model = custom_path
                else:
                    if os.path.exists(local_ms_model_dir) and os.path.isdir(local_ms_model_dir):
                        ms_model = local_ms_model_dir
                    if os.path.exists(local_vad_dir) and os.path.isdir(local_vad_dir):
                        vad_param = local_vad_dir
                    if os.path.exists(local_punc_dir) and os.path.isdir(local_punc_dir):
                        punc_param = local_punc_dir

                print(f"⏩ [LOG] 正在加载 FunASR Paraformer 模型: {ms_model}")
                try:
                    model = AutoModel(model=ms_model, model_revision="v2.0.4",
                                      vad_model=vad_param, vad_model_revision="v2.0.4",
                                      punc_model=punc_param, punc_model_revision="v2.0.4",
                                      device=device_str, disable_update=True, hub="ms")
                except Exception as ms_ex:
                    model = AutoModel(model=hf_model, model_revision="v2.0.4",
                                      vad_model="fsmn-vad", vad_model_revision="v2.0.4",
                                      punc_model="ct-punc", punc_model_revision="v2.0.4",
                                      device=device_str, disable_update=True, hub="hf")

            self.funasr_model = model
            self.funasr_model_type = model_type
            self.last_used_time = time.time()
            return model, model_type
            
    def preload_models(self):
        if config.get("preload_models", True):
            if HF_TOKEN and len(HF_TOKEN) >= 30:
                pass
                try:
                    self.get_pyannote_diarization("cpu")
                    self.get_pyannote_embedding("cpu")
                    pass
                except Exception as e:
                    pass

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
        if sys.platform == "darwin":
            try:
                import torch
                if torch.backends.mps.is_available():
                    self.device = "mps"
            except Exception:
                pass
        else:
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
                pass
            except Exception:
                self.compute_type = "float16"  # 无法检测时保守选择
        else:
            self.compute_type = "int8"  # CPU 上用 INT8 加速
        pass

    def run_diarization_and_embedding(self, wav_path: str) -> tuple[list[dict], dict[str, list[float]]]:
        """
        运行 pyannote.audio 进行声纹识别与说话人分割，并在同一批次直接从内存中提取特征向量
        """
        # 对路径进行短路径安全处理，防御 C++ 库路径崩溃
        short_wav_path = get_short_path_name(os.path.abspath(wav_path))
        
        # 验证 Hugging Face Token 长度是否合理
        if not HF_TOKEN or len(HF_TOKEN) < 30:
            pass
            return [], {}

        try:
            import torch
            import torchaudio
            from pyannote.audio import Pipeline, Inference
            from pyannote.core import Segment
            import numpy as np
            
            # 直接将音频加载到内存，避免后续二次读取
            waveform, sample_rate = torchaudio.load(short_wav_path)
            audio_in_memory = {"waveform": waveform, "sample_rate": sample_rate}
            
            # 动态可用显存监控，实现硬件级别的热熔断 CPU 降级机制
            device_to_use = self.device
            if device_to_use == "cuda":
                try:
                    free_mem, total_mem = torch.cuda.mem_get_info()
                    free_gb = free_mem / (1024 ** 3)
                    total_gb = total_mem / (1024 ** 3)
                    pass
                    if free_gb < 1.5:
                        pass
                        device_to_use = "cpu"
                except Exception as mem_ex:
                    pass

            pipeline = model_cache_manager.get_pyannote_diarization(device_to_use)
            
            pass
            diarization = pipeline(audio_in_memory)
            
            diarization_list = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                diarization_list.append({
                    "start": turn.start, 
                    "end": turn.end, 
                    "speaker": speaker
                })
                
            unique_speakers = set([d["speaker"] for d in diarization_list])
            pass
            
            # 立即在内存中进行特征提取
            speaker_embeddings = {}
            if unique_speakers:
                pass
                emb_model = model_cache_manager.get_pyannote_embedding(device_to_use)
                inference = Inference(emb_model, window="whole", device=torch.device(device_to_use))
                
                for speaker in unique_speakers:
                    sp_segs = [s for s in diarization_list if s.get("speaker") == speaker]
                    if not sp_segs:
                        continue
                        
                    sp_segs = sorted(sp_segs, key=lambda s: s["end"] - s["start"], reverse=True)
                    candidate_segs = [seg for seg in sp_segs if seg["end"] - seg["start"] >= 1.5][:5]
                    if not candidate_segs:
                        candidate_segs = [sp_segs[0]]
                        
                    embeddings_list = []
                    for seg in candidate_segs:
                        start = seg["start"]
                        end = min(seg["start"] + 10.0, seg["end"])
                        try:
                            emb = inference.crop(audio_in_memory, Segment(start, end))
                            if isinstance(emb, np.ndarray):
                                emb = np.nan_to_num(emb)
                                norm = np.linalg.norm(emb)
                                if norm > 0:
                                    embeddings_list.append(emb / norm)
                        except Exception as seg_ex:
                            pass
                            continue
                            
                    if embeddings_list:
                        avg_emb = np.mean(embeddings_list, axis=0)
                        norm = np.linalg.norm(avg_emb)
                        if norm > 0:
                            avg_emb = avg_emb / norm
                        speaker_embeddings[speaker] = avg_emb.tolist()
                        
                pass
                
                # ====== 单集内声纹聚类修正 ======
                if len(speaker_embeddings) >= 2:
                    merge_map = {}
                    sp_ids = sorted(speaker_embeddings.keys())
                    for i in range(len(sp_ids)):
                        if sp_ids[i] in merge_map: continue
                        for j in range(i + 1, len(sp_ids)):
                            if sp_ids[j] in merge_map: continue
                            emb_i = np.array(speaker_embeddings[sp_ids[i]])
                            emb_j = np.array(speaker_embeddings[sp_ids[j]])
                            norm_i = np.linalg.norm(emb_i)
                            norm_j = np.linalg.norm(emb_j)
                            if norm_i > 0 and norm_j > 0:
                                sim = np.dot(emb_i, emb_j) / (norm_i * norm_j)
                                if sim >= 0.92:
                                    merge_map[sp_ids[j]] = sp_ids[i]
                                    pass
                                    
                    if merge_map:
                        for seg in diarization_list:
                            if seg.get("speaker") in merge_map:
                                seg["speaker"] = merge_map[seg["speaker"]]
                        for merged_sp in merge_map:
                            if merged_sp in speaker_embeddings:
                                del speaker_embeddings[merged_sp]
                        pass

            # 清理内存中的音频
            del audio_in_memory
            del waveform
            import gc
            gc.collect()
            
            return diarization_list, speaker_embeddings
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            pass
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
            from app.config import config as _online_config
            from app.core.asr_providers import get_provider

            provider_name = _online_config.get("online_asr_provider", "mimo")
            provider = get_provider(provider_name)

            pass

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

            pass

            # Online ASR: merge with diarization and batch callback
            batch_buffer = []
            for seg in whisper_segments:
                current_speaker = self._find_speaker(seg, diarization_segments)

                # Generate timestamp with hour:minute:second (including fractional seconds)
                total_seconds = seg.start
                hour = int(total_seconds // 3600)
                minute = int((total_seconds % 3600) // 60)
                second = total_seconds % 60
                # Format seconds with two decimal places
                timestamp = f"[{hour:02d}:{minute:02d}:{second:05.2f}]"

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
                        pass
                    batch_buffer = []

            if on_segment_batch and batch_buffer:
                try:
                    on_segment_batch(list(batch_buffer))
                except Exception as batch_ex:
                    pass

            # Progress callback for online mode
            if progress_callback:
                try:
                    progress_callback(75.0)
                except Exception as pe:
                    if str(pe) == "TASK_CANCELLED":
                        raise pe

            print("✅ 语音识别转录成功完成！")
            return merged_results

        else:
            # 本地转录模式
            short_wav_path = get_short_path_name(os.path.abspath(wav_path))
            import torch
            
            device_to_use = self.device
            custom_path = config.get("local_whisper_model_path", "")
            is_whisper = False
            if custom_path and os.path.isdir(custom_path):
                # Faster-Whisper models contain model.bin and config.json
                if os.path.exists(os.path.join(custom_path, "model.bin")):
                    is_whisper = True

            asr_start_time = time.time()
            if is_whisper:
                print("⏩ 正在加载本地 Faster-Whisper 模型进行语音转录...")
                model = model_cache_manager.get_model(custom_path, device_to_use, self.compute_type)
                pass
                try:
                    whisper_segments_raw, info = model.transcribe(
                        short_wav_path, 
                        beam_size=5, 
                        language="zh"
                    )
                    whisper_segments_raw = list(whisper_segments_raw)
                except Exception as e:
                    print(f"❌ [LOG] Faster-Whisper 转写发生错误: {e}")
                    whisper_segments_raw = []
            else:
                # 使用 FunASR 进行本地转写
                model, funasr_type = model_cache_manager.get_funasr_model(device_to_use)
                try:
                    if funasr_type == "sensevoice":
                        # SenseVoice 专属高性能推理参数与分段
                        res = model.generate(
                            input=short_wav_path,
                            language="auto",
                            use_itn=True,
                            batch_size_s=60,
                            merge_vad=True,
                            merge_length_s=15,
                        )
                        whisper_segments_raw = []
                        if res and len(res) > 0:
                            raw_text = res[0].get("text", "")
                            clean_text = clean_sensevoice_text(raw_text)
                            if clean_text:
                                # 按中英文常见句子终结标点进行自然断句
                                parts = re.split(r'([。！？；…\?\!])', clean_text)
                                sentence_list = []
                                current = ""
                                for p in parts:
                                    if not p:
                                        continue
                                    current += p
                                    if p in "。！？；…?!":
                                        sentence_list.append(current.strip())
                                        current = ""
                                if current.strip():
                                    sentence_list.append(current.strip())

                                # 准确获取音频总时长以进行时间步长等比例对齐
                                total_audio_sec = 0.0
                                try:
                                    import wave as _wave
                                    with _wave.open(short_wav_path, "rb") as w:
                                        total_audio_sec = w.getnframes() / float(w.getframerate())
                                except Exception:
                                    pass

                                total_chars = sum(len(s) for s in sentence_list) if sentence_list else 1
                                current_time = 0.0

                                for sentence in sentence_list:
                                    if total_audio_sec > 0:
                                        seg_dur = max((len(sentence) / total_chars) * total_audio_sec, 0.5)
                                    else:
                                        seg_dur = max(len(sentence) / 3.5, 1.5)

                                    whisper_segments_raw.append(WhisperSegmentDummy(
                                        start=current_time,
                                        end=current_time + seg_dur,
                                        text=sentence
                                    ))
                                    current_time += seg_dur
                            else:
                                print("⚠️ [LOG] SenseVoice 识别文本为空")
                        else:
                            print("⚠️ [LOG] SenseVoice 返回结果为空")
                    else:
                        # Paraformer 原有推理逻辑
                        res = model.generate(input=short_wav_path, batch_size_s=300, sentence_timestamp=True)
                        whisper_segments_raw = []
                        if res and len(res) > 0:
                            if "sentence_info" in res[0] and res[0]["sentence_info"]:
                                for sentence in res[0]["sentence_info"]:
                                    whisper_segments_raw.append(WhisperSegmentDummy(
                                        start=sentence.get("start", 0) / 1000.0,
                                        end=sentence.get("end", 0) / 1000.0,
                                        text=sentence.get("text", "")
                                    ))
                            elif "timestamp" in res[0] and res[0]["timestamp"]:
                                full_text = res[0].get("text", "")
                                timestamps = res[0]["timestamp"]
                                print(f"⚠️ [LOG] FunASR 返回结果缺少 sentence_info，使用字符级时间戳构建段落 (字数: {len(full_text)}, ts: {len(timestamps)})")

                                parts = re.split(r'([。！？；…?])', full_text) if full_text else []
                                sentence_list = []
                                current = ""
                                for p in parts:
                                    if not p:
                                        continue
                                    current += p
                                    if p in "。！？；…?":
                                        sentence_list.append(current.strip())
                                        current = ""
                                if current.strip():
                                    sentence_list.append(current.strip())

                                _PUNC_CHARS = set("。！？；…?,.!;:，、")
                                char_pos = 0
                                for sent in sentence_list:
                                    speech_len = sum(1 for c in sent if c not in _PUNC_CHARS)
                                    if char_pos < len(timestamps) and speech_len > 0:
                                        end_pos = min(char_pos + speech_len, len(timestamps))
                                        seg_start = timestamps[char_pos][0] / 1000.0
                                        seg_end   = timestamps[end_pos - 1][1] / 1000.0
                                        whisper_segments_raw.append(WhisperSegmentDummy(
                                            start=seg_start,
                                            end=seg_end,
                                            text=sent
                                        ))
                                        char_pos = end_pos
                            elif "text" in res[0] and res[0]["text"]:
                                full_text = res[0]["text"]
                                print(f"⚠️ [LOG] FunASR 返回结果缺少时间戳信息。已采用全文断句估计模式 (字数: {len(full_text)})")

                                sentences = re.split(r'([。！？；…?])', full_text)
                                sentence_list = []
                                current_sentence = ""
                                for part in sentences:
                                    if not part:
                                        continue
                                    current_sentence += part
                                    if part in "。！？；…?":
                                        sentence_list.append(current_sentence.strip())
                                        current_sentence = ""
                                if current_sentence.strip():
                                    sentence_list.append(current_sentence.strip())

                                current_time = 0.0
                                for sentence in sentence_list:
                                    N = len(sentence)
                                    duration_est = max(N / 3.5, 1.5)
                                    whisper_segments_raw.append(WhisperSegmentDummy(
                                        start=current_time,
                                        end=current_time + duration_est,
                                        text=sentence
                                    ))
                                    current_time += duration_est
                            else:
                                print("⚠️ [LOG] FunASR 返回结果为空或解析失败")
                        else:
                            print("⚠️ [LOG] FunASR 返回结果为空")
                except Exception as e:
                    import traceback as _traceback
                    _err_detail = _traceback.format_exc()
                    print(f"❌ [LOG] FunASR 转写发生错误: {e}\n详细堆栈:\n{_err_detail}")
                    whisper_segments_raw = []

            # 过滤相邻重复句，防止本地 Whisper 幻觉循环
            def clean_txt(text):
                return re.sub(r'[^\w\s]', '', text).strip()

            dedup_prev_text = ""
            if whisper_segments_raw:
                duration = max(seg.end for seg in whisper_segments_raw)
            else:
                duration = 1.0

            # Calculate and print ASR performance metrics
            asr_end_time = time.time()
            asr_duration = asr_end_time - asr_start_time
            rtf = asr_duration / max(duration, 1.0)
            speed_ratio = max(duration, 1.0) / max(asr_duration, 0.001)
            
            if is_whisper:
                engine_name = 'Faster-Whisper'
            elif not is_whisper and 'funasr_type' in locals() and funasr_type == 'sensevoice':
                engine_name = 'FunASR SenseVoiceSmall'
            else:
                engine_name = 'FunASR Paraformer'
            print(f"📊 [ASR REPORT] Engine: {engine_name} | Audio: {duration/60.0:.1f}m | Time: {asr_duration:.1f}s | Speed: {speed_ratio:.1f}x (RTF: {rtf:.3f})")

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

                # Timestamp (fractional seconds for precise alignment)
                total_seconds = seg.start
                hour = int(total_seconds // 3600)
                minute = int((total_seconds % 3600) // 60)
                second = total_seconds % 60
                timestamp = f"[{hour:02d}:{minute:02d}:{second:05.2f}]"

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
                        pass
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
                            if str(pe) == "TASK_CANCELLED":
                                raise pe
                            print(f"⚠️ [LOG] 进度回调触发异常: {pe}")

            # Flush remaining segments
            if on_segment_batch and batch_buffer:
                try:
                    on_segment_batch(list(batch_buffer))
                except Exception as batch_ex:
                    pass

            print("✅ 语音识别转录成功完成！")
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

            model = model_cache_manager.get_pyannote_embedding(device_to_use)
            
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
                                pass
                
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
                    
                    pass
            
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

                    sewn_json_str = call_llm(prompt, label="LLM语义缝合")
                    
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




