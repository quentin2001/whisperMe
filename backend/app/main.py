import os
import uuid
import traceback
import shutil
from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from app.config import (
    config, 
    save_config, 
    SHORT_DOWNLOADS_DIR, 
    SHORT_TRANSCRIPTS_DIR
)
from app.database import db
from app.core.downloader import PodcastDownloader
from app.core.transcriber import PodcastTranscriber
from app.core.summarizer import PodcastSummarizer
from app.core.notifier import PodcastNotifier
from app.core.queue_manager import queue_manager

app = FastAPI(title="whisperMe Local Podcast Processor", version="1.0.0")

# 配置 CORS 跨域请求（前端 Vite 运行在 5173，后端运行在 8000）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件挂载：允许前端直接读取下载好的原始 MP3 播客音频
app.mount("/audio", StaticFiles(directory=str(SHORT_DOWNLOADS_DIR)), name="audio")

# 初始化核心组件
downloader = PodcastDownloader()
transcriber = PodcastTranscriber()
summarizer = PodcastSummarizer()
notifier = PodcastNotifier()

@app.on_event("startup")
def startup_event():
    # 1. 启动队列管理器并绑定管道处理器
    queue_manager.start(run_podcast_pipeline)
    
    # 2. 自动恢复数据库中因服务重启而中断的未完成/排队任务，并重入队列
    try:
        data = db._read_data()
        modified = False
        requeued_count = 0
        for t in data.get("tasks", []):
            status = t.get("status")
            if status not in ["completed", "failed"]:
                t["status"] = "pending"
                t["progress"] = 0.0
                t["error_message"] = None
                modified = True
                
                # 重回队列
                queue_manager.add_task(t["id"], t["url"])
                requeued_count += 1
                print(f"🔄 [STARTUP] 检测到未完成任务，已自动重新入队: {t.get('title') or t.get('id')} | URL: {t.get('url')}")
        if modified:
            db._write_data(data)
            print(f"✅ [STARTUP] 成功恢复并重新排队 {requeued_count} 个未完成任务。")
    except Exception as e:
        print(f"❌ [STARTUP] 恢复未完成任务失败: {e}")

    # 3. 运行历史任务语气助词发言人自动标记迁移
    try:
        data = db._read_data()
        modified = False
        interjection_chars = set("嗯对啊哦吧呢呀啦哈哼嗨呗嘛呃喔呦哎对好的噢唏嚯啥呀么）—（,，.。?？!！谢拜行了")
        for t in data.get("tasks", []):
            transcript = t.get("transcript", [])
            if not transcript:
                continue
            
            speaker_texts = {}
            for seg in transcript:
                sp = seg.get("speaker")
                if not sp:
                    continue
                text = seg.get("text", "").strip()
                speaker_texts[sp] = speaker_texts.get(sp, "") + text
                
            mappings = t.get("speaker_mappings", {})
            task_modified = False
            for sp, full_text in speaker_texts.items():
                if sp in mappings and mappings[sp] and mappings[sp] != sp:
                    continue
                cleaned = "".join([c for c in full_text if c.isalnum()])
                if not cleaned:
                    mappings[sp] = "未识别语气词"
                    task_modified = True
                    continue
                all_chars_interjection = all(c in interjection_chars for c in cleaned)
                if len(cleaned) <= 8 and all_chars_interjection:
                    mappings[sp] = "未识别语气词"
                    task_modified = True
            if task_modified:
                t["speaker_mappings"] = mappings
                modified = True
                print(f"🏷️ [STARTUP MIGRATION] 自动为任务 {t.get('title') or t.get('id')} 中的发言人标记 '未识别语气词'")
        if modified:
            db._write_data(data)
    except Exception as migration_ex:
        print(f"❌ [STARTUP MIGRATION] 语气词发言人迁移失败: {migration_ex}")

# --- Pydantic 模型类 ---
class CreateTaskRequest(BaseModel):
    url: str
    asr_mode: str = "local"

class RenameSpeakerRequest(BaseModel):
    speaker_id: str
    new_name: str

