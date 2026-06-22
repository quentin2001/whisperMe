import os
import uuid
import traceback
import shutil
import time
import threading
import urllib.parse
import json
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import (
    config, 
    SHORT_DOWNLOADS_DIR, 
    SHORT_TRANSCRIPTS_DIR,
    CURRENT_VERSION
)
from app.database import db
from app.core.downloader import PodcastDownloader
from app.core.transcriber import PodcastTranscriber
from app.core.summarizer import PodcastSummarizer
from app.core.notifier import notifier
from app.core.queue_manager import queue_manager

# 导入子路由
from app.routers.tasks import router as tasks_router, upload_router
from app.routers.config import router as config_router
from app.routers.system import router as system_router, start_system_background_tasks
from app.routers.boards import router as boards_router

app = FastAPI(title="whisperMe Local Podcast Processor", version=CURRENT_VERSION)

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

# 引入模块化路由
app.include_router(tasks_router)
app.include_router(upload_router)
app.include_router(config_router)
app.include_router(system_router)
app.include_router(boards_router)

# 初始化核心组件
downloader = PodcastDownloader()
transcriber = PodcastTranscriber()
summarizer = PodcastSummarizer()

# --- 智能声纹特征与大模型命名推理引擎 ---

def match_speakers_with_voiceprints(speaker_embeddings: dict) -> dict:
    """
    Compare speaker embeddings with fingerprints database using Cosine Similarity
    """
    if not speaker_embeddings:
        return {}
    try:
        from app.config import PROJECT_DIR
        import numpy as np
        fingerprints_file = os.path.join(PROJECT_DIR, "speaker_fingerprints.json")
        if not os.path.exists(fingerprints_file):
            return {}
        with open(fingerprints_file, "r", encoding="utf-8") as f:
            fingerprints = json.load(f)
        if not fingerprints:
            return {}
            
        mappings = {}
        for sp_id, emb in speaker_embeddings.items():
            if not emb: continue
            best_match = None
            max_sim = -1.0
            
            emb_v = np.array(emb)
            norm_emb = np.linalg.norm(emb_v)
            if norm_emb == 0: continue
            
            for known_name, known_emb in fingerprints.items():
                known_v = np.array(known_emb)
                norm_known = np.linalg.norm(known_v)
                if norm_known == 0: continue
                
                sim = np.dot(emb_v, known_v) / (norm_emb * norm_known)
                if sim > max_sim:
                    max_sim = sim
                    best_match = known_name
            
            # 余弦相似度阈值设为 0.81，确保匹配高精准
            if max_sim >= 0.81 and best_match:
                mappings[sp_id] = best_match
                print(f"🎯 [LOG] 声纹库匹配成功 - 自动将 {sp_id} 关联为老熟人: {best_match} (相似度: {max_sim:.3f})")
        return mappings
    except Exception as e:
        print(f"⚠️ [LOG] 比对声纹特征库失败: {e}")
        return {}

def pre_filter_noise_speakers(transcript: list) -> dict:
    """
    第一阶段：预过滤噪音发言人（只说语气助词，总字数极少，或空白段）
    返回字典: {speaker_id: "语气词发言人"}
    """
    if not transcript:
        return {}
        
    speaker_stats = {}
    for seg in transcript:
        sp = seg.get("speaker")
        if not sp: continue
        text = seg.get("text", "").strip()
        speaker_stats[sp] = speaker_stats.get(sp, "") + text
        
    noise_speakers = {}
    interjection_chars = set("嗯对啊哦吧呢呀啦哈哼嗨呗嘛呃喔呦哎好的噢唏嚯啥么是吗了嘿哟嗷呐哇")
    
    for sp, full_text in speaker_stats.items():
        # 移除标点和空白
        cleaned = "".join([c for c in full_text if c.isalnum()])
        if not cleaned:
            noise_speakers[sp] = "语气词发言人"
            continue
            
        # 过滤仅包含语气助词，且总句长很短的发言人
        if len(cleaned) <= 15 and all(c in interjection_chars for c in cleaned):
            noise_speakers[sp] = "语气词发言人"
            print(f"🚫 [LOG] 第一阶段预过滤 - 发言人 {sp} 说话极短且全为语气助词，直接标记为'语气词发言人'，跳过大模型识别。")
            
    return noise_speakers

