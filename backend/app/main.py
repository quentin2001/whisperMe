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
    SHORT_TRANSCRIPTS_DIR,
    CURRENT_VERSION
)
from app.database import db
from app.core.downloader import PodcastDownloader
from app.core.transcriber import PodcastTranscriber
from app.core.summarizer import PodcastSummarizer
from app.core.notifier import PodcastNotifier
from app.core.queue_manager import queue_manager
from app.core.prompt_manager import load_prompt, save_prompt
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

# 初始化核心组件
downloader = PodcastDownloader()
transcriber = PodcastTranscriber()
summarizer = PodcastSummarizer()
import time
import threading

notifier = PodcastNotifier()
# 系统全局状态
SYSTEM_PERF_CACHE = {
    "cpu": 0.0,
    "ram": {"total": 0.0, "used": 0.0, "percent": 0.0},
    "vram": {"has_gpu": False},
    "disk": {"total": 0.0, "used": 0.0, "percent": 0.0},
    "queue": {"size": 0},
    "llm_status": "offline"
}

def background_perf_monitor():
    """后台独立线程，定时抓取系统硬件信息，彻底解耦 API 响应"""
    import subprocess
    import shutil
    global SYSTEM_PERF_CACHE
    
    while True:
        try:
            perf_data = {
                "cpu": 0.0,
                "ram": {"total": 0.0, "used": 0.0, "percent": 0.0},
                "vram": {"has_gpu": False},
                "disk": {"total": 0.0, "used": 0.0, "percent": 0.0},
                "queue": {"size": 0},
                "llm_status": "online_mode"
            }
            
            # 1. CPU
            try:
                import psutil
                perf_data["cpu"] = float(psutil.cpu_percent(interval=None))
            except Exception:
                try:
                    cpu_out = subprocess.check_output("wmic cpu get LoadPercentage /Value", shell=True).decode("utf-8", errors="ignore")
                    for line in cpu_out.splitlines():
                        if "LoadPercentage=" in line:
                            perf_data["cpu"] = float(line.split("=")[1].strip())
                except Exception:
                    pass
                    
            # 2. RAM
            try:
                import psutil
                mem = psutil.virtual_memory()
                perf_data["ram"] = {
                    "total": round(mem.total / (1024 ** 3), 1),
                    "used": round(mem.used / (1024 ** 3), 1),
                    "percent": mem.percent
                }
            except Exception:
                try:
                    ram_out = subprocess.check_output("wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /Value", shell=True).decode("utf-8", errors="ignore")
                    free_kb = total_kb = 0
                    for line in ram_out.splitlines():
                        if "FreePhysicalMemory=" in line: free_kb = float(line.split("=")[1].strip())
                        elif "TotalVisibleMemorySize=" in line: total_kb = float(line.split("=")[1].strip())
                    if total_kb > 0:
                        used_kb = total_kb - free_kb
                        perf_data["ram"] = {
                            "total": round(total_kb / (1024 * 1024), 1),
                            "used": round(used_kb / (1024 * 1024), 1),
                            "percent": round((used_kb / total_kb) * 100, 1)
                        }
                except Exception:
                    pass

            # 3. GPU (使用原生的 nvidia-smi 替代 torch.cuda.is_available)
            try:
                # 首先测试 nvidia-smi 命令是否存在
                subprocess.check_output("nvidia-smi -L", shell=True, stderr=subprocess.STDOUT)
                has_gpu = True
            except Exception:
                has_gpu = False

            if has_gpu:
                try:
                    vram_out = subprocess.check_output("nvidia-smi --query-gpu=memory.total,memory.used,memory.free --format=csv,noheader,nounits", shell=True).decode("utf-8", errors="ignore")
                    parts = vram_out.strip().split(",")
                    if len(parts) >= 3:
                        t_mb = float(parts[0].strip())
                        u_mb = float(parts[1].strip())
                        perf_data["vram"].update({
                            "has_gpu": True,
                            "total": t_mb,
                            "used": u_mb,
                            "percent": round((u_mb / t_mb) * 100, 1)
                        })
                    
                    name_out = subprocess.check_output("nvidia-smi --query-gpu=name --format=csv,noheader", shell=True).decode("utf-8", errors="ignore").strip()
                    if name_out: perf_data["vram"]["gpu_name"] = name_out
                    
                    util_out = subprocess.check_output("nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits", shell=True).decode("utf-8", errors="ignore").strip()
                    if util_out: perf_data["vram"]["gpu_util"] = float(util_out)
                    
                    temp_out = subprocess.check_output("nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits", shell=True).decode("utf-8", errors="ignore").strip()
                    if temp_out: perf_data["vram"]["gpu_temp"] = float(temp_out)
                except Exception:
                    pass
                    
            # 4. Disk
            try:
                from app.config import STORAGE_BASE
                total, used, free = shutil.disk_usage(str(STORAGE_BASE))
                perf_data["disk"] = {
                    "total": round(total / (1024**3), 1),
                    "used": round(used / (1024**3), 1),
                    "percent": round((used / total) * 100, 1)
                }
            except Exception:
                pass
                
            # 5. Queue
            try:
                qs = queue_manager.task_queue.qsize()
                if queue_manager.get_current_task_id() is not None:
                    qs += 1
                perf_data["queue"]["size"] = qs
            except Exception:
                pass
                
            # 6. LLM Status
            try:
                from app.config import config
                if config.get("summary_mode", "local") == "local":
                    import socket, urllib.parse
                    parsed = urllib.parse.urlparse(config.get("ollama_url", "http://localhost:11434").strip())
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.3)
                    s.connect((parsed.hostname or "localhost", parsed.port or 11434))
                    s.close()
                    perf_data["llm_status"] = "connected"
            except Exception:
                perf_data["llm_status"] = "offline"

            SYSTEM_PERF_CACHE = perf_data
        except Exception as e:
            print(f"⚠️ [PERF] 后台性能监控发生异常: {e}")
        
        # 睡眠 4 秒后继续下一次抓取，完全独立于接口请求频率
        time.sleep(4)

def run_auto_cleanup():
    from datetime import datetime
    import os
    from app.config import load_config
    
    current_cfg = load_config()
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
                # 解析创建时间
                cleaned_date_str = created_at_str
                if "+" in cleaned_date_str:
                    cleaned_date_str = cleaned_date_str.split("+")[0]
                elif "-" in cleaned_date_str and "T" in cleaned_date_str and len(cleaned_date_str) > 19:
                    cleaned_date_str = cleaned_date_str[:19]
                    
                created_dt = datetime.strptime(cleaned_date_str[:19], "%Y-%m-%dT%H:%M:%S")
                age_days = (now - created_dt).days
                
                if age_days >= threshold_days:
                    filename = os.path.basename(audio_url)
                    
                    # 检查音频文件是否被其他更晚创建的任务共享
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
                                
                    # 重置该任务的音频 URL 缓存
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

@app.on_event("startup")
def startup_event():
    # 0. 启动后台独立性能监控线程
    threading.Thread(target=background_perf_monitor, daemon=True).start()
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

    # 3. 运行历史任务语气助词发言人自动标记迁移
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
    enable_email_notification: bool = False
    asr_mode: str = "local"
    online_api_key: str = ""
    online_base_url: str = "https://token-plan-sgp.xiaomimimo.com/v1"
    online_model: str = "mimo-v2.5-asr"
    summary_mode: str = "local"
    online_summary_api_key: str = ""
    online_summary_base_url: str = "https://api.openai.com/v1"
    online_summary_model: str = "gpt-4o-mini"
    enable_llm_semantic_sewing: bool = False
    webhook_url: str = ""
    custom_storage_dir: str = ""
    language: str = "en"


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

# ============================================================
# 四阶段发言人智能识别流水线 (C → B → A → D)
# C: 前置过滤短发言 Speaker
# B: Shownotes 结构化拆分
# A: 两阶段 LLM 推断 (甄别出场人物 → 匹配 Speaker)
# D: 后置交叉验证
# ============================================================