class UpdateConfigRequest(BaseModel):
    ffmpeg_path: str
    ffmpeg_bin_dir: str
    local_whisper_model_path: str
    hf_token: str
    ollama_url: str
    ollama_model: str
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_sender: str
    notification_email: str
    enable_win_notification: bool
    asr_mode: str = "local"
    online_api_key: str = ""
    online_base_url: str = "https://token-plan-sgp.xiaomimimo.com/v1"
    online_model: str = "mimo-v2.5-asr"
    summary_mode: str = "local"
    online_summary_api_key: str = ""
    online_summary_base_url: str = "https://api.openai.com/v1"
    online_summary_model: str = "gpt-4o-mini"


# --- 智能声纹特征与大模型命名推理引擎 ---
def save_speaker_fingerprint(name: str, embedding: list[float]):
    if not name or not embedding:
        return
    try:
        from app.config import PROJECT_DIR
        import json
        fingerprints_file = os.path.join(PROJECT_DIR, "speaker_fingerprints.json")
        fingerprints = {}
        if os.path.exists(fingerprints_file):
            with open(fingerprints_file, "r", encoding="utf-8") as f:
                fingerprints = json.load(f)
        fingerprints[name] = embedding
        with open(fingerprints_file, "w", encoding="utf-8") as f:
            json.dump(fingerprints, f, ensure_ascii=False, indent=2)
        print(f"💾 [LOG] 声纹特征成功写入特征库: {name}")
    except Exception as e:
        print(f"⚠️ [LOG] 写入声纹特征库失败: {e}")

def match_speakers_with_voiceprints(speaker_embeddings: dict) -> dict:
    """
    Compare speaker embeddings with fingerprints database using Cosine Similarity
    """
    if not speaker_embeddings:
        return {}
    
    try:
        from app.config import PROJECT_DIR
        import json
        import numpy as np
        
        fingerprints_file = os.path.join(PROJECT_DIR, "speaker_fingerprints.json")
        if not os.path.exists(fingerprints_file):
            return {}
            
        with open(fingerprints_file, "r", encoding="utf-8") as f:
            fingerprints = json.load(f)
            
        matched_mappings = {}
        
        for sp_id, emb in speaker_embeddings.items():
            emb_arr = np.array(emb)
            best_name = None
            best_sim = 0.0
            
            for name, fp_emb in fingerprints.items():
                fp_arr = np.array(fp_emb)
                
                # Calculate Cosine Similarity
                norm_emb = np.linalg.norm(emb_arr)
                norm_fp = np.linalg.norm(fp_arr)
                if norm_emb > 0 and norm_fp > 0:
                    sim = np.dot(emb_arr, fp_arr) / (norm_emb * norm_fp)
                    if sim > best_sim:
                        best_sim = sim
                        best_name = name
                        
            # Match if similarity is high (threshold = 0.8)
            if best_sim >= 0.8:
                matched_mappings[sp_id] = best_name
                print(f"🔍 [LOG] 声纹库精准匹配成功: {sp_id} -> {best_name} (相似度: {best_sim:.2f})")
                
        return matched_mappings
    except Exception as e:
        print(f"⚠️ [LOG] 声纹特征库匹配失败: {e}")
        return {}