def split_shownotes(shownotes: str) -> dict:
    """
    辅助分析 shownotes 结构，拆分为节目内容区和常驻主播模板区
    """
    if not shownotes:
        return {"episode_content": "", "template_section": "", "episode_names": set(), "template_names": set()}
        
    lines = shownotes.split('\n')
    episode_lines = []
    template_lines = []
    
    is_template = False
    template_keywords = ["加入我们", "加入听友群", "关注我们", "日常指南", "播客合作", "联系我们", "小红书", "公众号", "微博", "商业合作", "制作人", "主播:", "主持:", "嘉宾:", "Staff", "团队:"]
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # 启发式规则：一旦检测到联系方式或版权常驻内容，判定后续均为固定模板区
        if any(kw in stripped for kw in template_keywords) or is_template:
            is_template = True
            template_lines.append(line)
        else:
            episode_lines.append(line)
            
    episode_content = "\n".join(episode_lines)
    template_section = "\n".join(template_lines)
    
    # 提取专有名词人名候选
    def extract_names_from_text(text):
        import re
        names = set()
        # 匹配 @用户 或 "@" 标志的别名
        matches_at = re.findall(r'@([a-zA-Z0-9_\u4e00-\u9fa5]+)', text)
        names.update(matches_at)
        
        # 匹配常见的 "主播：XXX" 模式
        matches_host = re.findall(r'(?:主持|主播|嘉宾|制作|后期|剪辑|文案|商务|运营)[：:\s]+([a-zA-Z0-9_\u4e00-\u9fa5\s，、]+)', text)
        for m in matches_host:
            for sub in re.split(r'[，、\s]+', m):
                sub = sub.strip()
                if sub and len(sub) <= 8:
                    names.add(sub)
        return names
        
    episode_names = extract_names_from_text(episode_content)
    template_names = extract_names_from_text(template_section)
    print(f"👤 [LOG] 本期内容区人名: {episode_names}")
    print(f"📄 [LOG] 固定模板区人名: {template_names}")
    return {"episode_content": episode_content, "template_section": template_section, "episode_names": episode_names, "template_names": template_names}

def _call_llm_api(prompt: str, summary_mode: str = None, label: str = "LLM调用") -> str:
    import httpx
    if not summary_mode:
        summary_mode = config.get("summary_mode", "local")
    headers = {"Content-Type": "application/json"}
    if summary_mode == "online":
        api_key = config.get("online_summary_api_key", "").strip()
        base_url = config.get("online_summary_base_url", "https://api.openai.com/v1").strip()
        target_model = config.get("online_summary_model", "gpt-4o-mini").strip()
        api_url = f"{base_url.rstrip('/')}/chat/completions"
        if api_key: headers["Authorization"] = f"Bearer {api_key}"
        print(f"📡 [LOG] {label}【在线模式】 - 接口: {api_url} | 模型: {target_model}")
    else:
        ollama_url = config.get("ollama_url", "http://localhost:11434").strip()
        target_model = config.get("ollama_model", "qwen2.5:7b-instruct").strip()
        base_url = ollama_url.rstrip('/')
        if '/v1' not in base_url and '11434' not in base_url: api_url = f"{base_url}/v1/chat/completions"
        elif '11434' in base_url and '/v1' not in base_url: api_url = f"{base_url}/v1/chat/completions"
        else: api_url = f"{base_url}/chat/completions"
        print(f"🤖 [LOG] {label}【本地模式】 - 接口: {api_url} | 模型: {target_model}")
    payload = {"model": target_model, "messages": [{"role": "user", "content": prompt}], "stream": False, "temperature": 0.1}
    response = None
    try:
        with httpx.Client(timeout=120.0, trust_env=True) as client:
            response = client.post(api_url, json=payload, headers=headers)
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                print(f"❌ [LOG ERROR] LLM 响应错误, code: {response.status_code}, body: {response.text}")
                return ""
    except Exception as e:
        print(f"❌ [LOG ERROR] LLM 请求超时或建联失败: {e}")
        return ""

