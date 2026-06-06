import json
import httpx
from app.config import config

class PodcastSummarizer:
    def __init__(self):
        # 动态读取配置，实现热更新
        pass

    def summarize(self, metadata: dict, transcript_segments: list[dict], speaker_mappings: dict = None) -> str:
        """
        根据播客元数据、热门评论以及转录剧本，调用大模型生成报告（支持本地与在线 API 切换）
        """
        # 1. 读取实时配置
        summary_mode = config.get("summary_mode", "local")
        
        # 2. 确定接口地址、API Key 和目标模型
        if summary_mode == "online":
            api_key = config.get("online_summary_api_key", "").strip()
            base_url = config.get("online_summary_base_url", "https://api.openai.com/v1").strip()
            target_model = config.get("online_summary_model", "gpt-4o-mini").strip()
            
            # 拼接 completions 地址
            api_url = f"{base_url.rstrip('/')}/chat/completions"
            headers = {
                "Content-Type": "application/json"
            }
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            print(f"📡 [LOG] 启动【在线 API 总结模式】 - 接口地址: {api_url} | 目标模型: {target_model}")
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
            headers = {"Content-Type": "application/json"}
            print(f"🤖 [LOG] 启动【本地大模型总结模式】 - 接口地址: {api_url} | 目标模型: {target_model}")

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

        # 5. 限制长文本大小（如果是本地模型为了安全限制大小，在线大模型通常可以大一些）
        max_char_len = 80000 if summary_mode == "online" else 30000
        if len(full_transcript_text) > max_char_len:
            print(f"⚠️ [LOG] 转录剧本字数较多 ({len(full_transcript_text)}字)，为了防止超出大模型上下文窗口进行安全裁剪...")
            half_len = max_char_len // 2
            full_transcript_text = (
                full_transcript_text[:half_len] 
                + "\n\n...[此处省略部分中间对话]...\n\n" 
                + full_transcript_text[-half_len:]
            )

        # 6. 构建坚若磐石的 Grounded Prompt（防捏造、防脑补、防胡编乱造）
        prompt = f"""你是一个极其严格、专业且尊重客观事实的播客内容分析与知识提炼助手。
请根据下面提供的【播客单集 Shownotes】、【听众热门评论】和【播客对话转录文本】，生成一份详尽、结构清晰的【播客价值总结分析报告】。

> [!CAUTION]
> ⚠️ 核心防伪守则（必须严格遵守，否则视为失败）：
> 1. **严禁臆测发散 (Strict Source Grounding)**：所有分析结论、嘉宾立场、议题提炼及评级，必须【100% 且仅能】基于下方提供的事实源数据。严禁使用你自身固有知识库中的外部信息去“扩展”或“脑补”播客中未提及的事情或技术细节。
> 2. **拒绝幻觉，空值如实报告**：如果播客转录本中完全没有提及某人、某事或某个观点，哪怕该词出现在了 Shownotes 简介里，也绝对不得在总结中编造其对话内容，必须如实标注“转录文本中未讨论/未提及”。
> 3. **精准引用**：提炼核心观点和发言人立场时，必须直接引用（或高度提炼）转录文本中的原话、金句或提及的具体事例，并指明是谁（如“张三”、“Host”）说的。
> 4. **客观呈现听众反馈**：舆情分析部分必须完全基于【热门听众评论】列表中的实际留言（比如赞同、吐槽、提出什么问题），不得凭空编造听众情感走向。

---

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

## 3. 播客对话转录文本（按时间戳与发言人排列）：
---
{full_transcript_text}
---

---

# 请以 Markdown 格式输出以下结构的内容（严禁输出结构外的发散废话，直接输出报告正文）：

## 1. 播客概要与“含金量”评级
- **核心主旨**：用 2-3 句话精准总结这期播客**实际讨论**的核心主题（拒绝大话空话，紧扣转录事实）。
- **目标受众**：根据播客讨论内容的专业深度，说明适合哪些细分人群收听。
- **含金量评级与判定理由**：请给出评级（A+ / A / B / C / D 之一），并从**内容信息密度**、**观点的独特性**和**知识实用度**三个维度，【基于转录中的干货多寡】简述判定理由。
- **推荐等级**：是否值得花时间复听（值得去听 / 仅看总结即可 / 建议避坑）。

## 2. 核心观点与议题提炼
请梳理出播客实际讨论的 3-5 个核心议题。对每个议题：
- **议题名称**
- **核心论点**：结合不同人的发言总结其达成的共识或分歧。
- **关键论据/金句**：**必须**包含转录中发言人提到过的原话、金句或他们讲到的具体案例。

## 3. 发言人画像与立场分析
- **角色定位**：说明都有谁参与了说话，谁是主持人（Host），谁是嘉宾（Guest）。
- **立场与风格**：简述各位发言人的核心立场、讨论风格以及观点倾向，切忌根据发言人的名气脑补其背景，只分析其在此单集中的言论表现。
- **互动氛围**：他们之间的互动如何（比如是和谐互补，还是存在观点的交锋摩擦）。

## 4. 听众口碑与评论区舆情分析
- **听众主要反馈**：评论区大家最赞同的观点是什么？有没有提出不同的质疑？（必须从提供的评论列表中提取，无评论则写“暂无评论数据”）。
- **评论情感极性**：正向期待为主 / 中立探讨 / 存在争议偏见。
- **社会共鸣点**：这期播客勾起了听众什么共鸣或情绪。

## 5. 事实一致性与局限性声明（防伪防脑补区）
- 请在此处特别说明：本报告有哪些内容是简介（Shownotes）中提到但转录对话中**实际并未展开讨论**的？（若有，请逐一列出；若无，写“Shownotes 提及内容与实际转录文本一致”）。
"""

        # 7. 调用 completions 接口
        payload = {
            "model": target_model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "temperature": 0.2
        }
        
        try:
            with httpx.Client(timeout=600.0, trust_env=False) as client:
                response = client.post(api_url, json=payload, headers=headers)
                if response.status_code != 200:
                    raise Exception(f"大模型接口请求失败，状态码: {response.status_code}，详情: {response.text}")
                
                result = response.json()
                summary_md = result.get("choices", [{}])[0].get("message", {}).get("content", "未能获得 LLM 总结的有效内容").strip()
                print("🟢 [LOG] 大模型总结报告生成顺利完成！")
                return summary_md
                
        except httpx.ConnectError:
            err_msg = f"""⚠️ **本地大模型生成总结失败**
- **原因**：无法连接到大模型推理服务（当前配置接口地址为 `{api_url}`）。
- **解决方案**：
  1. 如果使用 **本地大模型 (Ollama/LM Studio)**：请确保您已启动对应的 Local Server（如 LM Studio 的 1234 端口），且配置的地址无误。
  2. 如果使用 **在线 API 总结**：请确保您的网络通畅，且 API 代理地址不需要翻墙或代理配置正确。
  3. 确认服务开启后刷新页面，或者点击右上角“重新生成报告”。"""
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
