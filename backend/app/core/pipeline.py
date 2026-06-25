import os
import time
import traceback
import urllib.parse
from app.config import config
from app.database import db
from app.core.downloader import PodcastDownloader
from app.core.transcriber import PodcastTranscriber
from app.core.summarizer import PodcastSummarizer
from app.core.speaker import auto_rename_speakers, apply_interjection_labels
from app.core.notifier import notifier
from app.core import logger

print = logger.info

downloader = PodcastDownloader()
transcriber = PodcastTranscriber()
summarizer = PodcastSummarizer()

def check_cancelled(task_id: str) -> dict:
    task = db.get_task(task_id)
    if not task or task.get("status") == "cancelled":
        raise Exception("TASK_CANCELLED")
    return task

def run_podcast_pipeline(task_id: str, url: str):
    """
    完整的本地播客处理异步流水线
    """
    local_mp3 = None
    standardized_wav = None
    pipeline_start_time = time.time()
    timing_stats = {}
    
    try:
        # Step 0: 物理安全校验，如果任务被中途从数据库删除，立即跳过执行
        task = check_cancelled(task_id)

        # Step 0.5: 检测本地大模型服务是否可用（若配置为本地大模型总结模式）
        summary_mode = task.get("summary_mode", "local")
        if summary_mode == "local":
            import socket
            ollama_url = config.get("ollama_url", "http://localhost:11434").strip()
            try:
                parsed = urllib.parse.urlparse(ollama_url)
                host = parsed.hostname or "localhost"
                port = parsed.port or 11434
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1.0)
                s.connect((host, port))
                s.close()
            except Exception:
                raise Exception(
                    f"本地大模型未开启：当前系统配置的是【本地大模型总结模式】，但未检测到正在运行 the 本地推理服务（地址: {ollama_url}）。"
                    "请先启动您的 LM Studio 或 Ollama 服务，或者在【系统设置】中将 AI 总结引擎切换为【在线 OpenAI 兼容 API】。"
                )
            
        # Step 0.8: ASR 断点续传/跳过检查
        # 增量写入后，转录中也会有段落。只有段落+完整transcript同时存在才跳过
        existing_paragraphs = db.get_paragraphs_by_podcast(task_id)
        has_full_transcript = bool(task.get("transcript"))
        if existing_paragraphs and len(existing_paragraphs) > 0 and has_full_transcript:
            print(f"🎯 [LOG] 检测到数据库中任务 {task_id} 已有历史转录段落 ({len(existing_paragraphs)} 段)，直接跳过下载与 ASR 转录，进入 AI 总结重算阶段。")
            db.update_task(task_id, status="summarizing", progress=80.0)
            
            task_metadata = task.get("metadata") or {
                "title": task.get("title") or "未命名任务",
                "podcast_name": task.get("podcast_name") or "本地导入",
                "image_url": task.get("image_url") or "",
                "like_count": 0,
                "comment_count": 0,
                "shownotes": "",
                "comments": []
            }
            merged_transcript = task.get("transcript") or []
            
            check_cancelled(task_id)
            task_summary_mode = task.get("summary_mode", "local")
            t_summary_start = time.time()
            summary_report = summarizer.summarize(task_metadata, merged_transcript, summary_mode=task_summary_mode)
            
            total_time = time.time() - pipeline_start_time
            time_report = f"\n\n---\n\n### ⏱️ 分析用时统计 (ASR 断点跳过)\n- **AI 总结**: {time.time() - t_summary_start:.1f} 秒\n- **总计耗时**: {total_time:.1f} 秒\n"
            summary_report += time_report
            db.update_task(task_id, summary=summary_report, progress=95.0)

            check_cancelled(task_id)
            db.update_task(task_id, status="completed", progress=100.0)

            notifier.send_desktop_notification(
                title="播客 AI 总结生成完成！",
                message=f"《{task_metadata['title']}》已重新总结成功。"
            )
            return

        # 清理不完整的增量段落（上次转录中途崩溃留下的）
        if existing_paragraphs and len(existing_paragraphs) > 0 and not has_full_transcript:
            print(f"🧹 [LOG] 检测到 {len(existing_paragraphs)} 条残留段落（无完整转录），清理后重新开始。")
            db.delete_paragraphs_by_podcast(task_id)

        # Step 1: 下载音频与获取元数据
        db.update_task(task_id, status="downloading", progress=10.0)
        
        def download_progress_callback(percent):
            # 实时检查任务是否已被删除或手动取消
            check_cancelled(task_id)
            # 将下载进度 (0-100) 映射到数据库任务 progress 字段 (10-30)
            mapped_progress = 10.0 + (percent / 100.0) * 20.0
            db.update_task(task_id, progress=round(mapped_progress, 1))
            
        t_download_start = time.time()
        local_mp3, metadata = downloader.download_url_audio(url, progress_callback=download_progress_callback)
        timing_stats['音频下载'] = time.time() - t_download_start
        
        # 双重检查
        check_cancelled(task_id)
            
        # 将解析到的播客元数据回写数据库
        db.update_task(
            task_id, 
            title=metadata["title"], 
            podcast_name=metadata["podcast_name"],
            image_url=metadata.get("image_url", ""),
            metadata=metadata,
            progress=30.0
        )

        # 立即注册音频播放路径，让用户可以边听边等
        check_cancelled(task_id)
        audio_filename = os.path.basename(local_mp3)
        db.update_task(task_id, audio_url=f"/audio/{audio_filename}", progress=32.0)

        # Step 2: 音频格式预处理（16kHz Mono WAV）
        check_cancelled(task_id)
        db.update_task(task_id, status="transcribing", progress=40.0)
        t_preprocess_start = time.time()
        standardized_wav = downloader.preprocess_audio(local_mp3)
        timing_stats['音频预处理'] = time.time() - t_preprocess_start

        # Step 3: PyAnnote 声纹分割
        check_cancelled(task_id)
        t_diarization_start = time.time()
        diar_data = transcriber.run_diarization(standardized_wav)
        timing_stats['声纹分割'] = time.time() - t_diarization_start
        db.update_task(task_id, progress=60.0)

        # Step 4: Whisper 语音识别与时间轴交叉合并
        check_cancelled(task_id)

        def progress_callback(current_progress):
            check_cancelled(task_id)
            db.update_task(task_id, progress=current_progress)

        # 增量段落写入回调
        accumulated_segments = []

        def on_segment_batch(new_segments):
            """每 10 个段落触发一次，增量写入数据库"""
            accumulated_segments.extend(new_segments)
            try:
                paragraphs = transcriber.cluster_segments_to_paragraphs(task_id, accumulated_segments)
                db.add_paragraphs(paragraphs)
            except Exception as batch_ex:
                print(f"⚠️ [LOG] 增量段落写入失败: {batch_ex}")

        asr_mode = task.get("asr_mode", "local")
        t_transcribe_start = time.time()
        merged_transcript = transcriber.transcribe_and_merge(
            local_mp3,  # Whisper 直读原始 MP3，不再需要 WAV 预处理
            diar_data,
            progress_callback=progress_callback,
            asr_mode=asr_mode,
            on_segment_batch=on_segment_batch
        )
        timing_stats['语音识别转录'] = time.time() - t_transcribe_start
        db.update_task(task_id, transcript=merged_transcript, progress=75.0)

        # Step 4.2: 最终段落聚合（兜底，确保完整性）
        try:
            print("⏳ [LOG] 正在运行最终语义分块聚合...")
            paragraphs = transcriber.cluster_segments_to_paragraphs(task_id, merged_transcript)
            db.add_paragraphs(paragraphs)
            print(f"✅ [LOG] 成功为任务 {task_id} 聚合出 {len(paragraphs)} 个语义段落。")
        except Exception as chunk_ex:
            print(f"⚠️ [LOG 警告] 语义分块聚合失败: {chunk_ex}")

        # Step 4.5: 提取声纹特征，并进行智能特征及上下文改名
        check_cancelled(task_id)
        try:
            print("⏳ [LOG] 正在提取发言人声纹特征向量...")
            speaker_embeddings = transcriber.extract_speaker_embeddings(standardized_wav, diar_data)
            db.update_task(task_id, speaker_embeddings=speaker_embeddings)
            
            # 如果聚类修正合并了 SPEAKER，需要同步更新已有的 transcript 和段落
            diar_speakers = set(seg["speaker"] for seg in diar_data)
            transcript_speakers = set(seg.get("speaker") for seg in merged_transcript)
            merged_away = transcript_speakers - diar_speakers
            if merged_away:
                reverse_map = {}
                for old_sp in merged_away:
                    for seg in merged_transcript:
                        if seg.get("speaker") == old_sp:
                            seg_center = (seg.get("start", 0) + seg.get("end", 0)) / 2
                            for d in diar_data:
                                if d["start"] <= seg_center <= d["end"]:
                                    reverse_map[old_sp] = d["speaker"]
                                    break
                            break
                
                if reverse_map:
                    print(f"🔄 [LOG] 正在同步聚类修正到转录文本: {reverse_map}")
                    for seg in merged_transcript:
                        if seg.get("speaker") in reverse_map:
                            seg["speaker"] = reverse_map[seg["speaker"]]
                    db.update_task(task_id, transcript=merged_transcript)
                    
                    try:
                        paragraphs = db.get_paragraphs_by_podcast(task_id)
                        if paragraphs:
                            updated = False
                            for p in paragraphs:
                                if p.get("speaker") in reverse_map:
                                    p["speaker"] = reverse_map[p["speaker"]]
                                    updated = True
                            if updated:
                                db.delete_paragraphs_by_podcast(task_id)
                                db.add_paragraphs(paragraphs)
                                print(f"✅ [LOG] 段落 speaker 标签已同步更新")
                    except Exception as para_ex:
                        print(f"⚠️ [LOG] 同步段落 speaker 标签失败: {para_ex}")
            
            t_rename_start = time.time()
            auto_rename_speakers(task_id, metadata, merged_transcript, speaker_embeddings)
        except Exception as emb_ex:
            timing_stats['发言人智能推断'] = time.time() - t_rename_start
            if str(emb_ex) == "TASK_CANCELLED":
                raise emb_ex
            print(f"⚠️ [LOG 警告] 提取声纹特征或智能改名失败: {emb_ex}")

        # Step 4.8: 对仅说语气词/短词的发言人自动打上“未识别语气词”标签
        check_cancelled(task_id)
        try:
            apply_interjection_labels(task_id, merged_transcript)
        except Exception as label_ex:
            print(f"⚠️ [LOG 警告] 自动标记语气词发言人失败: {label_ex}")

        # 物理销毁临时超大标准化 WAV 音频
        if standardized_wav and os.path.exists(standardized_wav):
            try:
                os.remove(standardized_wav)
                print(f"🗑️ [LOG] 已物理清理临时大音频: {standardized_wav}")
            except Exception as fe:
                print(f"⚠️ [LOG 警告] 无法物理清理临时 WAV 文件: {fe}")

        # Step 5: 调用 AI 总结
        check_cancelled(task_id)
        db.update_task(task_id, status="summarizing", progress=80.0)
        task_summary_mode = task.get("summary_mode", "local")
        t_summary_start = time.time()
        summary_report = summarizer.summarize(metadata, merged_transcript, summary_mode=task_summary_mode)
        timing_stats['AI 深度总结'] = time.time() - t_summary_start
        
        total_time = time.time() - pipeline_start_time
        time_report = "\n\n---\n\n### ⏱️ 分析用时统计\n"
        for step, t in timing_stats.items():
            if t > 60:
                time_report += f"- **{step}**: {t/60:.1f} 分钟\n"
            else:
                time_report += f"- **{step}**: {t:.1f} 秒\n"
        if total_time > 60:
            time_report += f"\n**总计耗时**: {total_time/60:.1f} 分钟"
        else:
            time_report += f"\n**总计耗时**: {total_time:.1f} 秒"
            
        summary_report += time_report
        db.update_task(task_id, summary=summary_report, progress=95.0)

        # 标志任务已彻底成功（校验关键产出）
        check_cancelled(task_id)
        if not merged_transcript or len(merged_transcript) == 0:
            db.update_task(task_id, status="failed", error_message="转录结果为空，无法生成总结。", progress=100.0)
            notifier.send_desktop_notification(title="❌ 播客处理失败", message=f"《{metadata.get('title', '')}》转录结果为空")
            return
        if not summary_report or len(summary_report.strip()) < 20:
            db.update_task(task_id, status="failed", error_message="AI 总结生成失败或内容过短。", progress=100.0)
            notifier.send_desktop_notification(title="❌ 播客处理失败", message=f"《{metadata.get('title', '')}》AI 总结失败")
            return
        db.update_task(task_id, status="completed", progress=100.0)

        # Step 6: 消息提醒
        duration_str = metadata.get("duration", "")
        duration_info = f" ({duration_str})" if duration_str and duration_str != "00:00" else ""
        notifier.send_desktop_notification(
            title="🎙️ 播客转录完成",
            message=f"{metadata['podcast_name']}｜{metadata['title']}{duration_info}"
        )
        if config.get("enable_email_notification", False):
            notifier.send_email_notification(
                podcast_title=metadata["title"],
                podcast_name=metadata["podcast_name"],
                task_id=task_id,
                summary_md=summary_report,
                like_count=metadata["like_count"],
                comment_count=metadata["comment_count"],
                image_url=metadata.get("image_url", "")
            )

    except Exception as e:
        task_info = db.get_task(task_id)
        task_exists = task_info is not None
        is_cancelled = task_info and task_info.get("status") == "cancelled"
        
        if not task_exists or is_cancelled or str(e) == "TASK_CANCELLED":
            print(f"🗑️ [LOG] 检测到任务 {task_id} 在运行期间已被用户删除或取消，物理流程彻底中断并安全释放磁盘。")
            if is_cancelled:
                db.update_task(task_id, status="cancelled", progress=100.0, error_message="任务已被手动取消。")
            if local_mp3 and os.path.exists(local_mp3):
                try:
                    os.remove(local_mp3)
                except Exception:
                    pass
            return
            
        print(f"❌ [🚨 任务异常中断] 任务 {task_id} 崩盘: {e}")
        traceback.print_exc()
        db.update_task(task_id, status="failed", error_message=str(e), progress=100.0)
        
        err_short = str(e)[:80] + ("..." if len(str(e)) > 80 else "")
        notifier.send_desktop_notification(
            title="❌ 播客处理失败",
            message=f"{task_info.get('title', '未知')}｜{err_short}"
        )
    finally:
        if standardized_wav and os.path.exists(standardized_wav):
            try:
                os.remove(standardized_wav)
                print(f"🗑️ [CLEANUP] 已成功物理清理标准化 WAV: {standardized_wav}")
            except Exception:
                pass
        try:
            import sys
            import gc
            gc.collect()
            if 'torch' in sys.modules:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    print("🧹 [CLEANUP] 已成功释放 PyTorch CUDA 显存缓存")
        except Exception as ram_ex:
            print(f"⚠️ [CLEANUP] 释放内存时出错: {ram_ex}")