def match_speakers_with_llm(metadata: dict, transcript: list, unmatched_speakers: list, known_mappings: dict) -> dict:
    """
    Use local Ollama or Online Standard API to match unmatched speakers using shownotes and first 5 minutes of transcript
    """
    if not unmatched_speakers:
        return {}
        
    try:
        import httpx
        import json
        from app.config import config
        
        # 1. Prepare shownotes
        shownotes = metadata.get("shownotes", "").strip()
        title = metadata.get("title", "")
        
        # 2. Extract first 5 minutes of transcript (e.g. first 40 segments)
        transcript_sample = []
        for seg in transcript[:40]:
            speaker_tag = seg.get("speaker", "UNKNOWN")
            # Map known speakers so LLM has more context
            speaker_name = known_mappings.get(speaker_tag, speaker_tag)
            transcript_sample.append(f"【{speaker_name}】: {seg.get('text', '')}")
            
        transcript_text = "\n".join(transcript_sample)
        
        # 3. Build prompt
        prompt = f"""
我们有一个播客单集，标题是《{title}》。
节目简介（Shownotes）如下：
---
{shownotes}
---

以下是该单集前几分钟的对话文本：
---
{transcript_text}
---

已知的部分角色匹配：
{json.dumps(known_mappings, ensure_ascii=False)}

请通过分析播客简介中提到的“主持人”、“主播”及“嘉宾”名单，结合对话开头人物之间的称呼、打招呼方式与自我介绍，推断出以下未匹配的 SPEAKER ID 对应简介里的哪位具体人物姓名：
未匹配列表: {unmatched_speakers}

注意：
1. 仅返回一个简洁的 JSON 格式的字典映射，例如：{{"SPEAKER_00": "张三", "SPEAKER_01": "李四"}}。
2. 不要包含任何 MarkDown 格式标记（如 ```json 标签），也不要包含任何解释性文字，直接输出 JSON 纯文本。
3. 如果根据文本无法推断出某些 ID 对应的人名，请对应返回 null，例如：{{"SPEAKER_00": null}}。
"""

        # Dynamic engine selection based on config
        summary_mode = config.get("summary_mode", "local")
        headers = {"Content-Type": "application/json"}
        
        if summary_mode == "online":
            api_key = config.get("online_summary_api_key", "").strip()
            base_url = config.get("online_summary_base_url", "https://api.openai.com/v1").strip()
            target_model = config.get("online_summary_model", "gpt-4o-mini").strip()
            
            api_url = f"{base_url.rstrip('/')}/chat/completions"
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            print(f"📡 [LOG] 智能人名推断启动【在线模式】 - 接口: {api_url} | 模型: {target_model}")
        else:
            ollama_url = config.get("ollama_url", "http://localhost:11434").strip()
            target_model = config.get("ollama_model", "qwen2.5:7b-instruct").strip()
            
            base_url = ollama_url.rstrip('/')
            if '/v1' not in base_url and '11434' not in base_url:
                api_url = f"{base_url}/v1/chat/completions"
            elif '11434' in base_url and '/v1' not in base_url:
                api_url = f"{base_url}/v1/chat/completions"
            else:
                api_url = f"{base_url}/chat/completions"
            print(f"🤖 [LOG] 智能人名推断启动【本地模式】 - 接口: {api_url} | 模型: {target_model}")
            
        payload = {
            "model": target_model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "temperature": 0.1
        }
        
        with httpx.Client(timeout=45.0, trust_env=False) as client:
            r = client.post(api_url, headers=headers, json=payload)
            
        if r.status_code == 200:
            res_data = r.json()
            response_text = res_data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            
            # Extract JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
                
            response_text = response_text.strip()
            
            # Parse JSON
            llm_mappings = json.loads(response_text)
            
            # Filter valid mappings
            valid_mappings = {}
            for k, v in llm_mappings.items():
                if k in unmatched_speakers and v and isinstance(v, str):
                    valid_mappings[k] = v
                    print(f"🤖 [LOG] 大模型推理匹配成功: {k} -> {v}")
                    
            return valid_mappings
            
    except Exception as e:
        print(f"⚠️ [LOG] 大模型智能人名推理失败: {e}")
        
    return {}

def auto_rename_speakers(task_id: str, metadata: dict, transcript: list, speaker_embeddings: dict):
    """
    Combined speaker renaming automation pipeline
    """
    if not transcript or not speaker_embeddings:
        return
        
    print(f"🚀 [LOG] 正在对任务 {task_id} 启动智能声纹库与大模型改名流水线...")
    
    # 1. First Pass: Voiceprint embedding match
    voiceprint_mappings = match_speakers_with_voiceprints(speaker_embeddings)
    
    # 2. Identify remaining unmatched speakers
    all_speakers = set(speaker_embeddings.keys())
    matched_speakers = set(voiceprint_mappings.keys())
    unmatched_speakers = list(all_speakers - matched_speakers)
    
    # 3. Second Pass: LLM shownotes deduction for unmatched speakers
    llm_mappings = {}
    if unmatched_speakers:
        llm_mappings = match_speakers_with_llm(metadata, transcript, unmatched_speakers, voiceprint_mappings)
        
    # 4. Merge mappings
    final_mappings = {**voiceprint_mappings, **llm_mappings}
    
    if final_mappings:
        # Load existing task mappings if any
        task = db.get_task(task_id)
        if task:
            existing_mappings = task.get("speaker_mappings", {})
            # Merge (prioritizing existing manually renamed ones, then new matched ones)
            merged = {**final_mappings, **existing_mappings}
            db.update_task(task_id, speaker_mappings=merged)
            print(f"🎉 [LOG] 智能改名流水线完成！已自动应用以下角色命名: {merged}")

