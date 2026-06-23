import os
import json
import re
import httpx
from app.config import config, PROJECT_DIR
from app.database import db
from app.core import logger

print = logger.info


def get_dynamic_threshold(sample_count: int) -> float:
    """根据声纹出现次数动态调整匹配阈值：出现越多，信任度越高，阈值越宽松"""
    if sample_count >= 10:
        return 0.75   # 老熟人
    elif sample_count >= 5:
        return 0.78
    elif sample_count >= 2:
        return 0.80
    else:
        return 0.83   # 只见过一次，严格匹配


def match_speakers_with_voiceprints(speaker_embeddings: dict) -> tuple:
    """
    Compare speaker embeddings with global voiceprint library (SQLite) using Cosine Similarity.
    返回 (mappings, confidence_dict)
    - mappings: { "SPEAKER_00": "张三" }
    - confidence: { "SPEAKER_00": { "score": 0.87, "source": "voiceprint" } }
    """
    if not speaker_embeddings:
        return {}, {}
    try:
        import numpy as np
        # 从 SQLite 全局声纹库读取
        fingerprints = db.get_all_speakers_with_embeddings()
        if not fingerprints:
            return {}, {}

        mappings = {}
        confidence = {}
        for sp_id, emb in speaker_embeddings.items():
            if not emb: continue
            best_match = None
            max_sim = -1.0
            best_count = 1

            emb_v = np.array(emb)
            norm_emb = np.linalg.norm(emb_v)
            if norm_emb == 0: continue

            for known_name, info in fingerprints.items():
                known_v = np.array(info["embedding"])
                norm_known = np.linalg.norm(known_v)
                if norm_known == 0: continue

                sim = np.dot(emb_v, known_v) / (norm_emb * norm_known)
                if sim > max_sim:
                    max_sim = sim
                    best_match = known_name
                    best_count = info.get("sample_count", 1)

            # 动态阈值：出现次数越多，阈值越宽松
            threshold = get_dynamic_threshold(best_count)
            if max_sim >= threshold and best_match:
                mappings[sp_id] = best_match
                confidence[sp_id] = {"score": round(max_sim, 4), "source": "voiceprint"}
                # 匹配成功，更新出现次数和最近见过时间
                db.upsert_speaker(best_match, fingerprints[best_match]["embedding"], sample_count=best_count + 1)
                print(f"🎯 [LOG] 声纹库匹配成功 - {sp_id} → {best_match} (相似度: {max_sim:.3f}, 阈值: {threshold}, 出现次数: {best_count})")
        return mappings, confidence
    except Exception as e:
        print(f"⚠️ [LOG] 比对声纹特征库失败: {e}")
        return {}, {}

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
        names = set()
        # 匹配 @用户 或 "@" 标志 of 别名
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
    sample_size = min(35, len(transcript))
    sample_transcript = []
    
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
    all_valid_names = set(n.lower() for n in episode_names | template_names)
    
    for sp_id, matched_name in llm_mappings.items():
        if not matched_name or matched_name == sp_id:
            continue
            
        m_name_lower = matched_name.lower()
        if m_name_lower in all_valid_names or m_name_lower in lower_shownotes:
            final_mappings[sp_id] = matched_name
        else:
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
    
    if not shownotes_split:
        shownotes_split = split_shownotes(shownotes)
        
    episode_content = shownotes_split["episode_content"]
    template_names = shownotes_split["template_names"]
    episode_names = shownotes_split["episode_names"]
    
    participants = _llm_identify_participants(title, episode_content, template_names, summary_mode=summary_mode)
    if not participants:
        print("⚠️ [LOG 警告] 第二阶段未推断出任何在场发言人名单候选。")
        return {}
    print(f"👥 [LOG] 第二阶段 - 大模型推断的本期真实在场人员: {participants}")
    
    llm_mappings = _llm_match_speakers(participants, transcript, unmatched_speakers, known_mappings, title, summary_mode=summary_mode)
    if not llm_mappings:
        print("⚠️ [LOG 警告] 第三阶段未建立起临时标识与真实名字的关联。")
        return {}
    print(f"🔌 [LOG] 第三阶段 - 大模型建议的配对映射: {llm_mappings}")
    
    final_mappings = _validate_mappings(llm_mappings, episode_content, episode_names, template_names)
    return final_mappings

def auto_rename_speakers(task_id: str, metadata: dict, transcript: list, speaker_embeddings: dict):
    """
    一键自动化声纹角色推理核心管线
    """
    task = db.get_task(task_id)
    if not task: return

    existing_mappings = task.get("speaker_mappings", {})
    existing_confidence = task.get("speaker_confidence", {})
    all_speakers = set(seg.get("speaker") for seg in transcript if seg.get("speaker"))

    noise_mappings = pre_filter_noise_speakers(transcript)

    unmatched_embeddings = {}
    if speaker_embeddings:
        for sp_id, emb in speaker_embeddings.items():
            if sp_id not in noise_mappings and sp_id not in existing_mappings:
                unmatched_embeddings[sp_id] = emb

    voiceprint_mappings, voiceprint_confidence = match_speakers_with_voiceprints(unmatched_embeddings)
    known_mappings = {**noise_mappings, **voiceprint_mappings}

    # 构建置信度字典
    all_confidence = {**existing_confidence}
    for sp_id in noise_mappings:
        all_confidence[sp_id] = {"score": 1.0, "source": "noise"}
    for sp_id, info in voiceprint_confidence.items():
        all_confidence[sp_id] = info

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
            for sp_id in llm_mappings:
                all_confidence[sp_id] = {"score": 0.0, "source": "llm"}
        except Exception as e:
            print(f"⚠️ [LOG] 大模型推理改名失败: {e}")

    final_mappings = {**noise_mappings, **voiceprint_mappings, **llm_mappings}
    if final_mappings:
        merged = {**final_mappings, **existing_mappings}
        merged_confidence = {**all_confidence, **existing_confidence}
        db.update_task(task_id, speaker_mappings=merged, speaker_confidence=merged_confidence)
        print(f"🎉 [LOG] 四阶段智能识别完成！已自动应用以下角色命名: {merged}")

def apply_interjection_labels(task_id: str, transcript: list):
    if not transcript: return
    task = db.get_task(task_id)
    if not task: return
    speaker_texts = {}
    for seg in transcript:
        sp = seg.get("speaker")
        if not sp: continue
        speaker_texts[sp] = speaker_texts.get(sp, "") + seg.get("text", "").strip()
    mappings = task.get("speaker_mappings", {})
    confidence = task.get("speaker_confidence", {})
    modified = False
    interjection_chars = set("嗯对啊哦吧呢呀啦哈哼嗨呗嘛呃喔呦哎好的噢唏嚯啥么是吗了嘿哟嗷呐哇")
    for sp, full_text in speaker_texts.items():
        if sp in mappings and mappings[sp] and mappings[sp] != sp: continue
        cleaned = "".join([c for c in full_text if c.isalnum()])
        if not cleaned:
            mappings[sp] = "未识别语气词"
            confidence[sp] = {"score": 1.0, "source": "noise"}
            modified = True
            continue
        if len(cleaned) <= 15 and all(c in interjection_chars for c in cleaned):
            mappings[sp] = "未识别语气词"
            confidence[sp] = {"score": 1.0, "source": "noise"}
            modified = True
            print(f"🏷️ [LOG] 自动将仅说语气助词的发言人 {sp} 标记为 '未识别语气词'")
    if modified:
        db.update_task(task_id, speaker_mappings=mappings, speaker_confidence=confidence)