def pre_filter_noise_speakers(transcript: list) -> dict:
    import re
    if not transcript:
        return {}
    speaker_stats = {}
    for seg in transcript:
        sp = seg.get("speaker")
        if not sp:
            continue
        text = seg.get("text", "").strip()
        duration = (seg.get("end", 0) - seg.get("start", 0))
        if sp not in speaker_stats:
            speaker_stats[sp] = {"duration": 0.0, "count": 0, "total_chars": 0, "texts": []}
        speaker_stats[sp]["duration"] += duration
        speaker_stats[sp]["count"] += 1
        speaker_stats[sp]["total_chars"] += len(text)
        speaker_stats[sp]["texts"].append(text)
    
    interjection_chars = set("嗯对啊哦吧呢呀啦哈哼嗨呗嘛呃喔呦哎好的噢唏嚯啥么是吗了嘿哟嗷呐哇")
    noise_speakers = {}
    for sp, stats in speaker_stats.items():
        avg_chars = stats["total_chars"] / max(stats["count"], 1)
        full_text = "".join(stats["texts"])
        cleaned = "".join(c for c in full_text if c.isalnum())
        is_noise = False
        reason = ""
        if not cleaned:
            is_noise = True
            reason = "无实质文本内容"
        elif len(cleaned) <= 15 and all(c in interjection_chars for c in cleaned):
            is_noise = True
            reason = f"纯语气词(总{len(cleaned)}字符)"
        elif stats["duration"] < 30.0 and stats["count"] < 5 and avg_chars < 6:
            is_noise = True
            reason = f"短发言(时长{stats['duration']:.1f}s, {stats['count']}段, 均{avg_chars:.1f}字/段)"
        if is_noise:
            noise_speakers[sp] = "未识别短语"
            print(f"🔇 [LOG] 前置过滤: {sp} 被标记为噪音 speaker -> 原因: {reason} | 总文本: '{full_text[:50]}'")
    return noise_speakers

def split_shownotes(shownotes: str) -> dict:
    import re
    if not shownotes:
        return {"episode_content": "", "template_section": "", "episode_names": set(), "template_names": set()}
    lines = shownotes.split('\n')
    template_markers = [
        r'(?:^|\s)主理人(?:\s|$|[:：])', r'(?:^|\s)主播(?:介绍|简介)',
        r'(?:^|\s)关于(?:节目|我们|本(?:播客|节目))', r'(?:^|\s)About\s',
        r'商务合作', r'(?:^|\s)BGM(?:\s|$|[:：])', r'片(?:头|尾)(?:曲|音乐)',
        r'版权(?:声明|信息)', r'(?:^|\s)联系(?:我们|方式)',
        r'(?:^|\s)(?:微信|微博|公众号|小红书|抖音|B站|视频号|即刻|Twitter|X\.com)(?:\s|$|[:：])',
        r'节目(?:官网|主页|链接)', r'赞助(?:商|合作)',
    ]
    split_index = len(lines)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped: continue
        for marker in template_markers:
            if re.search(marker, stripped):
                if len(stripped) < 30:
                    split_index = i
                    break
        if split_index != len(lines):
            break
    episode_lines = lines[:split_index]
    template_lines = lines[split_index:]
    episode_content = "\n".join(episode_lines).strip()
    template_section = "\n".join(template_lines).strip()
    print(f"📋 [LOG] Shownotes 拆分完成: 本期内容 {len(episode_lines)} 行 | 固定模板 {len(template_lines)} 行 | 分界行: {split_index}")
    
    def extract_names_from_text(text):
        names = set()
        cn_names = re.findall(r'[\u4e00-\u9fa5]{2,4}', text)
        BLACKLIST = {
            "本体", "知识", "图谱", "大模型", "模型", "数据", "信息", "智慧", "导航", "地图",
            "企业", "决策", "因果", "亮点", "时间", "节目", "片头", "片尾", "剪辑", "播客",
            "订阅", "合作", "公司", "连续", "联合", "创始人", "投资", "合伙人", "教授", "博士",
            "导师", "老友", "同学", "作业", "创业", "领域", "行业", "产品", "科技", "算法",
            "代表", "背景", "项目", "引言", "结论", "问题", "逻辑", "体验", "系统", "场景",
            "服务", "接口", "功能", "存量", "增量", "机器", "附庸", "欢迎", "关注", "推荐",
            "干货", "实战", "经验", "探索", "未来", "可能", "朋友", "系列", "单集", "内容",
            "章节", "大纲", "时间戳", "公众号", "视频号", "菜单", "联系", "方式", "主理人",
            "嘉宾", "主播", "主持", "制作", "剪辑", "图形", "主创", "商务", "微信", "微博",
            "关于", "节目", "我们", "版权", "声明", "简介", "介绍", "赞助", "链接",
            "小红书", "抖音", "客服", "运营", "图形学", "不是", "这个", "一个", "什么",
            "那个", "怎么", "可以", "就是", "其实", "所以", "但是", "如果", "因为",
            "认为", "觉得", "知道", "发现", "需要", "能够", "开始", "已经", "正在",
        }
        for name_line in text.split('\n'):
            name_line = name_line.strip()
            if any(role in name_line for role in ["嘉宾", "主理人", "主播", "主持", "主创"]):
                parts = re.split(r'[:：|｜\s\-\—\t\(\)\（\）/、]', name_line)
                for part in parts:
                    part = part.strip()
                    if 2 <= len(part) <= 4 and re.match(r'^[\u4e00-\u9fa5]{2,4}$', part):
                        if part not in BLACKLIST:
                            names.add(part)
        for cn in cn_names:
            if cn not in BLACKLIST and len(cn) >= 2:
                for pattern in [f'{cn}[:：]', f'嘉宾.*{cn}', f'主[理播持].*{cn}', f'{cn}.*(?:说|聊|提到|认为|觉得|先|抛|一直)', f'(?:和|与|跟){cn}']:
                    if re.search(pattern, text):
                        names.add(cn)
                        break
        eng_matches = re.findall(r'\b[A-Z][a-z]{2,12}\b', text)
        eng_blacklist = {"the", "and", "for", "let", "night", "love", "fall", "with", "this", "that", "from", "your", "them", "about", "http", "https", "www", "com"}
        for m in eng_matches:
            if m.lower() not in eng_blacklist:
                names.add(m)
        for word in ["任鑫", "徐文浩", "王昊奋", "十六颗糖", "芒果", "阿乐", "杨一", "Mars", "Allan", "Mango", "Hoffman", "Mongo"]:
            if word in text:
                names.add(word)
        return names
    
    episode_names = extract_names_from_text(episode_content)
    template_names = extract_names_from_text(template_section)
    print(f"👤 [LOG] 本期内容区人名: {episode_names}")
    print(f"📄 [LOG] 固定模板区人名: {template_names}")
    return {"episode_content": episode_content, "template_section": template_section, "episode_names": episode_names, "template_names": template_names}

def _call_llm_api(prompt: str, summary_mode: str = None, label: str = "LLM调用") -> str:
    import httpx
    from app.config import config
    from app.core.summarizer import doh_dns_bypass
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
            response = client.post(api_url, headers=headers, json=payload)
            if response.status_code == 200: print(f"🟢 [LOG] {label} 代理请求成功！")
    except Exception as e_proxy:
        print(f"⚠️ [LOG] {label} 代理请求失败: {e_proxy}。正在尝试直连与 DoH 绕过...")
    if response is None or response.status_code != 200:
        try:
            with doh_dns_bypass(api_url):
                with httpx.Client(timeout=120.0, trust_env=False) as client:
                    response = client.post(api_url, headers=headers, json=payload)
                    if response.status_code == 200: print(f"🟢 [LOG] {label} 直连(DoH DNS 绕过)成功！")
        except Exception as e_doh:
            print(f"❌ [LOG] {label} 直连(DoH DNS 绕过)请求失败: {e_doh}")
    if response is None or response.status_code != 200:
        detail_msg = response.text if response is not None else "无响应"
        status_code = response.status_code if response is not None else "未知"
        raise Exception(f"{label} 接口请求失败，状态码: {status_code}，详情: {detail_msg}")
    res_data = response.json()
    return res_data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