def apply_interjection_labels(task_id: str, transcript: list):
    """
    分析所有发言人的总文本，如果某个发言人只说了极其简短的语气词/助词，
    且用户或智能匹配尚未给其命名，则自动将其默认昵称设为“未识别语气词”。
    """
    if not transcript:
        return
        
    task = db.get_task(task_id)
    if not task:
        return
        
    speaker_texts = {}
    for seg in transcript:
        sp = seg.get("speaker")
        if not sp:
            continue
        text = seg.get("text", "").strip()
        speaker_texts[sp] = speaker_texts.get(sp, "") + text
        
    mappings = task.get("speaker_mappings", {})
    modified = False
    
    interjection_chars = set("嗯对啊哦吧呢呀啦哈哼嗨呗嘛呃喔呦哎对好的噢唏嚯啥呀么）—（,，.。?？!！谢拜行了")
    for sp, full_text in speaker_texts.items():
        if sp in mappings and mappings[sp] and mappings[sp] != sp:
            continue
        cleaned = "".join([c for c in full_text if c.isalnum()])
        if not cleaned:
            mappings[sp] = "未识别语气词"
            modified = True
            continue
        all_chars_interjection = all(c in interjection_chars for c in cleaned)
        if len(cleaned) <= 8 and all_chars_interjection:
            mappings[sp] = "未识别语气词"
            modified = True
            print(f"🏷️ [LOG] 自动将仅说语气助词的发言人 {sp} 标记为 '未识别语气词' (总文本: '{full_text}')")
            
    if modified:
        db.update_task(task_id, speaker_mappings=mappings)