def _llm_identify_participants(title: str, episode_content: str, template_names: set, summary_mode: str = None) -> list:
    """
    第二阶段：推理这期节目的所有【可能参与者名单】
    """
    prompt = f"""一期播客的标题是：《{title}》
该节目的 ShowNotes（播客简介）部分摘录如下：
---
{episode_content}
---
此外，本节目在固定结尾常驻的主播/幕后团队名单候选有：{list(template_names)}。

任务：
请根据标题、播客简介，推断出这期单集节目的“真实在场说话的发言人”（包含常驻主播、特邀嘉宾等）。
注意：
1. 播客简介里提到的人名（如“本期我们邀请了XXX”）是极高概率的在场发言人。
2. 固定结尾名单中的主播，可能这期节目录制时缺席了（例如“本期由主播A独立主持，主播B请假”）。请根据简介内容排除缺席的常驻主播。
3. 请只列出你认为确定在场发言的人名列表。

请以严格的 JSON 数组格式返回（不要有 ```json 或 Markdown 格式包裹，只返回纯文本数组），例如：
["张三", "李四"]"""
    
    response_str = _call_llm_api(prompt, summary_mode=summary_mode, label="第2阶段-识别在场名单")
    try:
        # 清除 Markdown 标记符号
        cleaned = response_str.strip().replace("```json", "").replace("```", "").strip()
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        pass
    return []

def _llm_match_speakers(participants: list, transcript: list, unmatched_speakers: list, known_mappings: dict, title: str, summary_mode: str = None) -> dict:
    """
    第三阶段：将临时发言人标签（如 SPEAKER_00）与推导出的真实人名进行配对
    """
    # 提取对话前 30 句进行文本指征匹配
    sample_size = min(35, len(transcript))
    sample_transcript = []
    
    # 判定是否属于纯文本噪声（如空回复或全是符号）
    def is_clean_text(text: str) -> bool:
        if not text: return False
        cleaned = "".join([c for c in text if c.isalnum()])
        return len(cleaned) > 0

    for seg in transcript[:80]:
        if len(sample_transcript) >= sample_size:
            break
        txt = seg.get("text", "").strip()
        sp = seg.get("speaker")
        if sp and is_clean_text(txt):
            # 如果声纹库已在第一阶段锁定该 SPEAKER 姓名，则直接在此替换，方便 LLM 建立上下文定位
            mapped_name = known_mappings.get(sp, sp)
            sample_transcript.append(f"{mapped_name}: {txt}")
            
    transcript_snippet = "\n".join(sample_transcript)
    
    prompt = f"""你是一个顶级的音频文本声光定位分析专家。
当前有一期播客，标题为：《{title}》
经算法分析，本期单集实际在场的【真实发言人名单】候选有：{participants}。

现在给你这期节目开头的前 30 句转录文本（其中部分发言人可能已经被声纹库认出并标记了名字，其余则标记为临时符号如 SPEAKER_XX）：
---
{transcript_snippet}
---

请根据发言人的说话语气、自报家门（如“大家好，我是某某”）、打招呼以及相互的称呼、甚至对话的逻辑，把这些未识别的临时发言人标识（{unmatched_speakers}）与真实候选名单（{participants}）进行精确的一对一匹配。

输出要求：
1. 必须以严格的 JSON 字典格式输出，Key 为临时标识，Value 为匹配到的真实人名，例如：{{"SPEAKER_00": "张三"}}。
2. 不要包含 ```json 或 Markdown 符号包裹，直接输出纯 JSON 字符串。
3. 如果某个人物实在无法判定，可以不输出在 JSON 中。"""

    response_str = _call_llm_api(prompt, summary_mode=summary_mode, label="第3阶段-声纹与人名匹配")
    try:
        cleaned = response_str.strip().replace("```json", "").replace("```", "").strip()
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    return {}

def _validate_mappings(llm_mappings: dict, episode_content: str, episode_names: set, template_names: set) -> dict:
    """
    第四阶段：黄金交叉校验防御机制
    """
    if not llm_mappings:
        return {}
        
    final_mappings = {}
    lower_shownotes = (episode_content or "").lower()
    
    # 提取 shownotes 包含的全部专有名词人名合集，支持大小写模糊匹配
    all_valid_names = set(n.lower() for n in episode_names | template_names)
    
    for sp_id, matched_name in llm_mappings.items():
        if not matched_name or matched_name == sp_id:
            continue
            
        m_name_lower = matched_name.lower()
        # 规则 1：名字必须在 shownotes 候选人名中，或者出现在 shownotes 文本中
        if m_name_lower in all_valid_names or m_name_lower in lower_shownotes:
            final_mappings[sp_id] = matched_name
        else:
            # 规则 2：拼写容错（如 Shownotes 写的是 "Quentin"，LLM 识别并返回了 "quentin2001"）
            fuzzy_match = False
            for name in (episode_names | template_names):
                if name.lower() in m_name_lower or m_name_lower in name.lower():
                    final_mappings[sp_id] = name
                    print(f"🛡️ [交叉校验] 拼写纠偏 - 将大模型输出 '{matched_name}' 自动纠正为 Shownotes 正确拼写 '{name}'")
                    fuzzy_match = True
                    break
            if not fuzzy_match:
                print(f"🛡️ [交叉校验拦截] 大模型输出的 '{matched_name}' 无法在播客 ShowNotes 中找到任何提及，判定为幻觉匹配，已拒绝应用该结果！")
                
    return final_mappings

