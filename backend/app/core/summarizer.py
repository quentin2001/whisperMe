import json
import httpx
from app.config import config
from app.core.prompt_manager import load_prompt
from app.core.network import doh_dns_bypass
from app.core.llm_utils import call_llm

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



    def summarize(self, metadata: dict, transcript_segments: list[dict], speaker_mappings: dict = None, summary_mode: str = None) -> str:
        """
        根据播客元数据、热门评论以及转录剧本，调用大模型生成报告（支持本地与在线 API 切换）
        """
        # 1. 如果没有传入指定的 summary_mode，则读取实时配置兜底
        if not summary_mode:
            summary_mode = config.get("summary_mode", "local")



        # 3. 组装转录文本
        transcript_text_lines = []
        for seg in transcript_segments:
            speaker_name = seg["speaker"]
            if speaker_mappings and speaker_name in speaker_mappings:
                speaker_name = speaker_mappings[speaker_name]
            line = f"{seg['timestamp_str']} {speaker_name}: {seg['text']}"
            transcript_text_lines.append(line)

        full_transcript_text = "\n".join(transcript_text_lines)

        # 4. 组装评论内容
        comments_text_lines = []
        for idx, c in enumerate(metadata.get("comments", [])):
            comments_text_lines.append(f"{idx+1}. {c['author']} (点赞 {c['likes']}): {c['content']}")
        full_comments_text = "\n".join(comments_text_lines) if comments_text_lines else "暂无评论数据"

        # 5. 长文本分段策略
        max_char_len = 80000 if summary_mode == "online" else 45000
        chunk_threshold = max_char_len  # 超过此长度则分段总结

        # 6. 动态加载 Prompt，支持前端实时编辑
        prompt_dict = load_prompt()
        user_prompt = prompt_dict.get("prompt", "")
        # 兼容旧格式：如果有 base_prompt + action_prompt，拼接使用
        if not user_prompt:
            base_prompt = prompt_dict.get("base_prompt", "")
            action_prompt = prompt_dict.get("action_prompt", "")
            user_prompt = f"{base_prompt}\n\n{{{{PODCAST_DATA}}}}\n\n{action_prompt}"

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
            if len(full_transcript_text) > chunk_threshold:
                # ========== 长播客分段总结模式 ==========
                chunk_chars = max_char_len - 5000  # 留余量给 prompt 本身
                chunks = self._split_transcript_into_chunks(transcript_text_lines, chunk_chars, overlap_lines=15)
                total_chunks = len(chunks)
                print(f"📄 [LOG] 转录文本较长 ({len(full_transcript_text)}字)，自动分为 {total_chunks} 段进行分段总结...")

                partial_summaries = []
                for i, chunk_lines in enumerate(chunks):
                    chunk_text = "\n".join(chunk_lines)
                    chunk_data = f"""{meta_block}

## 3. 播客对话转录文本 - 第 {i+1}/{total_chunks} 段（按时间戳与发言人排列）：
---
{chunk_text}
---
"""
                    chunk_suffix = f"""

请针对以上第 {i+1}/{total_chunks} 段转录内容，生成一份**该段落的局部总结报告**。要求：
1. 严格遵守上方的核心防伪守则。
2. 按照标准报告结构输出，但仅覆盖本段中讨论的内容。
3. 如果本段内容较少，可以简化结构，重点提炼核心观点和金句。
4. 在报告最末尾增加一行：`本段覆盖时间范围：{chunk_lines[0][:12] if chunk_lines else '?'} — {chunk_lines[-1][:12] if chunk_lines else '?'}`"""
                    chunk_prompt = user_prompt.replace("{{PODCAST_DATA}}", chunk_data + chunk_suffix)
                    print(f"📝 [LOG] 正在总结第 {i+1}/{total_chunks} 段...")
                    partial = call_llm(chunk_prompt, summary_mode=summary_mode, label="LLM局部总结", timeout=600.0, temperature=0.2)
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
                data_block = f"""{meta_block}

## 3. 播客对话转录文本（按时间戳与发言人排列）：
---
{full_transcript_text}
---
"""
                prompt = user_prompt.replace("{{PODCAST_DATA}}", data_block)
                print(f"📝 [LOG] 转录文本长度正常 ({len(full_transcript_text)}字)，使用单次总结模式")
                summary_md = call_llm(prompt, summary_mode=summary_mode, label="LLM全局总结", timeout=600.0, temperature=0.2)
                print("🟢 [LOG] 大模型总结报告生成顺利完成！")

            return summary_md

        except httpx.ConnectError:
            err_msg = f"""⚠️ **本地大模型生成总结失败**
- **原因**：无法连接到大模型推理服务（当前配置接口地址为 `{api_url}`）。
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