# --- 异步后台工作引擎 ---
def run_podcast_pipeline(task_id: str, url: str):
    """
    完整的本地播客处理异步流水线
    """
    local_mp3 = None
    standardized_wav = None
    
    try:
        # Step 0: 物理安全校验，如果任务被中途从数据库删除，立即跳过执行
        task = db.get_task(task_id)
        if not task:
            print(f"⚠️ [LOG] 检测到任务 {task_id} 已被删除，队列自动抛弃执行。")
            return

        # Step 0.5: 检测本地大模型服务是否可用（若配置为本地大模型总结模式）
        from app.config import config
        summary_mode = config.get("summary_mode", "local")
        if summary_mode == "local":
            import socket
            import urllib.parse
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
                    f"本地大模型未开启：当前系统配置的是【本地大模型总结模式】，但未检测到正在运行的本地推理服务（地址: {ollama_url}）。"
                    "请先启动您的 LM Studio 或 Ollama 服务，或者在【系统设置】中将 AI 总结引擎切换为【在线 OpenAI 兼容 API】。"
                )
            
        # Step 1: 下载音频与获取元数据
        db.update_task(task_id, status="downloading", progress=10.0)
        
        def download_progress_callback(percent):
            # 实时检查任务是否已被删除，如果是则抛出异常以中断下载流
            if not db.get_task(task_id):
                raise Exception("TASK_CANCELLED")
            # 将下载进度 (0-100) 映射到数据库任务 progress 字段 (10-30)
            mapped_progress = 10.0 + (percent / 100.0) * 20.0
            db.update_task(task_id, progress=round(mapped_progress, 1))
            
        local_mp3, metadata = downloader.download_url_audio(url, progress_callback=download_progress_callback)
        
        # 双重检查
        if not db.get_task(task_id):
            raise Exception("TASK_CANCELLED")
            
        # 将解析到的播客元数据回写数据库
        db.update_task(
            task_id, 
            title=metadata["title"], 
            podcast_name=metadata["podcast_name"],
            metadata=metadata,
            progress=30.0
        )
        
        # Step 2: 音频格式预处理（16kHz Mono WAV）
        if not db.get_task(task_id):
            raise Exception("TASK_CANCELLED")
        db.update_task(task_id, status="transcribing", progress=40.0)
        standardized_wav = downloader.preprocess_audio(local_mp3)
        
        # 在数据库中记录音频相对于服务端的播放路径 (e.g. /audio/hash.mp3)
        if not db.get_task(task_id):
            raise Exception("TASK_CANCELLED")
        audio_filename = os.path.basename(local_mp3)
        db.update_task(task_id, audio_url=f"/audio/{audio_filename}", progress=45.0)

        # Step 3: PyAnnote 声纹分割
        if not db.get_task(task_id):
            raise Exception("TASK_CANCELLED")
        diar_data = transcriber.run_diarization(standardized_wav)
        db.update_task(task_id, progress=60.0)

        # Step 4: Whisper 语音识别与时间轴交叉合并
        if not db.get_task(task_id):
            raise Exception("TASK_CANCELLED")
            
        def progress_callback(current_progress):
            if not db.get_task(task_id):
                raise Exception("TASK_CANCELLED")
            db.update_task(task_id, progress=current_progress)

        asr_mode = task.get("asr_mode", "local")
        merged_transcript = transcriber.transcribe_and_merge(
            standardized_wav, 
            diar_data, 
            progress_callback=progress_callback,
            asr_mode=asr_mode
        )
        db.update_task(task_id, transcript=merged_transcript, progress=75.0)

        # Step 4.5: 提取声纹特征特征，并进行智能特征及上下文改名
        if not db.get_task(task_id):
            raise Exception("TASK_CANCELLED")
        try:
            print("⏳ [LOG] 正在提取发言人声纹特征向量...")
            speaker_embeddings = transcriber.extract_speaker_embeddings(standardized_wav, diar_data)
            db.update_task(task_id, speaker_embeddings=speaker_embeddings)
            
            # 运行智能改名流水线
            auto_rename_speakers(task_id, metadata, merged_transcript, speaker_embeddings)
        except Exception as emb_ex:
            if str(emb_ex) == "TASK_CANCELLED":
                raise emb_ex
            print(f"⚠️ [LOG 警告] 提取声纹特征或智能改名失败: {emb_ex}")

        # Step 4.8: 对仅说语气词/短词的发言人自动打上“未识别语气词”标签
        if not db.get_task(task_id):
            raise Exception("TASK_CANCELLED")
        try:
            apply_interjection_labels(task_id, merged_transcript)
        except Exception as label_ex:
            print(f"⚠️ [LOG 警告] 自动标记语气词发言人失败: {label_ex}")

        # 物理销毁临时超大标准化 WAV 音频，仅留原始压缩 MP3 供前端播放
        if standardized_wav and os.path.exists(standardized_wav):
            try:
                os.remove(standardized_wav)
                print(f"🗑️ [LOG] 已物理清理临时大音频: {standardized_wav}")
            except Exception as fe:
                print(f"⚠️ [LOG 警告] 无法物理清理临时 WAV 文件: {fe}")

        # Step 5: 调用本地 Ollama / 在线大模型进行长剧本摘要与口碑分析
        if not db.get_task(task_id):
            raise Exception("TASK_CANCELLED")
        db.update_task(task_id, status="summarizing", progress=80.0)
        summary_report = summarizer.summarize(metadata, merged_transcript)
        db.update_task(task_id, summary=summary_report, progress=95.0)

        # 标志任务已彻底成功
        if not db.get_task(task_id):
            raise Exception("TASK_CANCELLED")
        db.update_task(task_id, status="completed", progress=100.0)

        # Step 6: 消息/邮件提醒
        task_info = db.get_task(task_id)
        notifier.send_desktop_notification(
            title="播客 AI 转录完成！",
            message=f"《{metadata['title']}》已转录成功，点击进入工作台查看。"
        )
        notifier.send_email_notification(
            podcast_title=metadata["title"],
            podcast_name=metadata["podcast_name"],
            task_id=task_id,
            summary_md=summary_report,
            like_count=metadata["like_count"],
            comment_count=metadata["comment_count"]
        )

    except Exception as e:
        # 如果任务在中途已经被物理删除，静默跳过其余数据库和通知逻辑，物理销毁所有临时生成的音频，释放资源
        task_exists = db.get_task(task_id) is not None
        if not task_exists or str(e) == "TASK_CANCELLED":
            print(f"🗑️ [LOG] 检测到任务 {task_id} 在运行期间已被用户删除，物理流程彻底中止并安全释放磁盘。")
            if local_mp3 and os.path.exists(local_mp3):
                try:
                    os.remove(local_mp3)
                except Exception:
                    pass
            return
            
        print(f"❌ [🚨 任务异常中断] 任务 {task_id} 崩盘: {e}")
        traceback.print_exc()
        db.update_task(task_id, status="failed", error_message=str(e), progress=100.0)
        
        # 异常桌面通知
        notifier.send_desktop_notification(
            title="播客处理失败",
            message=f"URL: {url}\n错误: {str(e)}"
        )
    finally:
        # 物理清理可能残留的标准化 WAV 文件
        if standardized_wav and os.path.exists(standardized_wav):
            try:
                os.remove(standardized_wav)
                print(f"🗑️ [CLEANUP] 已成功物理清理标准化 WAV: {standardized_wav}")
            except Exception:
                pass
        # 释放 GPU 显存与内存缓存
        try:
            import torch
            import gc
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                print("🧹 [CLEANUP] 已成功释放 PyTorch CUDA 显存缓存")
        except Exception as ram_ex:
            print(f"⚠️ [CLEANUP] 释放内存时出错: {ram_ex}")