def match_speakers_with_llm(metadata: dict, transcript: list, unmatched_speakers: list, known_mappings: dict, summary_mode: str = None, noise_speakers: dict = None, shownotes_split: dict = None) -> dict:
    """
    运行大模型基于上下文推理的声纹匹配管线（第2、3、4阶段）
    """
    if not unmatched_speakers:
        return {}
        
    title = metadata.get("title", "未知标题")
    shownotes = metadata.get("shownotes", "")
    
    # 解析 shownotes 结构
    if not shownotes_split:
        shownotes_split = split_shownotes(shownotes)
        
    episode_content = shownotes_split["episode_content"]
    template_names = shownotes_split["template_names"]
    episode_names = shownotes_split["episode_names"]
    
    # 第 2 阶段：获取当前单集在场发言人名单
    participants = _llm_identify_participants(title, episode_content, template_names, summary_mode=summary_mode)
    if not participants:
        print("⚠️ [LOG 警告] 第二阶段未推断出任何在场发言人名单候选。")
        return {}
    print(f"👥 [LOG] 第二阶段 - 大模型推断的本期真实在场人员: {participants}")
    
    # 第 3 阶段：运行指征上下文匹配
    llm_mappings = _llm_match_speakers(participants, transcript, unmatched_speakers, known_mappings, title, summary_mode=summary_mode)
    if not llm_mappings:
        print("⚠️ [LOG 警告] 第三阶段未建立起临时标识与真实名字的关联。")
        return {}
    print(f"🔌 [LOG] 第三阶段 - 大模型建议的配对映射: {llm_mappings}")
    
    # 第 4 阶段：交叉验证
    final_mappings = _validate_mappings(llm_mappings, episode_content, episode_names, template_names)
    return final_mappings

def auto_rename_speakers(task_id: str, metadata: dict, transcript: list, speaker_embeddings: dict):
    """
    一键自动化声纹角色推理核心管线
    """
    from app.database import db
    task = db.get_task(task_id)
    if not task: return
    
    existing_mappings = task.get("speaker_mappings", {})
    all_speakers = set(seg.get("speaker") for seg in transcript if seg.get("speaker"))
    
    # 阶段 1：第一层噪音物理熔断过滤
    noise_mappings = pre_filter_noise_speakers(transcript)
    
    # 阶段 2：第二层历史声纹特征库（老熟人）余弦相似度比对
    # 排除噪音发言人和已标记完的人
    unmatched_embeddings = {}
    if speaker_embeddings:
        for sp_id, emb in speaker_embeddings.items():
            if sp_id not in noise_mappings and sp_id not in existing_mappings:
                unmatched_embeddings[sp_id] = emb
                
    voiceprint_mappings = match_speakers_with_voiceprints(unmatched_embeddings)
    
    # 合并阶段 1 和阶段 2 结果
    known_mappings = {**noise_mappings, **voiceprint_mappings}
    
    # 阶段 3：第三层大模型上下文指征分析与第四层 ShowNotes 黄金交叉验证
    unmatched_speakers = list(all_speakers - set(known_mappings.keys()) - set(existing_mappings.keys()))
    
    llm_mappings = {}
    if unmatched_speakers:
        try:
            summary_mode = task.get("summary_mode", "local")
            llm_mappings = match_speakers_with_llm(
                metadata, 
                transcript, 
                unmatched_speakers, 
                {**existing_mappings, **known_mappings}, 
                summary_mode=summary_mode
            )
        except Exception as e:
            print(f"⚠️ [LOG] 大模型推理改名失败: {e}")
            
    # 合并所有匹配映射
    final_mappings = {**noise_mappings, **voiceprint_mappings, **llm_mappings}
    if final_mappings:
        merged = {**final_mappings, **existing_mappings}
        db.update_task(task_id, speaker_mappings=merged)
        print(f"🎉 [LOG] 四阶段智能识别完成！已自动应用以下角色命名: {merged}")

