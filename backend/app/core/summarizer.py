import json
import httpx
import socket
from urllib.parse import urlparse
from contextlib import contextmanager
from app.config import config
from app.core.prompt_manager import load_prompt

def resolve_host_via_doh(host: str) -> str:
    if not host:
        return None
    
    # 硬编码的常用域名静态 IP 兜底，防止 Clash DNS 劫持和 DoH 本身也被拦截导致的双重失效
    STATIC_IP_MAPS = {
        "token-plan-sgp.xiaomimimo.com": "8.222.147.102"
    }
    
    # 尝试 DoH 解析
    doh_urls = [
        "https://dns.alidns.com/resolve",
        "https://doh.pub/dns-query"
    ]
    for doh_base in doh_urls:
        try:
            params = {"name": host, "type": "1"}
            with httpx.Client(trust_env=False, timeout=5.0) as client:
                resp = client.get(doh_base, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    answers = data.get("Answer", [])
                    for ans in answers:
                        if ans.get("type") == 1:
                            ip = ans.get("data")
                            if ip and not ip.startswith("198.18."):
                                return ip
        except Exception:
            pass
            
    # 尝试系统 DNS 解析
    try:
        ips = socket.getaddrinfo(host, None)
        if ips:
            ip = ips[0][4][0]
            if ip and not ip.startswith("198.18."):
                return ip
    except Exception:
        pass
        
    # 如果解析失败或者是 Clash 劫持的 fake-IP (198.18.*.*)，则使用静态 IP 兜底
    if host in STATIC_IP_MAPS:
        print(f"⚠️ [LOG] {host} 解析失败或被 Clash DNS 劫持，使用静态 IP 兜底: {STATIC_IP_MAPS[host]}")
        return STATIC_IP_MAPS[host]
        
    return None

@contextmanager
def doh_dns_bypass(url: str):
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or (80 if parsed.scheme == "http" else 443)
    except Exception:
        host = None
        port = None

    if not host:
        yield
        return

    real_ip = resolve_host_via_doh(host)
    if real_ip and real_ip != "198.18.0.46":
        print(f"🎯 [LOG] DoH 拦截 DNS 成功 -> 将域名 {host} 直接映射至公网 IP {real_ip} 进行直连")
        original_getaddrinfo = socket.getaddrinfo
        def custom_getaddrinfo(*args, **kwargs):
            h = args[0] if args else kwargs.get("host")
            if h == host:
                p = args[1] if len(args) > 1 else kwargs.get("port")
                target_port = p
                if target_port is None: target_port = port
                try: target_port = int(target_port)
                except ValueError: target_port = port
                return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (real_ip, target_port))]
            return original_getaddrinfo(*args, **kwargs)
        
        socket.getaddrinfo = custom_getaddrinfo
        try:
            yield
        finally:
            socket.getaddrinfo = original_getaddrinfo
    else:
        yield

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
                
            # 2. 直连模式兜底 (结合 DoH 绕过)
            if response is None or response.status_code != 200:
                try:
                    with doh_dns_bypass(api_url):
                        with httpx.Client(timeout=600.0, trust_env=False) as client:
                            response = client.post(api_url, json=payload, headers=headers)
                            if response.status_code == 200:
                                print("🟢 [LOG] 通过直连(DoH DNS 绕过)模式成功生成总结报告！")
                except Exception as e_doh:
                    print(f"❌ [LOG] 大模型总结直连(DoH DNS 绕过)请求失败: {e_doh}")

            if response is None or response.status_code != 200:
                detail_msg = response.text if response is not None else "无响应"
                status_code = response.status_code if response is not None else "未知"
                raise Exception(f"大模型接口请求失败，状态码: {status_code}，详情: {detail_msg}")

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