# --- API 端点实现 ---

@app.get("/api/tasks")
def list_tasks():
    tasks = db.get_all_tasks()
    # 动态注入排队位置
    for t in tasks:
        if t.get("status") == "pending":
            pos = queue_manager.get_queue_position(t.get("id"))
            t["queue_position"] = pos
    return tasks

@app.get("/api/tasks/{task_id}")
def get_task_details(task_id: str):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="未找到该任务")
    # 动态注入排队位置
    if task.get("status") == "pending":
        pos = queue_manager.get_queue_position(task.get("id"))
        task["queue_position"] = pos
    return task

@app.post("/api/tasks")
def create_task(req: CreateTaskRequest):
    task_id = str(uuid.uuid4())
    db.add_task(task_id, req.url, asr_mode=req.asr_mode)
    
    # 放入全局单例队列管理器进行排队串行处理，不再直接塞给 background_tasks 并行跑
    queue_manager.add_task(task_id, req.url)
    return {"task_id": task_id, "status": "pending"}

@app.post("/api/upload")
def upload_audio(file: UploadFile = File(...), asr_mode: str = Form("local")):
    # 1. 验证文件后缀
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"]:
        raise HTTPException(status_code=400, detail="不支持的音频格式。仅支持 mp3, wav, m4a, aac, flac, ogg 等格式。")
    
    # 2. 生成唯一的任务 ID 和文件名
    task_id = str(uuid.uuid4())
    safe_filename = f"uploaded_{task_id}{ext}"
    local_path = os.path.join(SHORT_DOWNLOADS_DIR, safe_filename)
    
    # 3. 保存上传文件到 downloads 目录
    try:
        with open(local_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存上传音频文件失败: {str(e)}")
        
    # 4. 创建任务并以本地导入的元数据初始化
    db.add_task(task_id, local_path, asr_mode=asr_mode)
    
    name_without_ext = os.path.splitext(file.filename)[0]
    db.update_task(
        task_id,
        title=name_without_ext,
        podcast_name="本地导入",
        metadata={
            "title": name_without_ext,
            "podcast_name": "本地导入",
            "shownotes": "用户上传的本地音频文件，完全离线处理。",
            "like_count": 0,
            "comment_count": 0,
            "comments": [],
            "source": "local"
        }
    )
    
    # 5. 放入全局单例队列管理器进行排队串行处理
    queue_manager.add_task(task_id, local_path)
    return {"task_id": task_id, "status": "pending"}

@app.get("/api/performance")
def get_performance():
    import subprocess
    import torch
    from app.config import PROJECT_DIR
    
    cpu_percent = 0.0
    ram_total_gb = 0.0
    ram_used_gb = 0.0
    ram_percent = 0.0
    
    vram_total_mb = 0.0
    vram_used_mb = 0.0
    vram_percent = 0.0
    gpu_name = "NVIDIA GPU"
    gpu_util = 0.0
    gpu_temp = 0.0
    
    # 1. 查询 CPU 占用率
    try:
        cpu_out = subprocess.check_output("wmic cpu get LoadPercentage /Value", shell=True).decode("utf-8", errors="ignore")
        for line in cpu_out.splitlines():
            if "LoadPercentage=" in line:
                cpu_percent = float(line.split("=")[1].strip())
    except Exception:
        pass
        
    # 2. 查询系统内存 RAM
    try:
        ram_out = subprocess.check_output("wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /Value", shell=True).decode("utf-8", errors="ignore")
        free_kb = 0
        total_kb = 0
        for line in ram_out.splitlines():
            if "FreePhysicalMemory=" in line:
                free_kb = float(line.split("=")[1].strip())
            elif "TotalVisibleMemorySize=" in line:
                total_kb = float(line.split("=")[1].strip())
        if total_kb > 0:
            ram_total_gb = round(total_kb / (1024 * 1024), 1)
            used_kb = total_kb - free_kb
            ram_used_gb = round(used_kb / (1024 * 1024), 1)
            ram_percent = round((used_kb / total_kb) * 100, 1)
    except Exception:
        pass

    # 3. 查询显卡及显存 VRAM 详细信息
    has_gpu = torch.cuda.is_available()
    if has_gpu:
        try:
            # 3.1 查显存
            vram_out = subprocess.check_output(
                "nvidia-smi --query-gpu=memory.total,memory.used,memory.free --format=csv,noheader,nounits", 
                shell=True
            ).decode("utf-8", errors="ignore")
            parts = vram_out.strip().split(",")
            if len(parts) >= 3:
                vram_total_mb = float(parts[0].strip())
                vram_used_mb = float(parts[1].strip())
                vram_percent = round((vram_used_mb / vram_total_mb) * 100, 1)
                
            # 3.2 查 GPU 物理名称 (动态匹配用户显卡，拒绝硬编码)
            gpu_name_out = subprocess.check_output(
                "nvidia-smi --query-gpu=name --format=csv,noheader", 
                shell=True
            ).decode("utf-8", errors="ignore").strip()
            if gpu_name_out:
                gpu_name = gpu_name_out
                
            # 3.3 查 GPU 核心计算负载
            gpu_util_out = subprocess.check_output(
                "nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits", 
                shell=True
            ).decode("utf-8", errors="ignore").strip()
            if gpu_util_out:
                gpu_util = float(gpu_util_out)
                
            # 3.4 查 GPU 核心温度
            gpu_temp_out = subprocess.check_output(
                "nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits", 
                shell=True
            ).decode("utf-8", errors="ignore").strip()
            if gpu_temp_out:
                gpu_temp = float(gpu_temp_out)
        except Exception:
            pass

    # 4. 查询磁盘存储空间 (项目所在分区)
    disk_total_gb = 0.0
    disk_used_gb = 0.0
    disk_percent = 0.0
    try:
        total, used, free = shutil.disk_usage(str(PROJECT_DIR))
        disk_total_gb = round(total / (1024**3), 1)
        disk_used_gb = round(used / (1024**3), 1)
        disk_percent = round((used / total) * 100, 1)
    except Exception:
        pass

    # 5. 查询任务排队状况
    queue_size = 0
    try:
        queue_size = queue_manager.task_queue.qsize()
        if queue_manager.get_current_task_id() is not None:
            queue_size += 1
    except Exception:
        pass

    # 6. 检测本地大模型接口连接状况 (仅在用户选择本地模式时检测)
    llm_status = "online_mode"
    try:
        from app.config import config
        summary_mode = config.get("summary_mode", "local")
        if summary_mode == "local":
            import socket
            import urllib.parse
            ollama_url = config.get("ollama_url", "http://localhost:11434").strip()
            parsed = urllib.parse.urlparse(ollama_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 11434
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3) # 限制 300ms 快速超时，不阻塞 API
            s.connect((host, port))
            s.close()
            llm_status = "connected"
    except Exception:
        llm_status = "offline"

    return {
        "cpu": cpu_percent,
        "ram": {
            "total": ram_total_gb,
            "used": ram_used_gb,
            "percent": ram_percent
        },
        "vram": {
            "total": vram_total_mb,
            "used": vram_used_mb,
            "percent": vram_percent,
            "has_gpu": has_gpu,
            "gpu_name": gpu_name,
            "gpu_util": gpu_util,
            "gpu_temp": gpu_temp
        },
        "disk": {
            "total": disk_total_gb,
            "used": disk_used_gb,
            "percent": disk_percent
        },
        "queue": {
            "size": queue_size
        },
        "llm_status": llm_status
    }

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
        
    # 物理清除下载的 MP3 文件以释放硬盘
    audio_url = task.get("audio_url")
    if audio_url:
        filename = os.path.basename(audio_url)
        local_file_path = os.path.join(SHORT_DOWNLOADS_DIR, filename)
        if os.path.exists(local_file_path):
            try:
                os.remove(local_file_path)
                print(f"🗑️ [LOG] 任务删除 - 已物理清除音频文件: {local_file_path}")
            except Exception as e:
                print(f"⚠️ [LOG 警告] 无法删除物理音频: {e}")

    success = db.delete_task(task_id)
    return {"success": success}

@app.post("/api/tasks/{task_id}/speaker/rename")
def rename_speaker(task_id: str, req: RenameSpeakerRequest):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="未找到任务")
        
    mappings = task.get("speaker_mappings", {})
    mappings[req.speaker_id] = req.new_name
    db.update_task(task_id, speaker_mappings=mappings)
    
    # 将手动命名的发言人声纹特征写入本地声纹库
    speaker_embs = task.get("speaker_embeddings", {})
    emb = speaker_embs.get(req.speaker_id)
    if emb:
        save_speaker_fingerprint(req.new_name, emb)
        
    return {"success": True, "speaker_mappings": mappings}

