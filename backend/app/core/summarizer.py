import re
import json
import httpx
from app.config import config
from app.core.prompt_manager import load_prompt, get_template_prompt, BUILTIN_TEMPLATES
from app.core.network import doh_dns_bypass
from app.core.llm_utils import call_llm
from app.core import logger

print = logger.info

# 中文语气词/口头禅去噪正则（播客口语转录中的高频噪声）
_FILLER_PATTERN = re.compile(
    r'^[\s]*(嗯+|啊+|呃+|额+|哦+|唉+|哎+|诶+|对对对|是是是|好好好|'
    r'对的对的|没错没错|就是就是|然后然后)[\s。，、！？.,!?]*$'
)
_FILLER_INLINE_PATTERN = re.compile(
    r'(?:^|(?<=[。，、！？.,!?\s]))'
    r'(?:嗯+|啊+|呃+|额+|哦+|就是说|那个|然后嘛|对吧|你知道吗|怎么说呢)'
    r'(?=[。，、！？.,!?\s]|$)'
)

class PodcastSummarizer:
    def __init__(self):
        # 动态读取配置，实现热更新
        pass

    def _split_transcript_into_chunks(self, lines: list[str], max_chars: int, overlap_lines: int = 15) -> list[list[str]]:
        """
        将转录文本行列表分段，每段不超过 max_chars 字符，段间有 overlap_lines 行重叠
        """
        if not lines:
            return [[]]

        chunks = []
        current_chunk = []
        current_len = 0

        for line in lines:
            line_len = len(line) + 1  # +1 for newline
            if current_len + line_len > max_chars and current_chunk:
                chunks.append(current_chunk)
                # 保留最后 overlap_lines 行作为下一段的开头（重叠）
                overlap = current_chunk[-overlap_lines:] if len(current_chunk) > overlap_lines else current_chunk[:]
                current_chunk = overlap
                current_len = sum(len(l) + 1 for l in current_chunk)
            current_chunk.append(line)
            current_len += line_len

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _denoise_transcript_lines(self, lines: list[str]) -> list[str]:
        """
        对转录文本行进行去噪处理，减少送入 LLM 的 token 数量：
        1. 删除纯语气词/口头禅行（如 "嗯"、"对对对"）
        2. 清理行内语气词填充（如 "嗯，就是说，那个"）
        3. 合并连续的极短行（<5 字符）
        """
        if not lines:
            return lines

        denoised = []
        for line in lines:
            # 保留说话人标签：提取 "SpeakerName: text" 格式
            speaker_prefix = ""
            text_part = line
            if ": " in line:
                parts = line.split(": ", 1)
                if len(parts[0]) < 30:  # 合理的说话人名长度
                    speaker_prefix = parts[0] + ": "
                    text_part = parts[1]

            # 跳过纯语气词行
            if _FILLER_PATTERN.match(text_part.strip()):
                continue

            # 清理行内语气词
            cleaned = _FILLER_INLINE_PATTERN.sub('', text_part).strip()
            # 清理连续标点
            cleaned = re.sub(r'[，、]{2,}', '，', cleaned)
            cleaned = re.sub(r'\s{2,}', ' ', cleaned)
            # 清理首尾残留标点
            cleaned = cleaned.strip('，、。！？,. ')

            if not cleaned or len(cleaned) < 2:
                continue

            denoised.append(speaker_prefix + cleaned if speaker_prefix else cleaned)

        original_len = sum(len(l) for l in lines)
        denoised_len = sum(len(l) for l in denoised)
        reduction = original_len - denoised_len
        if reduction > 0:
            pct = (reduction / original_len * 100) if original_len > 0 else 0
            print(f"🧹 [LOG] 转录文本去噪完成：{len(lines)} 行 → {len(denoised)} 行，字符数 {original_len} → {denoised_len}（减少 {reduction} 字符，{pct:.1f}%）")

        return denoised

    def summarize(self, metadata: dict, transcript_segments: list[dict], speaker_mappings: dict = None, summary_mode: str = None, custom_prompt: str = None) -> str:
        """
        根据播客元数据、热门评论以及转录剧本，调用大模型生成报告（支持本地与在线 API 切换）
        """
        # 1. 如果没有传入指定的 summary_mode，则读取实时配置兜底
        if not summary_mode:
            summary_mode = config.get("summary_mode", "local")



        # 3. 组装转录文本并自动识别是否有多个发言人
        raw_speakers = set(seg.get("speaker") or "" for seg in transcript_segments)
        raw_speakers = {s for s in raw_speakers if s and s != "UNKNOWN_SPEAKER" and s != "未知发言人"}
        has_multiple_speakers = len(raw_speakers) > 1

        transcript_text_lines = []
        for seg in transcript_segments:
            text = seg.get("text", "").strip()
            if not text:
                continue
            
            if has_multiple_speakers:
                speaker_name = seg.get("speaker") or "未知发言人"
                if speaker_mappings and speaker_name in speaker_mappings:
                    speaker_name = speaker_mappings[speaker_name]
                line = f"{speaker_name}: {text}"
            else:
                line = text
                
            transcript_text_lines.append(line)

        # 3.5. 转录文本去噪（减少送入 LLM 的 token 数量）
        transcript_text_lines = self._denoise_transcript_lines(transcript_text_lines)

        # 4. 组装评论内容
        comments_text_lines = []
        for idx, c in enumerate(metadata.get("comments", [])):
            comments_text_lines.append(f"{idx+1}. {c['author']} (点赞 {c['likes']}): {c['content']}")
        full_comments_text = "\n".join(comments_text_lines) if comments_text_lines else "暂无评论数据"

        # 5. 长文本分段策略
        # qwen2.5-7b-instruct-1m 等长上下文模型支持远超 45K chars，统一提高到 80K 减少不必要的分段
        max_char_len = 80000
        chunk_threshold = max_char_len  # 超过此长度则分段总结

        total_transcript_chars = sum(len(l) for l in transcript_text_lines)
        print(f"📊 [LOG] 总结输入统计 - 模式: {summary_mode} | 转录行数: {len(transcript_text_lines)} | 转录字符数: {total_transcript_chars} | 分段阈值: {chunk_threshold}")

        # 6. 动态加载 Prompt，支持前端实时编辑
        if custom_prompt:
            user_prompt = custom_prompt
            print(f"📝 [LOG] 使用前端传入的自定义 Prompt（{len(custom_prompt)} 字符）")
        else:
            # 6.1. 优先使用 default_template_id 对应的模板（尊重用户在设置中选择的默认模板）
            prompt_dict = load_prompt()
            default_template_id = prompt_dict.get("default_template_id", "standard")

            # 6.2. 本地模式自适应：如果用户未设置过默认模板（仍为 standard），自动切换到精简速览
            #      本地 7B 模型更擅长遵循简短指令，且输出更快
            if summary_mode != "online" and default_template_id == "standard":
                effective_template_id = "concise"
                print(f"⚡ [LOG] 本地模式自动优化：使用精简速览模板（concise）以加速生成。如需完整分析请在前端手动选择模板。")
            else:
                effective_template_id = default_template_id
                print(f"📋 [LOG] 使用默认模板: {effective_template_id}")

            # 6.3. 按模板 ID 加载 prompt 内容
            template_prompt = get_template_prompt(effective_template_id)
            if template_prompt:
                user_prompt = template_prompt
            else:
                user_prompt = prompt_dict.get("prompt", "")
                if not user_prompt:
                    base_prompt = prompt_dict.get("base_prompt", "")
                    action_prompt = prompt_dict.get("action_prompt", "")
                    user_prompt = f"{base_prompt}\n\n{{{{PODCAST_DATA}}}}\n\n{action_prompt}"

        # 6.5. 如果未开启或未识别出多个发言人，动态注入 Prompt 刚性约束
        unique_speakers = set(seg.get("speaker") for seg in transcript_segments if seg.get("speaker"))
        if len(unique_speakers) <= 1:
            guard_instruction = """
[🚨 极重要防错声明]
检测到本期播客的转录文本中没有区分发言人（所有发言标记均为相同角色或未知）。
请务必遵守以下刚性约束：
1. 严禁尝试在总结或分析中臆测、脑补出任何具体的发言人姓名、嘉宾画像或主持人角色（如 Host、Guest 名字）。
2. 在原计划输出“## 3. 发言人画像与立场分析”章节时，请将其重命名为“## 3. 议题正反核心视点交锋与视角分析”。
3. 纯粹从播客讨论的议题语义逻辑出发，提炼不同观点的正反论据、共识与分歧，以客观内容取代针对具体人名的画像分析。
"""
            user_prompt = guard_instruction + "\n" + user_prompt

        # 公共数据块（不含转录文本）
        meta_block = f"""
# 事实源数据：

## 1. 播客单集元数据：
- 播客单集标题：{metadata.get('title', '未知标题')}
- 所属节目名称：{metadata.get('podcast_name', '未知播客')}
- 互动数据：点赞数 {metadata.get('like_count', 0)}，评论数 {metadata.get('comment_count', 0)}
- 节目 Shownotes 简介：
---
{metadata.get('shownotes', '暂无简介')}
---

## 2. 热门听众评论列表：
---
{full_comments_text}
---
"""

        try:
            if len(transcript_text_lines) > 0 and sum(len(l) for l in transcript_text_lines) > chunk_threshold:
                # ========== 长播客分段总结模式 ==========
                chunk_chars = max_char_len - 5000  # 留余量给 prompt 本身
                chunks = self._split_transcript_into_chunks(transcript_text_lines, chunk_chars, overlap_lines=15)
                total_chunks = len(chunks)
                print(f"📄 [LOG] 转录文本较长，自动分为 {total_chunks} 段进行分段总结...")

                partial_summaries = []
                for i, chunk_lines in enumerate(chunks):
                    chunk_text = "\n".join(chunk_lines)

                    chunk_data = f"""{meta_block}

## 3. 播客对话转录文本 - 第 {i+1}/{total_chunks} 段（按发言人排列）：
---
{chunk_text}
---
"""
                    chunk_suffix = f"""

请针对以上第 {i+1}/{total_chunks} 段转录内容，生成一份**该段落的局部总结报告**。要求：
1. 严格遵守上方的核心防伪守则。
2. 按照标准报告结构输出，但仅覆盖本段中讨论的内容。
3. 如果本段内容较少，可以简化结构，重点提炼核心观点和金句。"""
                    # 制作静态的 System Prompt，用于触发 Prefix Caching 缓存
                    system_prompt = user_prompt.replace("{{PODCAST_DATA}}", "\n[请仔细阅读下一条消息中提供的转录文本，并根据本指令生成总结报告]\n")
                    chunk_prompt_user = chunk_data + chunk_suffix
                    print(f"📝 [LOG] 正在总结第 {i+1}/{total_chunks} 段...")
                    partial = call_llm(chunk_prompt_user, system_prompt=system_prompt, summary_mode=summary_mode, label="LLM局部总结", timeout=600.0, temperature=0.2)
                    partial_summaries.append(partial)
                    print(f"✅ [LOG] 第 {i+1}/{total_chunks} 段总结完成")

                # 合并阶段：将所有分段总结合并为最终报告
                all_partial = "\n\n---\n\n".join(
                    [f"### 第 {i+1} 段总结\n\n{s}" for i, s in enumerate(partial_summaries)]
                )
                merge_prompt = f"""请根据以下一份播客的多段分段总结报告，合并生成一份**完整、连贯、无重复**的最终播客价值总结分析报告。

**播客标题**：《{metadata.get('title', '未知标题')}》
**所属节目**：{metadata.get('podcast_name', '未知播客')}

以下是各段总结报告：
---
{all_partial}
---

请将以上各段总结合并为一份**完整、连贯、无重复**的最终播客价值总结分析报告，按照标准报告结构组织，去除重复内容，保留所有核心观点、金句和可执行建议。"""
                print(f"🔗 [LOG] 正在合并 {total_chunks} 段总结为最终报告...")
                summary_md = call_llm(merge_prompt, summary_mode=summary_mode, label="LLM合并总结", timeout=600.0, temperature=0.2)
                print("🟢 [LOG] 长播客分段总结报告生成完成！")

            else:
                # ========== 普通单次总结模式 ==========
                transcript_text = "\n".join(transcript_text_lines)

                data_block = f"""{meta_block}

## 3. 播客对话转录文本：
---
{transcript_text}
---
"""
                system_prompt = user_prompt.replace("{{PODCAST_DATA}}", "\n[请仔细阅读下一条消息中提供的转录文本，并根据本指令生成总结报告]\n")
                print(f"📝 [LOG] 转录文本长度正常，使用单次总结模式")
                summary_md = call_llm(data_block, system_prompt=system_prompt, summary_mode=summary_mode, label="LLM全局总结", timeout=600.0, temperature=0.2)
                print("🟢 [LOG] 大模型总结报告生成顺利完成！")

            return summary_md

        except httpx.ConnectError:
            err_msg = f"""⚠️ **本地大模型生成总结失败**
- **原因**：无法连接到大模型推理服务。
- **解决方案**：
  1. 如果使用 **本地大模型 (Ollama/LM Studio)**：请确保您已启动对应的 Local Server（如 LM Studio 的 1234 端口），且配置的地址无误。
  2. 如果使用 **在线 API 总结**：请确保您的网络通畅，且 API 代理地址不需要翻墙或代理配置正确。
  3. 确认服务开启后刷新页面，或者点击右上角"重新生成报告"。"""
            print(f"❌ [LOG 异常] 连接大模型服务失败: ConnectError。")
            return err_msg

        except Exception as e:
            err_msg = f"""⚠️ **大模型生成总结失败**
- **报错详情**：`{str(e)}`
- **解决方案**：
  1. 请检查您的配置参数（API Key、Base URL、Model 等）是否正确。
  2. 如果使用本地模型，请确认显卡的显存是否充足。"""
            print(f"❌ [LOG 异常] 调用大模型时出错: {e}")
            return err_msg