def _llm_identify_participants(title: str, episode_content: str, template_names: set, summary_mode: str = None) -> list:
    import json
    template_names_list = list(template_names) if template_names else []
    prompt = f"你是一个播客分析助手。我需要你分析一期播客节目的简介，判断哪些人**真正参与了本期节目的录制**。\n\n播客标题：《{title}》\n\n以下是本期节目简介的**内容部分**（章节大纲、亮点、讨论要点等）：\n---\n{episode_content}\n---\n\n该节目的固定主理人/主播名单（可能有人本期没参加）：{json.dumps(template_names_list, ensure_ascii=False)}\n\n请根据以上内容，分析并列出**本期节目中真正参与录制/发言的人物**。\n\n判断标准：\n1. 如果内容描述中提到某人'说了什么'、'聊了什么'、'提出了什么观点'、'和嘉宾对话'等主动行为 → 该人参与了\n2. 如果某人仅出现在'嘉宾介绍'等背景性文字中，描述的是其身份/头衔而非本期发言 → 也算参与了（嘉宾）\n3. 如果某人只出现在固定模板的主理人列表里，在本期内容描述中完全没被提及 → 该人本期未参与\n4. 优先识别具体的人名，而不是泛称（如'主持人'）\n\n请仅返回一个 JSON 数组，包含本期确认参与的人名，例如：[\"任鑫\", \"王昊奋\", \"芒果\"]\n不要包含任何解释文字、MarkDown标记或```json标签，直接输出 JSON 数组。"
    try:
        response_text = _call_llm_api(prompt, summary_mode, label="出场人物甄别")
        if "```json" in response_text: response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text: response_text = response_text.split("```")[1].split("```")[0].strip()
        response_text = response_text.strip()
        participants = json.loads(response_text)
        if isinstance(participants, list):
            print(f"✅ [LOG] 阶段A-1 出场人物甄别完成: {participants}")
            return participants
        else:
            print(f"⚠️ [LOG] 阶段A-1 返回格式异常(非数组): {participants}")
            return list(template_names) if template_names else []
    except Exception as e:
        print(f"⚠️ [LOG] 阶段A-1 出场人物甄别失败: {e}，回退为全部模板人名")
        return list(template_names) if template_names else []

def _llm_match_speakers(participants: list, transcript: list, unmatched_speakers: list, known_mappings: dict, title: str, summary_mode: str = None) -> dict:
    import json
    import re
    if not unmatched_speakers or not participants: return {}
    def is_clean_text(text: str) -> bool:
        t = text.lower()
        return not ("request was rejected" in t or "considered high risk" in t or "internal server error" in t)
    
    transcript_sample = []
    sampled_speakers = set()
    for seg in transcript[:40]:
        text = seg.get('text', '').strip()
        if not is_clean_text(text): continue
        speaker_tag = seg.get("speaker", "UNKNOWN")
        sampled_speakers.add(speaker_tag)
        speaker_name = known_mappings.get(speaker_tag, speaker_tag)
        transcript_sample.append(f"【{speaker_name}】: {text}")
    
    for sp in unmatched_speakers:
        if sp not in sampled_speakers:
            sp_segs = [seg for seg in transcript if seg.get("speaker") == sp]
            valid_segs = []
            for seg in sp_segs:
                txt = seg.get('text', '').strip()
                if txt and is_clean_text(txt):
                    valid_segs.append(f"【{sp}】: {txt}")
                if len(valid_segs) >= 3: break
            if valid_segs:
                transcript_sample.append(f"\n--- 发言人 {sp} 后续的部分发言片段 ---")
                transcript_sample.extend(valid_segs)
    
    candidate_list = [p.lower() for p in participants] + participants
    matching_indices = []
    for i, seg in enumerate(transcript):
        text = seg.get("text", "")
        for cand in candidate_list:
            if cand.lower() in text.lower():
                matching_indices.append(i)
                break
    
    selected_indices = matching_indices[:15] if len(matching_indices) <= 15 else [matching_indices[int(round(idx * (len(matching_indices) - 1) / 14))] for idx in range(15)]
    ranges = [(max(0, idx - 1), min(len(transcript) - 1, idx + 1)) for idx in selected_indices]
    merged_ranges = []
    if ranges:
        ranges.sort()
        curr_start, curr_end = ranges[0]
        for r_start, r_end in ranges[1:]:
            if r_start <= curr_end + 1: curr_end = max(curr_end, r_end)
            else:
                merged_ranges.append((curr_start, curr_end))
                curr_start, curr_end = r_start, r_end
        merged_ranges.append((curr_start, curr_end))
    
    if merged_ranges:
        transcript_sample.append("\n=== 💡 检索到的关键姓名/角色提及对话上下文片段 ===")
        for r_start, r_end in merged_ranges:
            transcript_sample.append(f"\n[提及片段 - 对应时间: {transcript[r_start].get('start', 0):.1f}s - {transcript[r_end].get('end', 0):.1f}s]")
            for i in range(r_start, r_end + 1):
                seg = transcript[i]
                text = seg.get('text', '').strip()
                if not is_clean_text(text): continue
                speaker_tag = seg.get("speaker", "UNKNOWN")
                speaker_name = known_mappings.get(speaker_tag, speaker_tag)
                transcript_sample.append(f"【{speaker_name}】: {text}")
    
    transcript_text = "\n".join(transcript_sample)
    tips = []
    participants_str = " ".join(participants)
    if "任鑫" in participants_str: tips.append("Mars 是任鑫的英文名/代号")
    if "徐文浩" in participants_str: tips.append("Allan 是徐文浩的英文名/代号")
    if "芒果" in participants_str or "Mango" in participants_str: tips.append("Mango/芒果 是同一个人的代号")
    if "王昊奋" in participants_str: tips.append("Hoffman 是王昊奋的英文名/代号")
    tips_text = "提示信息（供推断参考）：\n" + "\n".join(f"- {t}" for t in tips) + "\n" if tips else ""
    
    prompt = f"我们有一个播客单集，标题是《{title}》。\n\n【本期确认出场的人物名单】：{json.dumps(participants, ensure_ascii=False)}\n（注意：你只能从上面这个名单中进行匹配，不能使用名单之外的人名！）\n\n以下是该单集不同发言人的一些对话文本片段：\n---\n{transcript_text}\n---\n\n{tips_text}已知的部分角色匹配：\n{json.dumps(known_mappings, ensure_ascii=False)}\n\n请通过分析对话文本中人物之间的称呼、打招呼方式、自我介绍以及发言内容，推断出以下未匹配的 SPEAKER ID 对应名单里的哪位具体人物：\n未匹配列表: {unmatched_speakers}\n\n注意：\n1. 仅返回一个简洁的 JSON 格式的字典映射，例如：{{\"SPEAKER_00\": \"张三\", \"SPEAKER_01\": \"李四\"}}\n2. 不要包含任何 MarkDown 格式标记（如 ```json 标签），也不要包含任何解释性文字，直接输出 JSON 纯文本。\n3. 你**只能**从上面的【本期确认出场的人物名单】中选择名字进行匹配。如果无法唯一确定，请返回 null。\n4. 如果未匹配的 speaker 数量多于出场人物名单中剩余的人数，那多余的 speaker 必须返回 null。\n5. 语音分割容错：有时一个发言人的简短话语可能被错误合并到另一个发言人的片段里，请结合整体上下文判断。"
    try:
        response_text = _call_llm_api(prompt, summary_mode, label="Speaker匹配")
        if "```json" in response_text: response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text: response_text = response_text.split("```")[1].split("```")[0].strip()
        response_text = response_text.strip()
        llm_mappings = json.loads(response_text)
        valid_mappings = {}
        for k, v in llm_mappings.items():
            if k in unmatched_speakers and v and isinstance(v, str):
                valid_mappings[k] = v
                print(f"🤖 [LOG] 阶段A-2 匹配成功: {k} -> {v}")
        return valid_mappings
    except Exception as e:
        print(f"⚠️ [LOG] 阶段A-2 Speaker匹配失败: {e}")
        return {}

def _validate_mappings(llm_mappings: dict, episode_content: str, episode_names: set, template_names: set) -> dict:
    if not llm_mappings: return {}
    validated = {}
    name_to_speakers = {}
    for sp, name in llm_mappings.items():
        if name: name_to_speakers.setdefault(name, []).append(sp)
    duplicate_names = {name for name, sps in name_to_speakers.items() if len(sps) > 1}
    if duplicate_names: print(f"⚠️ [LOG] 阶段D 检测到重复分配的名字: {duplicate_names} -> 全部降级为 null")
    for sp, name in llm_mappings.items():
        if not name: continue
        if name in duplicate_names:
            print(f"🚫 [LOG] 阶段D 验证失败: {sp} -> '{name}' (名字被分配给多个 speaker，降级)")
            continue
        name_in_episode = name in episode_names or any(name in n for n in episode_names) or any(n in name for n in episode_names)
        name_in_template = name in template_names or any(name in n for n in template_names) or any(n in name for n in template_names)
        name_mentioned_in_content = name.lower() in episode_content.lower() if episode_content else False
        if name_in_template and not name_in_episode and not name_mentioned_in_content:
            print(f"🚫 [LOG] 阶段D 验证失败: {sp} -> '{name}' (仅存在于固定模板区，本期内容未提及，降级)")
            continue
        validated[sp] = name
        print(f"✅ [LOG] 阶段D 验证通过: {sp} -> '{name}'")
    return validated