@app.post("/api/tasks/{task_id}/summary/regenerate")
def regenerate_summary(task_id: str, background_tasks: BackgroundTasks):
    """
    当修改了发言人昵称或需要重新总结时，可手动发起 Ollama 重建总结任务
    """
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="未找到任务")
    
    if task["status"] != "completed" and task["status"] != "failed":
        raise HTTPException(status_code=400, detail="任务处于非就绪状态，无法重新生成总结")

    def run_re_summarize():
        try:
            db.update_task(task_id, status="summarizing", progress=80.0)
            summary_report = summarizer.summarize(
                task["metadata"], 
                task["transcript"], 
                speaker_mappings=task.get("speaker_mappings")
            )
            db.update_task(task_id, status="completed", summary=summary_report, progress=100.0)
        except Exception as ex:
            db.update_task(task_id, status="failed", error_message=str(ex), progress=100.0)

    background_tasks.add_task(run_re_summarize)
    return {"status": "summarizing"}

@app.get("/api/config")
def get_global_config():
    return load_config_dict()

@app.post("/api/config")
def update_global_config(req: UpdateConfigRequest):
    new_cfg = req.dict()
    save_config(new_cfg)
    
    # 强制将新变量重写回内存 config 字典中，完成实时热更新
    for k, v in new_cfg.items():
        config[k] = v
        
    # 重更新 HF_TOKEN 内存缓存
    global HF_TOKEN
    import app.config
    import app.core.transcriber
    
    new_token = new_cfg.get("hf_token", "").strip()
    app.config.HF_TOKEN = new_token
    app.core.transcriber.HF_TOKEN = new_token
    
    # 重更新 HF_ENDPOINT 环境变量与 huggingface_hub constants
    import os
    if new_token and len(new_token) >= 30:
        os.environ["HF_ENDPOINT"] = "https://huggingface.co"
        try:
            import huggingface_hub.constants
            huggingface_hub.constants.ENDPOINT = "https://huggingface.co"
            huggingface_hub.constants.HUGGINGFACE_CO_URL_TEMPLATE = "https://huggingface.co/{repo_id}/resolve/{revision}/{filename}"
        except Exception:
            pass
    else:
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        try:
            import huggingface_hub.constants
            huggingface_hub.constants.ENDPOINT = "https://hf-mirror.com"
            huggingface_hub.constants.HUGGINGFACE_CO_URL_TEMPLATE = "https://hf-mirror.com/{repo_id}/resolve/{revision}/{filename}"
        except Exception:
            pass
        
    # 重启更新 notifier SMTP 缓存
    global notifier
    notifier = PodcastNotifier()
    
    return {"success": True}

# 辅助读取配置
def load_config_dict():
    from app.config import CONFIG_FILE_PATH
    import json
    with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
