import json
import httpx
from app.config import config
from app.core.prompt_manager import load_prompt

class PodcastSummarizer:
    def __init__(self):
        # 动态读取配置，实现热更新
        pass

    def summarize(self, metadata: dict, transcript_segments: list[dict], speaker_mappings: dict = None, summary_mode: str = None) -> str:
        """
        根据播客元数据、热门评论以及转录剧本，调用大模型生成报告（支持本地与在线 API 切换）
        """
        # 1. 如果没有传入指定的 summary_mode，则读取实时配置兜底
        if not summary_mode:
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
        max_char_len = 80000 if summary_mode == "online" else 45000
        if len(full_transcript_text) > max_char_len:
            print(f"⚠️ [LOG] 转录剧本字数较多 ({len(full_transcript_text)}字)，为了防止超出大模型上下文窗口进行安全裁剪...")
            half_len = max_char_len // 2
            full_transcript_text = (
                full_transcript_text[:half_len]
                + "\n\n...[此处省略部分中间对话]...\n\n"
                + full_transcript_text[-half_len:]
            )

        # 6. 动态加载 Prompt，支持前端实时编辑
        prompt_dict = load_prompt()
        base_prompt = prompt_dict.get("base_prompt", "")
        action_prompt = prompt_dict.get("action_prompt", "")

        # 将实际数据填充进 prompt（如果 prompt 包含占位符）
        # 如果 base_prompt 含有 {metadata} 等占位符则替换，否则直接拼接数据块
        data_block = f"""
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
"""
        prompt = f"{base_prompt}\n{data_block}\n{action_prompt}"

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
            response = None
            # 1. 优先使用系统代理
            try:
                with httpx.Client(timeout=600.0, trust_env=True) as client:
                    response = client.post(api_url, json=payload, headers=headers)
                    response.raise_for_status()
                    print("🟢 [LOG] 通过代理模式成功生成总结报告！")
            except Exception as e_proxy:
                print(f"⚠️ [LOG] 大模型总结接口代理请求失败: {e_proxy}。正在尝试直连模式...")
                
            # 2. 直连模式兜底
            if response is None or response.status_code != 200:
                with httpx.Client(timeout=600.0, trust_env=False) as client:
                    response = client.post(api_url, json=payload, headers=headers)
                    if response.status_code != 200:
                        raise Exception(f"大模型接口请求失败，状态码: {response.status_code}，详情: {response.text}")
                    print("🟢 [LOG] 通过直连模式成功生成总结报告！")

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