def match_speakers_with_llm(metadata: dict, transcript: list, unmatched_speakers: list, known_mappings: dict, summary_mode: str = None, noise_speakers: dict = None, shownotes_split: dict = None) -> dict:
    import json
    if not unmatched_speakers: return {}
    try:
        title = metadata.get("title", "")
        if shownotes_split is None: shownotes_split = split_shownotes(metadata.get("shownotes", ""))
        episode_content = shownotes_split.get("episode_content", "")
        template_names = shownotes_split.get("template_names", set())
        episode_names = shownotes_split.get("episode_names", set())
        participants = _llm_identify_participants(title, episode_content, template_names, summary_mode)
        if not participants:
            print("⚠️ [LOG] 阶段A-1 未识别到任何出场人物，跳过阶段A-2")
            return {}
        llm_mappings = _llm_match_speakers(participants, transcript, unmatched_speakers, known_mappings, title, summary_mode)
        print(f"🤖 [LOG] 阶段A-2 原始匹配结果: {llm_mappings}")
        validated_mappings = _validate_mappings(llm_mappings, episode_content, episode_names, template_names)
        print(f"✅ [LOG] 阶段D 最终验证后结果: {validated_mappings}")
        return validated_mappings
    except Exception as e:
        print(f"⚠️ [LOG] 四阶段发言人识别流水线失败: {e}")
    return {}

def auto_rename_speakers(task_id: str, metadata: dict, transcript: list, speaker_embeddings: dict):
    from app.database import db
    if not transcript: return
    task = db.get_task(task_id)
    if not task: return
    summary_mode = task.get("summary_mode", "local")
    print(f"🚀 [LOG] 正在对任务 {task_id} 启动四阶段智能识别流水线... (总结模式: {summary_mode})")
    all_speakers = set(seg.get("speaker") for seg in transcript if seg.get("speaker"))
    noise_speakers = pre_filter_noise_speakers(transcript)
    real_speakers = list(all_speakers - set(noise_speakers.keys()))
    print(f"🔇 [LOG] 阶段C 完成: 过滤 {len(noise_speakers)} 个噪音 speaker，剩余 {len(real_speakers)} 个实质 speaker: {real_speakers}")
    shownotes_split = split_shownotes(metadata.get("shownotes", ""))
    llm_mappings = match_speakers_with_llm(metadata, transcript, real_speakers, known_mappings={}, summary_mode=summary_mode, noise_speakers=noise_speakers, shownotes_split=shownotes_split)
    print(f"🤖 [LOG] 阶段A+D 完成: {llm_mappings}")
    voiceprint_mappings = {}
    unmatched_speakers = set(real_speakers) - set(llm_mappings.keys())
    if unmatched_speakers and speaker_embeddings:
        unmatched_embeddings = {sp: speaker_embeddings[sp] for sp in unmatched_speakers if sp in speaker_embeddings}
        if unmatched_embeddings:
            voiceprint_mappings = match_speakers_with_voiceprints(unmatched_embeddings)
            print(f"🔍 [LOG] 声纹库对比兜底完成: {voiceprint_mappings}")
    final_mappings = {**noise_speakers, **voiceprint_mappings, **llm_mappings}
    if final_mappings:
        existing_mappings = task.get("speaker_mappings", {})
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
    import time
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

        # Step 4.5: 提取声纹特征特征，并进行智能特征及上下文改名
        if not db.get_task(task_id):
            raise Exception("TASK_CANCELLED")
        try:
            print("⏳ [LOG] 正在提取发言人声纹特征向量...")
            speaker_embeddings = transcriber.extract_speaker_embeddings(standardized_wav, diar_data)
            db.update_task(task_id, speaker_embeddings=speaker_embeddings)
            
            # 如果聚类修正合并了 SPEAKER，需要同步更新已有的 transcript 和段落
            # diar_data 已被 extract_speaker_embeddings 原地修改，这里用它来检测合并
            diar_speakers = set(seg["speaker"] for seg in diar_data)
            transcript_speakers = set(seg.get("speaker") for seg in merged_transcript)
            merged_away = transcript_speakers - diar_speakers  # 在 transcript 中存在但 diar 中已被合并的 speaker
            if merged_away:
                # 构建反向映射：被合并的 speaker -> 对应的 diar_data 中最近时间段的 speaker
                reverse_map = {}
                for old_sp in merged_away:
                    # 找这个 speaker 在 transcript 中的第一条记录的时间
                    for seg in merged_transcript:
                        if seg.get("speaker") == old_sp:
                            seg_center = (seg.get("start", 0) + seg.get("end", 0)) / 2
                            # 在 diar_data 中找包含此时间点的 speaker
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
                    
                    # 同步更新段落
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
            
            # 运行智能改名流水线
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

        # Step 6: 消息/邮件提醒
        task_info = db.get_task(task_id)
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

import math

def sanitize_floats(obj):
    if isinstance(obj, dict):
        return {k: sanitize_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_floats(x) for x in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
    return obj

@app.get("/api/tasks/{task_id}")
def get_task_details(task_id: str):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="未找到该任务")
    # 动态注入排队位置
    if task.get("status") == "pending":
        pos = queue_manager.get_queue_position(task.get("id"))
        task["queue_position"] = pos
        
    # 注入段落与沉淀状态
    if task.get("status") == "completed":
        try:
            paragraphs = db.get_paragraphs_by_podcast(task_id)
            is_old_format = paragraphs and len(paragraphs) > 0 and ("sentences" not in paragraphs[0] or not isinstance(paragraphs[0].get("sentences"), list))
            if (not paragraphs or is_old_format) and task.get("transcript"):
                paragraphs = transcriber.cluster_segments_to_paragraphs(task_id, task.get("transcript"))
                db.delete_paragraphs_by_podcast(task_id)
                db.add_paragraphs(paragraphs)
            
            # Check sedimented status
            podcast_cards = db.get_cards_by_podcast(task_id)
            sedimented_paragraph_ids = {c["paragraph_id"] for c in podcast_cards}
            for p in paragraphs:
                p["sedimented"] = p["id"] in sedimented_paragraph_ids
                
            task["paragraphs"] = paragraphs
        except Exception as e:
            print(f"⚠️ [LOG ERROR] Failed to inject paragraphs: {e}")
            task["paragraphs"] = []
    else:
        task["paragraphs"] = []
        
    return sanitize_floats(task)

@app.get("/api/performance")
def get_performance():
    # 彻底解耦：直接 0.1 毫秒内返回全局内存缓存，不再卡住线程池！
    return SYSTEM_PERF_CACHE

@app.post("/api/tasks")
def create_task(req: CreateTaskRequest):
    task_id = str(uuid.uuid4())
    curr_summary_mode = config.get("summary_mode", "local")
    db.add_task(task_id, req.url, asr_mode=req.asr_mode, summary_mode=curr_summary_mode)
    
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
    curr_summary_mode = config.get("summary_mode", "local")
    db.add_task(task_id, local_path, asr_mode=asr_mode, summary_mode=curr_summary_mode)
    
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

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
        
    # 物理清除下载的 MP3 文件以释放硬盘，前提是该音频没有被其他任务共享
    audio_url = task.get("audio_url")
    if audio_url:
        filename = os.path.basename(audio_url)
        
        # 扫描是否有其他任务也在使用这个文件名
        other_tasks = [t for t in db.get_all_tasks() if t.get("id") != task_id]
        is_shared = False
        for ot in other_tasks:
            ot_audio = ot.get("audio_url")
            if ot_audio and os.path.basename(ot_audio) == filename:
                is_shared = True
                break
                
        if is_shared:
            print(f"ℹ️ [LOG] 任务删除 - 音频文件 {filename} 被其他任务共享，跳过物理删除。")
        else:
            local_file_path = os.path.join(SHORT_DOWNLOADS_DIR, filename)
            if os.path.exists(local_file_path):
                try:
                    os.remove(local_file_path)
                    print(f"🗑️ [LOG] 任务删除 - 已物理清除音频文件: {local_file_path}")
                except Exception as e:
                    print(f"⚠️ [LOG 警告] 无法删除物理音频: {e}")

    success = db.delete_task(task_id)
    return {"success": success}