def apply_interjection_labels(task_id: str, transcript: list):
    from app.database import db
    if not transcript: return
    task = db.get_task(task_id)
    if not task: return
    speaker_texts = {}
    for seg in transcript:
        sp = seg.get("speaker")
        if not sp: continue
        speaker_texts[sp] = speaker_texts.get(sp, "") + seg.get("text", "").strip()
    mappings = task.get("speaker_mappings", {})
    modified = False
    interjection_chars = set("嗯对啊哦吧呢呀啦哈哼嗨呗嘛呃喔呦哎好的噢唏嚯啥么是吗了嘿哟嗷呐哇")
    for sp, full_text in speaker_texts.items():
        if sp in mappings and mappings[sp] and mappings[sp] != sp: continue
        cleaned = "".join([c for c in full_text if c.isalnum()])
        if not cleaned:
            mappings[sp] = "未识别语气词"
            modified = True
            continue
        if len(cleaned) <= 15 and all(c in interjection_chars for c in cleaned):
            mappings[sp] = "未识别语气词"
            modified = True
            print(f"🏷️ [LOG] 自动将仅说语气助词的发言人 {sp} 标记为 '未识别语气词'")
    if modified:
        db.update_task(task_id, speaker_mappings=mappings)

# --- 异步后台工作引擎 ---

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
        task = db.get_task(task_id)
        if not task:
            print(f"⚠️ [LOG] 检测到任务 {task_id} 已被删除，队列自动抛弃执行。")
            return

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
            
        # Step 1: 下载音频与获取元数据
        db.update_task(task_id, status="downloading", progress=10.0)
        
        def download_progress_callback(percent):
            # 实时检查任务是否已被删除，如果是则抛出异常以中断下载流
            if not db.get_task(task_id):
                raise Exception("TASK_CANCELLED")
            # 将下载进度 (0-100) 映射到数据库任务 progress 字段 (10-30)
            mapped_progress = 10.0 + (percent / 100.0) * 20.0
            db.update_task(task_id, progress=round(mapped_progress, 1))
            
        t_download_start = time.time()
        local_mp3, metadata = downloader.download_url_audio(url, progress_callback=download_progress_callback)
        timing_stats['音频下载与解析'] = time.time() - t_download_start
        
        # 双重检查
        if not db.get_task(task_id):
            raise Exception("TASK_CANCELLED")
            
        # 将解析到的播客元数据回写数据库
        db.update_task(
            task_id, 
            title=metadata["title"], 
            podcast_name=metadata["podcast_name"],
            image_url=metadata.get("image_url", ""),
            metadata=metadata,
            progress=30.0
        )
        
        # Step 2: 音频格式预处理（16kHz Mono WAV）
        if not db.get_task(task_id):
            raise Exception("TASK_CANCELLED")
        db.update_task(task_id, status="transcribing", progress=40.0)
        t_preprocess_start = time.time()
        standardized_wav = downloader.preprocess_audio(local_mp3)
        timing_stats['音频预处理'] = time.time() - t_preprocess_start
        
        # 在数据库中记录音频相对于服务端的播放路径 (e.g. /audio/hash.mp3)
        if not db.get_task(task_id):
            raise Exception("TASK_CANCELLED")
        audio_filename = os.path.basename(local_mp3)
        db.update_task(task_id, audio_url=f"/audio/{audio_filename}", progress=45.0)

        # Step 3: PyAnnote 声纹分割
        if not db.get_task(task_id):
            raise Exception("TASK_CANCELLED")
        t_diarization_start = time.time()
        diar_data = transcriber.run_diarization(standardized_wav)
        timing_stats['声纹分割 (PyAnnote)'] = time.time() - t_diarization_start
        db.update_task(task_id, progress=60.0)

        # Step 4: Whisper 语音识别与时间轴交叉合并
        if not db.get_task(task_id):
            raise Exception("TASK_CANCELLED")
            
        def progress_callback(current_progress):
            if not db.get_task(task_id):
                raise Exception("TASK_CANCELLED")
            db.update_task(task_id, progress=current_progress)

        asr_mode = task.get("asr_mode", "local")
        t_transcribe_start = time.time()
        merged_transcript = transcriber.transcribe_and_merge(
            standardized_wav, 
            diar_data, 
            progress_callback=progress_callback,
            asr_mode=asr_mode
        )
        timing_stats['语音识别转录 (Whisper)'] = time.time() - t_transcribe_start
        db.update_task(task_id, transcript=merged_transcript, progress=75.0)

        # Step 4.2: 运行语义段落聚合 (Semantic Chunking)
        try:
            print("⏳ [LOG] 正在运行语义分块聚合管道...")
            t_chunk_start = time.time()
            paragraphs = transcriber.cluster_segments_to_paragraphs(task_id, merged_transcript)
            timing_stats['语义段落聚合'] = time.time() - t_chunk_start
            db.add_paragraphs(paragraphs)
            print(f"✅ [LOG] 成功为任务 {task_id} 聚合出 {len(paragraphs)} 个语义段落。")
        except Exception as chunk_ex:
            print(f"⚠️ [LOG 警告] 语义分块聚合失败: {chunk_ex}")

        # Step 4.5: 提取声纹特征，并进行智能特征及上下文改名
        if not db.get_task(task_id):
            raise Exception("TASK_CANCELLED")
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
        if not db.get_task(task_id):
            raise Exception("TASK_CANCELLED")
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
        if not db.get_task(task_id):
            raise Exception("TASK_CANCELLED")
        db.update_task(task_id, status="summarizing", progress=80.0)
        task_summary_mode = task.get("summary_mode", "local")
        t_summary_start = time.time()
        summary_report = summarizer.summarize(metadata, merged_transcript, summary_mode=task_summary_mode)
        timing_stats['AI 深度总结 (LLM)'] = time.time() - t_summary_start
        
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

        # 标志任务已彻底成功
        if not db.get_task(task_id):
            raise Exception("TASK_CANCELLED")
        db.update_task(task_id, status="completed", progress=100.0)

        # Step 6: 消息提醒
        notifier.send_desktop_notification(
            title="播客 AI 转录完成！",
            message=f"《{metadata['title']}》已转录成功，点击进入工作台查看。"
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
        
        notifier.send_desktop_notification(
            title="播客处理失败",
            message=f"URL: {url}\n错误: {str(e)}"
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

# --- 自动清理逻辑 ---

def run_auto_cleanup():
    from datetime import datetime
    current_cfg = config
    if not current_cfg.get("enable_auto_cleanup", False):
        return
        
    threshold_days = int(current_cfg.get("cleanup_threshold_days", 30))
    print(f"🧹 [Auto Cleanup] Starting audio file check. Threshold: {threshold_days} days.")
    
    try:
        all_tasks = db.get_all_tasks()
        now = datetime.now()
        cleaned_count = 0
        
        for task in all_tasks:
            audio_url = task.get("audio_url")
            if not audio_url:
                continue
                
            created_at_str = task.get("created_at")
            if not created_at_str:
                continue
                
            try:
                cleaned_date_str = created_at_str
                if "+" in cleaned_date_str:
                    cleaned_date_str = cleaned_date_str.split("+")[0]
                elif "-" in cleaned_date_str and "T" in cleaned_date_str and len(cleaned_date_str) > 19:
                    cleaned_date_str = cleaned_date_str[:19]
                    
                created_dt = datetime.strptime(cleaned_date_str[:19], "%Y-%m-%dT%H:%M:%S")
                age_days = (now - created_dt).days
                
                if age_days >= threshold_days:
                    filename = os.path.basename(audio_url)
                    
                    other_tasks = [t for t in all_tasks if t.get("id") != task["id"]]
                    is_shared_with_younger = False
                    for ot in other_tasks:
                        ot_audio = ot.get("audio_url")
                        if ot_audio and os.path.basename(ot_audio) == filename:
                            ot_created = ot.get("created_at")
                            if ot_created:
                                if "+" in ot_created:
                                    ot_created = ot_created.split("+")[0]
                                ot_dt = datetime.strptime(ot_created[:19], "%Y-%m-%dT%H:%M:%S")
                                if (now - ot_dt).days < threshold_days:
                                    is_shared_with_younger = True
                                    break
                                    
                    if not is_shared_with_younger:
                        local_file_path = os.path.join(SHORT_DOWNLOADS_DIR, filename)
                        if os.path.exists(local_file_path):
                            try:
                                os.remove(local_file_path)
                                print(f"🗑️ [Auto Cleanup] Cleaned up old audio file: {local_file_path}")
                            except Exception as e:
                                print(f"⚠️ [Auto Cleanup] Failed to delete file: {e}")
                                
                    db.update_task(task["id"], audio_url="")
                    cleaned_count += 1
            except Exception as parse_err:
                print(f"⚠️ [Auto Cleanup] Error processing task {task.get('id')} date: {parse_err}")
                
        if cleaned_count > 0:
            print(f"🧹 [Auto Cleanup] Done. Cleaned up {cleaned_count} audio files.")
    except Exception as e:
        print(f"❌ [Auto Cleanup] Error checking tasks: {e}")

def background_auto_cleanup_loop():
    """后台独立线程，启动 5 秒后及此后每隔 1 小时自动执行一次音频清理检测"""
    time.sleep(5)
    while True:
        try:
            run_auto_cleanup()
        except Exception as e:
            print(f"⚠️ [Auto Cleanup Thread Error] {e}")
        time.sleep(3600)

# --- App 启动生命周期管理 ---

@app.on_event("startup")
def startup_event():
    # 0. 启动后台独立性能监控线程 (来自 routers.system)
    start_system_background_tasks()
    print("✅ [STARTUP] 独立后台性能监控哨兵已上线！")
    
    # 0.5 启动自动音频清理检查线程
    threading.Thread(target=background_auto_cleanup_loop, daemon=True).start()
    print("✅ [STARTUP] 独立后台音频文件自动清理哨兵已上线！")
    
    # 1. 启动队列管理器并绑定管道处理器
    queue_manager.start(run_podcast_pipeline)
    
    # 2. 自动恢复数据库中因服务重启而中断的未完成/排队任务，并重入队列
    try:
        tasks = db.get_all_tasks()
        requeued_count = 0
        for t in tasks:
            status = t.get("status")
            if status not in ["completed", "failed"]:
                db.update_task(
                    t["id"],
                    status="pending",
                    progress=0.0,
                    error_message=None
                )
                
                # 重回队列
                queue_manager.add_task(t["id"], t["url"])
                requeued_count += 1
                print(f"🔄 [STARTUP] 检测到未完成任务，已自动重新入队: {t.get('title') or t.get('id')} | URL: {t.get('url')}")
        print(f"✅ [STARTUP] 成功恢复并重新排队 {requeued_count} 个未完成任务。")
    except Exception as e:
        print(f"❌ [STARTUP] 恢复未完成任务失败: {e}")

    # 3. 运行历史任务语气助词发言人自动标记迁移 (已修复 SQLite _write_data 写入 Bug)
    try:
        tasks = db.get_all_tasks()
        interjection_chars = set("嗯对啊哦吧呢呀啦哈哼嗨呗嘛呃喔呦哎对好的噢唏嚯啥呀么）—（,，.。?？!！谢拜行了")
        for t in tasks:
            full_t = db.get_task(t["id"])
            if not full_t: continue
            transcript = full_t.get("transcript", [])
            if not transcript:
                continue
            
            speaker_texts = {}
            for seg in transcript:
                sp = seg.get("speaker")
                if not sp:
                    continue
                text = seg.get("text", "").strip()
                speaker_texts[sp] = speaker_texts.get(sp, "") + text
                
            mappings = full_t.get("speaker_mappings", {})
            task_modified = False
            for sp, full_text in speaker_texts.items():
                if sp in mappings and mappings[sp] and mappings[sp] != sp:
                    continue
                
                pure_text = "".join([c for c in full_text if c.strip()])
                if pure_text == "" or set(pure_text).issubset(interjection_chars):
                    mappings[sp] = "语气词发言人"
                    task_modified = True
                    
            if task_modified:
                db.update_task(t["id"], speaker_mappings=mappings)
                print(f"🏷️ [STARTUP MIGRATION] 自动为任务 {t.get('title') or t.get('id')} 中的发言人标记 '语气词发言人'")
    except Exception as migration_ex:
        print(f"❌ [STARTUP MIGRATION] 语气词发言人迁移失败: {migration_ex}")