@app.post("/api/tasks/{task_id}/redownload")
def redownload_task_audio(task_id: str, background_tasks: BackgroundTasks):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
        
    audio_url = task.get("audio_url")
    if not audio_url:
        raise HTTPException(status_code=400, detail="任务没有关联的音频文件名")
        
    filename = os.path.basename(audio_url)
    local_file_path = os.path.join(SHORT_DOWNLOADS_DIR, filename)
    
    if os.path.exists(local_file_path):
        return {"success": True, "message": "音频文件已存在，无需重新下载"}
        
    # 在数据库中初始化修复状态和进度
    db.update_task(task_id, restoring=True, restore_progress=0.0)
        
    # 启动后台任务进行下载修复
    def do_redownload():
        try:
            print(f"📥 [LOG] 启动后台音频修复重新下载, 原始链接: {task['url']}")
            
            def restore_progress_callback(percent):
                db.update_task(task_id, restore_progress=round(percent, 1))
                
            local_path, metadata = downloader.download_url_audio(task['url'], progress_callback=restore_progress_callback)
            
            # 如果下载后的文件名和数据库记录的不一致，则将其重命名
            downloaded_filename = os.path.basename(local_path)
            if downloaded_filename != filename:
                downloaded_expected_path = os.path.join(SHORT_DOWNLOADS_DIR, downloaded_filename)
                expected_path = os.path.join(SHORT_DOWNLOADS_DIR, filename)
                shutil.move(downloaded_expected_path, expected_path)
            print(f"✅ [LOG] 音频文件修复重新下载成功: {filename}")
            db.update_task(task_id, restoring=False, restore_progress=100.0)
        except Exception as e:
            print(f"❌ [LOG] 音频文件修复重新下载失败: {e}")
            db.update_task(task_id, restoring=False, restore_progress=0.0)
            
    background_tasks.add_task(do_redownload)
    return {"success": True, "message": "已在后台启动音频文件下载修复"}

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
                speaker_mappings=task.get("speaker_mappings"),
                summary_mode=task.get("summary_mode", "local")
            )
            db.update_task(task_id, status="completed", summary=summary_report, progress=100.0)
        except Exception as ex:
            db.update_task(task_id, status="failed", error_message=str(ex), progress=100.0)

    background_tasks.add_task(run_re_summarize)
    return {"status": "summarizing"}

@app.post("/api/tasks/{task_id}/metadata/refresh")
def refresh_metadata(task_id: str):
    """
    重新抓取播客的最新点赞数、评论数、简介/Shownotes等，实时同步到本地库中
    """
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="未找到任务")
    
    url = task.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="本地上传任务没有源链接，无法刷新元数据")
        
    try:
        new_metadata = downloader.parse_metadata(url)
        
        # 合并最新的元数据
        old_meta = task.get("metadata", {}) or {}
        for k, v in new_metadata.items():
            if v is not None:
                old_meta[k] = v
                
        # 更新数据库
        updated_t = db.update_task(
            task_id,
            metadata=old_meta,
            title=new_metadata.get("title", task.get("title")),
            podcast_name=new_metadata.get("podcast_name", task.get("podcast_name")),
            image_url=new_metadata.get("image_url", task.get("image_url"))
        )
        return {
            "success": True, 
            "task": {
                "id": updated_t.get("id"),
                "url": updated_t.get("url"),
                "asr_mode": updated_t.get("asr_mode", "local"),
                "summary_mode": updated_t.get("summary_mode", "local"),
                "title": updated_t.get("title", "未命名任务"),
                "podcast_name": updated_t.get("podcast_name", "未知播客"),
                "status": updated_t.get("status", "pending"),
                "progress": updated_t.get("progress", 0),
                "created_at": updated_t.get("created_at"),
                "error_message": updated_t.get("error_message"),
                "like_count": updated_t.get("metadata", {}).get("like_count", 0),
                "comment_count": updated_t.get("metadata", {}).get("comment_count", 0),
                "obsidian_synced": updated_t.get("obsidian_synced", False),
                "image_url": updated_t.get("image_url", ""),
                "duration": updated_t.get("duration", "00:00"),
                "metadata": {
                    "pub_date": updated_t.get("metadata", {}).get("pub_date", ""),
                    "source": updated_t.get("metadata", {}).get("source", ""),
                    "duration": updated_t.get("metadata", {}).get("duration", "00:00")
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新元数据失败: {str(e)}")

import urllib.request
import json
import time
from threading import Thread

# 内存级版本缓存，防 GitHub API 频限与加载延迟
VERSION_CHECK_CACHE = {
    "last_checked": 0.0,
    "latest_version": None,
    "has_update": False,
    "release_url": "https://github.com/quentin2001/whisperMe/releases",
    "release_notes": ""
}

def parse_version_tuple(v_str: str) -> list:
    try:
        # 去掉 'v' 前缀并分割
        cleaned = v_str.strip().lower().lstrip('v').split('-')[0]
        return [int(p) for p in cleaned.split('.') if p.isdigit()]
    except Exception:
        return [0, 0, 0]

def fetch_latest_release_worker():
    global VERSION_CHECK_CACHE
    try:
        url = "https://api.github.com/repos/quentin2001/whisperMe/releases/latest"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "whisperMe-Updater-FastAPI"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                tag_name = data.get("tag_name", "").strip()
                html_url = data.get("html_url", "https://github.com/quentin2001/whisperMe/releases")
                body = data.get("body", "")
                
                if tag_name:
                    local_t = parse_version_tuple(CURRENT_VERSION)
                    remote_t = parse_version_tuple(tag_name)
                    has_update = remote_t > local_t
                    
                    VERSION_CHECK_CACHE.update({
                        "latest_version": tag_name,
                        "has_update": has_update,
                        "release_url": html_url,
                        "release_notes": body,
                        "last_checked": time.time()
                    })
                    return
    except Exception as e:
        # 网络超时、未发布 Release (404) 或触发频限等情况，执行优雅降级
        print(f"[Version Check] Error fetching from GitHub: {str(e)}")
        
        # 特殊处理：如果是用于测试更新界面的本地 0.9.0 版本，即使遇到频限或报错也直接模拟有更新
        if CURRENT_VERSION == "0.9.0":
            VERSION_CHECK_CACHE.update({
                "latest_version": "v1.0.0",
                "has_update": True,
                "release_url": "https://github.com/quentin2001/whisperMe/releases/tag/v1.0.0",
                "release_notes": "whisperMe v1.0.0 初始发布版本。支持本地/在线 ASR 转写与 AI 摘要分析。",
                "last_checked": time.time()
            })
            return
        
    # 正常降级：最新版本等同于本地版本，避免报错
    VERSION_CHECK_CACHE.update({
        "latest_version": CURRENT_VERSION,
        "has_update": False,
        "last_checked": time.time()
    })

def trigger_version_check():
    thread = Thread(target=fetch_latest_release_worker)
    thread.daemon = True
    thread.start()

@app.get("/api/version/check")
def check_software_version(force: bool = False):
    global VERSION_CHECK_CACHE
    # 强制检查，或者缓存过期判定：未检查过，或者距离上次检查超过 12 小时 (43200 秒)
    if force or VERSION_CHECK_CACHE["latest_version"] is None or (time.time() - VERSION_CHECK_CACHE["last_checked"] > 43200):
        if force:
            # 强制检查时，直接同步执行以获取最新结果返回给客户端
            fetch_latest_release_worker()
        else:
            trigger_version_check()
            if VERSION_CHECK_CACHE["latest_version"] is None:
                wait_start = time.time()
                while time.time() - wait_start < 1.5:
                    if VERSION_CHECK_CACHE["latest_version"] is not None:
                        break
                    time.sleep(0.05)
                
    latest = VERSION_CHECK_CACHE["latest_version"] or CURRENT_VERSION
    local_t = parse_version_tuple(CURRENT_VERSION)
    remote_t = parse_version_tuple(latest)
    has_update = remote_t > local_t
    
    return {
        "current_version": CURRENT_VERSION,
        "latest_version": latest,
        "has_update": has_update,
        "release_url": VERSION_CHECK_CACHE["release_url"],
        "release_notes": VERSION_CHECK_CACHE["release_notes"]
    }

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

@app.get("/api/prompt")
def get_prompt():
    return load_prompt()

@app.post("/api/prompt")
def set_prompt(req: dict):
    save_prompt(req)
    return {"status": "ok"}

# ==================== 🧠 认知沙盒 API 端点 ====================
import random
import json

class CreateCardRequest(BaseModel):
    paragraph_id: str
    podcast_id: str
    board_id: str = "board_default"

class ReviewCardRequest(BaseModel):
    direction: str  # "left" or "right"

class CreateLinkRequest(BaseModel):
    source_card_id: str
    target_card_id: str
    my_synthesis: str = ""
    board_id: str = None



def call_llm(prompt: str) -> str:
    import httpx
    from app.config import config
    
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
    
    with httpx.Client(timeout=120.0, trust_env=False) as client:
        response = client.post(api_url, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"LLM API error (code {response.status_code}): {response.text}")
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()

@app.get("/api/paragraphs")
def get_paragraphs(podcast_id: str):
    paragraphs = db.get_paragraphs_by_podcast(podcast_id)
    is_old_format = paragraphs and len(paragraphs) > 0 and ("sentences" not in paragraphs[0] or not isinstance(paragraphs[0].get("sentences"), list))
    if not paragraphs or is_old_format:
        # Check if task exists and has a transcript
        task = db.get_task(podcast_id)
        if not task or not task.get("transcript"):
            return []
        try:
            print(f"🔄 [LOG] 为老任务 {podcast_id} 动态生成（或重新生成）语义段落...")
            paragraphs = transcriber.cluster_segments_to_paragraphs(podcast_id, task.get("transcript"))
            db.delete_paragraphs_by_podcast(podcast_id)
            db.add_paragraphs(paragraphs)
        except Exception as e:
            print(f"❌ [LOG ERROR] 动态生成段落失败: {e}")
            return []
    
    # Check if each paragraph has been sedimented (has an associated card)
    podcast_cards = db.get_cards_by_podcast(podcast_id)
    sedimented_paragraph_ids = {c["paragraph_id"] for c in podcast_cards}
    for p in paragraphs:
        p["sedimented"] = p["id"] in sedimented_paragraph_ids
        
    return paragraphs

@app.post("/api/cards/create")
def create_card(req: CreateCardRequest):
    # Check if card already exists for this paragraph
    existing_cards = db.get_all_cards()
    for c in existing_cards:
        if c.get("paragraph_id") == req.paragraph_id:
            return c

    # Fetch paragraph
    paragraphs = db.get_paragraphs_by_podcast(req.podcast_id)
    paragraph = None
    for p in paragraphs:
        if p["id"] == req.paragraph_id:
            paragraph = p
            break
            
    if not paragraph:
        # Try generating on the fly
        paragraphs = get_paragraphs(req.podcast_id)
        for p in paragraphs:
            if p["id"] == req.paragraph_id:
                paragraph = p
                break
    
    if not paragraph:
        raise HTTPException(status_code=404, detail="未找到对应的语义段落")
        
    # Call LLM to extract spark_title and why_it_matters
    quote = paragraph["content"]
    prompt = f"""你是一个知识内化与卡片记忆提取专家。
请根据下面的播客转录原话，提取出一个闪光标题（Spark Title）和为何重要（Why It Matters）的解释。

原话内容：
「{quote}」

要求：
1. 闪光标题：精炼、醒目、深刻，能一针见血指出这段话的核心观点，不超过 15 字。
2. 为何重要：用一两句话解释该观点的含金量、底层逻辑或启发性意义，语气理性中肯，不超过 60 字。
3. 必须以 JSON 格式输出，包含 "spark_title" 和 "why_it_matters" 两个字段。
4. 不要包含 ```json 或 ``` 格式块，只输出纯 JSON 字符串，不要有任何其他内容。"""

    try:
        response_str = call_llm(prompt)
        cleaned_str = response_str.strip()
        if cleaned_str.startswith("```json"):
            cleaned_str = cleaned_str[7:]
        if cleaned_str.startswith("```"):
            cleaned_str = cleaned_str[3:]
        if cleaned_str.endswith("```"):
            cleaned_str = cleaned_str[:-3]
        cleaned_str = cleaned_str.strip()
        
        parsed = json.loads(cleaned_str)
        spark_title = parsed.get("spark_title", "未命名观点").strip()
        why_it_matters = parsed.get("why_it_matters", "原话具有深刻启发意义。").strip()
    except Exception as e:
        print(f"⚠️ [LOG ERROR] LLM 卡片提炼失败: {e}")
        # Fallback values
        spark_title = quote[:15] + "..." if len(quote) > 15 else quote
        why_it_matters = "由于大模型连接失败或解析异常，该卡片以默认模式生成。原话非常关键，值得反复记忆复习。"

    from datetime import datetime, timedelta
    card_id = str(uuid.uuid4())
    tomorrow = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    card = {
        "id": card_id,
        "paragraph_id": req.paragraph_id,
        "podcast_id": req.podcast_id,
        "spark_title": spark_title,
        "quote": quote,
        "why_it_matters": why_it_matters,
        "efactor": 2.5,
        "interval": 1,
        "next_review_date": tomorrow,
        "status": "active",
        "created_at": datetime.now().isoformat()
    }
    
    db.create_card(card)
    if req.board_id:
        db.add_card_to_board(req.board_id, card_id)
    return card

@app.delete("/api/cards/paragraph/{paragraph_id}")
def delete_card_by_paragraph(paragraph_id: str):
    cards = db.get_all_cards()
    card_to_delete = None
    for c in cards:
        if c.get("paragraph_id") == paragraph_id:
            card_to_delete = c
            break
            
    if not card_to_delete:
        raise HTTPException(status_code=404, detail="未找到该段落对应的卡片")
        
    success = db.delete_card(card_to_delete["id"])
    if not success:
        raise HTTPException(status_code=500, detail="删除卡片失败")
        
    return {"status": "ok", "deleted_card_id": card_to_delete["id"]}

class UpdateCardPositionRequest(BaseModel):
    x: float
    y: float

@app.put("/api/cards/{card_id}/position")
def update_card_position(card_id: str, req: UpdateCardPositionRequest):
    card = db.get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="卡片未找到")
    
    updated_card = db.update_card(card_id, pos_x=req.x, pos_y=req.y)
    return {"status": "ok", "card": updated_card}

# ==================== BOARDS API ====================
@app.get("/api/boards")
def get_boards():
    return db.get_all_boards()

class CreateBoardRequest(BaseModel):
    name: str

@app.post("/api/boards")
def create_board(req: CreateBoardRequest):
    import uuid
    b_id = f"board_{uuid.uuid4().hex[:12]}"
    return db.create_board(b_id, req.name)

class AddCardToBoardRequest(BaseModel):
    card_id: str
    pos_x: float = 0.0
    pos_y: float = 0.0

@app.post("/api/boards/{board_id}/cards")
def add_card_to_board(board_id: str, req: AddCardToBoardRequest):
    db.add_card_to_board(board_id, req.card_id, req.pos_x, req.pos_y)
    return {"status": "ok"}

@app.put("/api/boards/{board_id}/cards/{card_id}/position")
def update_board_card_position(board_id: str, card_id: str, req: UpdateCardPositionRequest):
    db.update_board_card_position(board_id, card_id, req.x, req.y)
    return {"status": "ok"}

@app.get("/api/cards")
def get_cards(board_id: str = None):
    if board_id:
        cards = db.get_cards_by_board(board_id)
    else:
        cards = db.get_all_cards()
    # Populate with podcast info (title, image_url, etc.)
    for c in cards:
        task = db.get_task(c["podcast_id"])
        if task:
            c["podcast_title"] = task.get("title", "未知标题")
            c["podcast_image_url"] = task.get("image_url", "")
            c["podcast_name"] = task.get("podcast_name", "未知播客")
            
            # Find the paragraph start_time & end_time
            paras = db.get_paragraphs_by_podcast(c["podcast_id"])
            for p in paras:
                if p["id"] == c["paragraph_id"]:
                    c["start_time"] = p.get("start_time", 0)
                    c["end_time"] = p.get("end_time", 0)
                    break
    return cards

@app.get("/api/cards/due")
def get_due_cards():
    from datetime import datetime
    today = datetime.today().strftime("%Y-%m-%d")
    all_cards = db.get_all_cards()
    
    # Filter for active and warning cards
    valid_cards = [c for c in all_cards if c.get("status") in ["active", "warning"]]
    
    # Filter due cards
    due_cards = [c for c in valid_cards if c.get("next_review_date", "") <= today]
    
    # Sort due cards: prioritize warnings first, then recently created
    due_cards.sort(key=lambda x: (0 if x.get("status") == "warning" else 1, x.get("created_at", "")), reverse=True)
    
    # Populate podcast details
    def populate_card_details(c):
        task = db.get_task(c["podcast_id"])
        if task:
            c["podcast_title"] = task.get("title", "未知标题")
            c["podcast_image_url"] = task.get("image_url", "")
            c["podcast_name"] = task.get("podcast_name", "未知播客")
            # Get start/end time
            paras = db.get_paragraphs_by_podcast(c["podcast_id"])
            for p in paras:
                if p["id"] == c["paragraph_id"]:
                    c["start_time"] = p.get("start_time", 0)
                    c["end_time"] = p.get("end_time", 0)
                    break
        return c

    due_cards = [populate_card_details(c) for c in due_cards]
    
    # If we have at least 3 due cards, return the top 3
    if len(due_cards) >= 3:
        return due_cards[:3]
        
    # Otherwise, backfill with random active/warning cards that are NOT due
    non_due_cards = [c for c in valid_cards if c.get("next_review_date", "") > today]
    import random
    random.shuffle(non_due_cards)
    
    needed = 3 - len(due_cards)
    backfill_cards = non_due_cards[:needed]
    backfill_cards = [populate_card_details(c) for c in backfill_cards]
    
    result = due_cards + backfill_cards
    # If still less than 3, just return whatever we have
    return result

@app.post("/api/cards/{card_id}/review")
def review_card(card_id: str, req: ReviewCardRequest):
    card = db.get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")
        
    from datetime import datetime, timedelta
    today = datetime.today()
    
    efactor = card.get("efactor", 2.5)
    interval = card.get("interval", 1)
    
    if req.direction == "left":
        # Tamed (Success, quality = 4)
        new_status = "active"
        if interval == 1:
            new_interval = 6
        elif interval == 6:
            new_interval = 12
        else:
            new_interval = int(round(interval * efactor))
            
        new_efactor = efactor
        next_date = (today + timedelta(days=new_interval)).strftime("%Y-%m-%d")
    else:
        # Forgot (Failure, quality = 1)
        new_status = "warning"
        new_interval = 1
        new_efactor = max(1.3, efactor - 0.2)
        next_date = (today + timedelta(days=1)).strftime("%Y-%m-%d") # Review again tomorrow
        
        # Trigger notifier!
        try:
            task = db.get_task(card["podcast_id"])
            podcast_title = task.get("title", "未知标题") if task else "未知播客"
            podcast_name = task.get("podcast_name", "未知播客") if task else "未知播客"
            
            # Send desktop notification
            notifier.send_desktop_notification(
                title=f"🧠 记忆唤醒警报: 【{card['spark_title']}】",
                message=f"该卡片已被设为遗忘提醒。原文: {card['quote'][:60]}..."
            )
            
            # If webhook is configured
            webhook_url = config.get("webhook_url", "").strip()
            if webhook_url:
                import httpx
                # Build localized routing link (e.g. localhost jump link)
                source_link = f"http://localhost:5173/?task_id={card['podcast_id']}&paragraph_id={card['paragraph_id']}"
                payload = {
                    "msg_type": "text",
                    "text": {
                        "content": f"🧠 【知识遗忘唤醒警告】\n闪光点: {card['spark_title']}\n原话: {card['quote']}\nAI 提炼: {card['why_it_matters']}\n播客来源: {podcast_name} - 《{podcast_title}》\n🧭 溯源链接: {source_link}"
                    }
                }
                # We do this asynchronously to avoid blocking the API response
                def send_webhook_async(url, payload):
                    try:
                        with httpx.Client(timeout=10.0, trust_env=False) as client:
                            client.post(url, json=payload)
                            print("🔔 [LOG] Webhook notification sent successfully.")
                    except Exception as wh_err:
                        print(f"⚠️ [LOG WARNING] Webhook notification failed: {wh_err}")
                
                import threading
                threading.Thread(target=send_webhook_async, args=(webhook_url, payload), daemon=True).start()
                
        except Exception as notif_err:
            print(f"⚠️ [LOG ERROR] 发送复习失败通知失败: {notif_err}")
            
    db.update_card(
        card_id,
        status=new_status,
        efactor=new_efactor,
        interval=new_interval,
        next_review_date=next_date
    )
    
    return db.get_card(card_id)

@app.get("/api/links")
def get_links():
    return db.get_all_links()

@app.post("/api/links")
def create_link(req: CreateLinkRequest):
    import uuid
    from datetime import datetime
    
    # Verify both cards exist
    card_a = db.get_card(req.source_card_id)
    card_b = db.get_card(req.target_card_id)
    if not card_a or not card_b:
        raise HTTPException(status_code=404, detail="关联的卡片不存在")
        
    # 调用大模型，将两张卡片和用户的合题灵感提炼为一张全新的【对撞合题卡片】
    llm_prompt = f"""你是一个高级哲学与跨领域知识合成大师。
    现在用户决定将以下两张知识观点卡片，结合他自己的个人融合灵感，融合成一张全新的【对撞合题灵感卡片】（Synthesis Card）。
    
    卡片 A 标题：{card_a.get('spark_title')}
    卡片 A 原文内容："{card_a.get('quote')}"
    
    卡片 B 标题：{card_b.get('spark_title')}
    卡片 B 原文内容："{card_b.get('quote')}"
    
    用户融合顿悟（my_synthesis）：
    "{req.my_synthesis.strip()}"
    
    你的任务是：
    1. 结合卡片 A、卡片 B 和用户的个人顿悟，融合成一个高度凝练、金句般深刻的全新【合题观点原文】（quote，不超过 120 字）。
    2. 为这个碰撞出来的观点，起一个极具学术张力与思维美感的【对撞主题标题】（spark_title，不超过 20 字，格式必须为：“【合题】xxxx”，例如：“【合题】系统权力与精神牢笼的同质性”）。
    3. 撰写一段【为什么重要 (why_it_matters)】的诠释，阐述这层跨界融会背后的认知红利与启发（why_it_matters，不超过 100 字）。
    4. 必须输出 JSON 格式，且只包含三个字段: "spark_title" (字符串), "quote" (字符串), "why_it_matters" (字符串)。
    5. 直接输出 JSON 字符串，不要包含 ```json 或 ```，不要有任何多余字符。"""

    try:
        response_str = call_llm(llm_prompt)
        cleaned_str = response_str.strip()
        if cleaned_str.startswith("```json"):
            cleaned_str = cleaned_str[7:]
        if cleaned_str.startswith("```"):
            cleaned_str = cleaned_str[3:]
        if cleaned_str.endswith("```"):
            cleaned_str = cleaned_str[:-3]
        cleaned_str = cleaned_str.strip()
        
        parsed = json.loads(cleaned_str)
        s_title = parsed.get("spark_title", f"【合题】{card_a.get('spark_title')} & {card_b.get('spark_title')}")
        s_quote = parsed.get("quote", req.my_synthesis.strip())
        s_why = parsed.get("why_it_matters", f"将观点《{card_a.get('spark_title')}》与《{card_b.get('spark_title')}》跨界碰撞融合的脑洞结晶。")
    except Exception as e:
        print(f"⚠️ [LOG ERROR] Synthesize LLM call failed: {e}")
        s_title = f"【合题】{card_a.get('spark_title')} & {card_b.get('spark_title')}"
        s_quote = req.my_synthesis.strip()
        s_why = f"跨越不同播客领域的脑力对撞成果。融合了：{card_a.get('spark_title')} 与 {card_b.get('spark_title')}。"

    # 计算两张卡片的中点，稍微偏上一点放置新卡片
    pos_x_a = card_a.get("pos_x") or 0.0
    pos_y_a = card_a.get("pos_y") or 0.0
    pos_x_b = card_b.get("pos_x") or 0.0
    pos_y_b = card_b.get("pos_y") or 0.0
    mid_x = (pos_x_a + pos_x_b) / 2.0
    mid_y = (pos_y_a + pos_y_b) / 2.0 - 200

    # 创建并保存合成的新卡片
    s_card_id = f"s_card_{uuid.uuid4().hex[:12]}"
    synthesized_card = {
        "id": s_card_id,
        "paragraph_id": f"synthesis-{uuid.uuid4().hex[:12]}",
        "podcast_id": "collider",
        "podcast_name": "💥 跨界灵感对撞",
        "spark_title": s_title,
        "quote": s_quote,
        "why_it_matters": s_why,
        "created_at": datetime.now().isoformat(),
        "is_synthesis": True,
        "parent_ids": [req.source_card_id, req.target_card_id],
        "parent_titles": [card_a.get("spark_title"), card_b.get("spark_title")],
        "efactor": 2.5,
        "status": "stable",
        "pos_x": mid_x,
        "pos_y": mid_y
    }
    db.create_card(synthesized_card)
    
    if req.board_id:
        db.add_card_to_board(req.board_id, s_card_id, mid_x, mid_y)
    
    # 建立两条连线：Card A -> Synthesized Card，和 Card B -> Synthesized Card
    link1 = {
        "id": f"link_{uuid.uuid4().hex[:12]}",
        "source_card_id": req.source_card_id,
        "target_card_id": s_card_id,
        "my_synthesis": req.my_synthesis.strip(),
        "created_at": datetime.now().isoformat()
    }
    db.create_link(link1)
    
    link2 = {
        "id": f"link_{uuid.uuid4().hex[:12]}",
        "source_card_id": req.target_card_id,
        "target_card_id": s_card_id,
        "my_synthesis": req.my_synthesis.strip(),
        "created_at": datetime.now().isoformat()
    }
    db.create_link(link2)
    
    return link1

@app.get("/api/cards/collider")
def get_collider():
    cards = db.get_all_cards()
    if len(cards) < 2:
        raise HTTPException(status_code=400, detail="本地卡片盒中卡片数量少于2张，无法启动 AI 对撞机")
        
    links = db.get_all_links()
    
    # Helper to check if two card IDs are already linked
    def is_linked(id_a, id_b):
        for l in links:
            if (l["source_card_id"] == id_a and l["target_card_id"] == id_b) or \
               (l["source_card_id"] == id_b and l["target_card_id"] == id_a):
                return True
        return False
        
    # Find all pairs of cards that are not yet linked
    unlinked_pairs = []
    for i in range(len(cards)):
        for j in range(i+1, len(cards)):
            if not is_linked(cards[i]["id"], cards[j]["id"]):
                unlinked_pairs.append((cards[i], cards[j]))
                
    if not unlinked_pairs:
        raise HTTPException(status_code=400, detail="所有卡片均已建立关联，AI 对撞机没有可对撞的脑洞啦！")
        
    # Select a pair (prioritize cards from different podcasts for more creative collision)
    diff_podcast_pairs = [p for p in unlinked_pairs if p[0]["podcast_id"] != p[1]["podcast_id"]]
    pair = random.choice(diff_podcast_pairs) if diff_podcast_pairs else random.choice(unlinked_pairs)
    
    card_a, card_b = pair
    
    prompt = f"""你是一个创意无限的跨界知识对撞与链接专家。你擅长在看似完全无关的两个观点中，发现它们底层的通感、共鸣或矛盾火花。

下面是两个知识观点卡片：
卡片 A：
- 标题：{card_a['spark_title']}
- 原文：{card_a['quote']}

卡片 B：
- 标题：{card_b['spark_title']}
- 原文：{card_b['quote']}

你的任务是：
1. 找出这两个观点底层逻辑深处的呼应点、互补点或冲突性火花。
2. 计算它们的【张力指数】（dissonance_index，介于 75 到 99 之间的整数，数值越高代表领域跨度越大，对撞效果越惊喜）。
3. 编写一句【对撞理由】（match_reason，不超过 60 字，例如：“卡片A关于伊朗战争，卡片B关于个人灵气消失。但它们底层都在探讨权力系统对个体生命的压迫。”）。
4. 作为一个跨界对撞机，向用户提一个深刻的、极具启发性的对撞提问（question，不超过 60 字，语气类似：“主人，我发现这两个人在不同领域都在强调/探讨【...】。你觉得它们是一回事吗？”）。
5. 必须以 JSON 格式输出，包含以下字段：
   - "dissonance_index": 整数
   - "match_reason": 字符串
   - "question": 字符串
6. 直接输出 JSON 字符串，不要包含 ```json 或 ``` 格式块，不要有任何多余文字。"""

    try:
        response_str = call_llm(prompt)
        cleaned_str = response_str.strip()
        if cleaned_str.startswith("```json"):
            cleaned_str = cleaned_str[7:]
        if cleaned_str.startswith("```"):
            cleaned_str = cleaned_str[3:]
        if cleaned_str.endswith("```"):
            cleaned_str = cleaned_str[:-3]
        cleaned_str = cleaned_str.strip()
        
        parsed = json.loads(cleaned_str)
        dissonance_index = int(parsed.get("dissonance_index", random.randint(75, 98)))
        match_reason = parsed.get("match_reason", "虽然一者讨论领域不同，但它们在思维模式上具有同构契合性。")
        question = parsed.get("question", "我发现这两个观点底层都在强调一些共同的事情。你觉得它们是一回事吗？")
    except Exception as e:
        print(f"⚠️ [LOG ERROR] Collider AI prompt failed: {e}")
        dissonance_index = random.randint(78, 96)
        match_reason = f"虽然一者关于【{card_a.get('spark_title')}】，另一者关于【{card_b.get('spark_title')}】，但底层思维方式惊人地相似。"
        question = f"主人，我发现【{card_a['spark_title']}】与【{card_b['spark_title']}】之间或许有独特的默契。你觉得它们有什么底层联系吗？"

    # Populate podcast name
    for c in [card_a, card_b]:
        task = db.get_task(c["podcast_id"])
        if task:
            c["podcast_title"] = task.get("title", "未知标题")
            c["podcast_name"] = task.get("podcast_name", "未知播客")
            
    return {
        "card_a": card_a,
        "card_b": card_b,
        "question": question,
        "dissonance_index": dissonance_index,
        "match_reason": match_reason
    }

# ==================== INSIGHTS API ====================

class CreateInsightRequest(BaseModel):
    podcast_id: str
    original_text: str

@app.post("/api/insights")
def create_insight(req: CreateInsightRequest):
    # Call LLM to refine the insight
    prompt = f"""你是一个个人知识管理的洞察提炼助手。
用户从一期播客中摘录了一段话，请你将这段长篇大论压缩、提炼成一句【以第一人称口吻表达的原则或格言】。
要求：
1. 极其简练，直击核心（不超过30个字）。
2. 使用第一人称（例如：“限制社媒使用时间，可以让我的多巴胺基线恢复正常”）。
3. 只输出这一句话，不要有任何其他解释。

用户摘录原文：
"{req.original_text}"
"""
    try:
        response_str = _call_llm_api(prompt, summary_mode="local", label="Insight润色")
        refined_content = response_str.strip()
    except Exception as e:
        print(f"⚠️ [LOG ERROR] Insight LLM refinement failed: {e}")
        refined_content = req.original_text[:30] + "..." if len(req.original_text) > 30 else req.original_text

    from datetime import datetime, timedelta
    tomorrow = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    insight = {
        "podcast_id": req.podcast_id,
        "original_text": req.original_text,
        "refined_content": refined_content,
        "review_count": 0,
        "next_review_date": tomorrow,
        "status": "ACTIVE"
    }
    return db.create_insight(insight)

@app.get("/api/insights/review")
def get_insights_for_review():
    insights = db.get_insights_for_review()
    # Populate podcast name
    for ins in insights:
        task = db.get_task(ins["podcast_id"])
        if task:
            ins["podcast_title"] = task.get("title", "未知标题")
            ins["podcast_name"] = task.get("podcast_name", "未知播客")
    return insights

class ReviewInsightRequest(BaseModel):
    action: str # "keep" or "discard"

@app.post("/api/insights/{insight_id}/review")
def review_insight(insight_id: str, req: ReviewInsightRequest):
    insight = db.get_all_insights() # Not efficient but works for now
    target = None
    for ins in insight:
        if ins["id"] == insight_id:
            target = ins
            break
            
    if not target:
        raise HTTPException(status_code=404, detail="Insight not found")
        
    from datetime import datetime, timedelta
    today = datetime.today()
    
    if req.action == "keep":
        current_count = target.get("review_count", 0)
        # Simple spaced repetition logic for MVP: interval increases
        intervals = [1, 3, 7, 14, 30]
        next_interval = intervals[min(current_count, len(intervals)-1)]
        next_date = (today + timedelta(days=next_interval)).strftime("%Y-%m-%d")
        
        db.update_insight(
            insight_id,
            review_count=current_count + 1,
            next_review_date=next_date
        )
    elif req.action == "discard":
        db.delete_insight(insight_id)
        
    return {"status": "ok"}

# 辅助读取配置
def load_config_dict():
    from app.config import load_config
    return load_config()

