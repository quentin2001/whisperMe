"""Shared LLM calling utility for boards, Q&A, and MCP tools."""
import httpx
import threading
from app.config import config
from app.core import logger
from app.core.network import doh_dns_bypass

print = logger.info

# Global semaphore to strictly serialize local model inference requests to prevent GPU congestion.
# High-end users can change this value in config.json if needed, defaults to 1.
_local_concurrency = config.get("max_local_llm_concurrency", 1)
local_llm_semaphore = threading.Semaphore(_local_concurrency)


class LLMError(Exception):
    """Base exception for all LLM network call failures."""
    pass


def _is_local_url(url: str) -> bool:
    clean = url.lower()
    return "127.0.0.1" in clean or "localhost" in clean or "0.0.0.0" in clean or "::1" in clean or ".local" in clean


def _execute_llm_call(api_url: str, payload: dict, headers: dict, timeout: float, label: str) -> str:
    response = None
    
    # Fast-path for local LLM URLs (LM Studio, Ollama, vLLM, etc.)
    if _is_local_url(api_url):
        try:
            with httpx.Client(timeout=timeout, trust_env=True) as client:
                response = client.post(api_url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
        except Exception as e_local:
            print(f"❌ [LOG] {label} 本地 LLM 请求失败: {e_local}")
            status_code = response.status_code if response is not None else "Unknown"
            detail_msg = response.text if response is not None else str(e_local)
            if "timed out" in str(e_local).lower():
                raise LLMError(f"本地 LLM 推理超时 ({int(timeout)}秒)，建议检查本地大模型服务响应速度或减小问答文本上下文")
            raise LLMError(f"本地 LLM 服务错误 (code {status_code}): {detail_msg}")

    # Tier 1: Try system proxy for remote endpoints
    try:
        with httpx.Client(timeout=timeout, trust_env=True) as client:
            response = client.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
    except Exception as e_proxy:
        print(f"⚠️ [LOG] {label} 代理请求失败: {e_proxy}。尝试直连...")

    # Tier 2: Direct connection with DoH bypass for remote endpoints
    try:
        with doh_dns_bypass(api_url):
            with httpx.Client(timeout=timeout, trust_env=False) as client:
                response = client.post(api_url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
    except Exception as e_doh:
        print(f"❌ [LOG] {label} 直连(DoH DNS 绕过)请求失败: {e_doh}")
        status_code = response.status_code if response is not None else "Unknown"
        detail_msg = response.text if response is not None else str(e_doh)
        raise LLMError(f"LLM API error (code {status_code}): {detail_msg}")


def call_llm(prompt: str, system_prompt: str = None, summary_mode: str = None, label: str = "LLM调用",
             temperature: float = 0.1, timeout: float = 120.0, max_tokens: int = None) -> str:
    """Call the configured LLM (local Ollama or online OpenAI-compatible API).

    Implements a two-tier network fallback strategy:
    1. Try with system proxy (trust_env=True)
    2. Fallback to direct connection using DoH DNS bypass (trust_env=False)

    Args:
        max_tokens: Maximum output tokens. Defaults to 2048 for local, 8192 for online.
    """
    if not summary_mode:
        summary_mode = config.get("summary_mode", "local")

    if summary_mode == "online":
        api_key = config.get("online_summary_api_key", "").strip()
        base_url = config.get("online_summary_base_url", "https://api.openai.com/v1").strip()
        target_model = config.get("online_summary_model", "gpt-4o-mini").strip()
        api_url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        print(f"📡 [LOG] {label}【在线模式】 - 接口: {api_url} | 模型: {target_model}")
    else:
        ollama_url = config.get("ollama_url", "http://localhost:11434").strip()
        target_model = config.get("ollama_model", "qwen2.5:7b-instruct").strip()
        base_url = ollama_url.rstrip('/')
        
        # Auto-append /v1 for OpenAI compatibility (supports LM Studio, Ollama, vLLM, etc.)
        if not base_url.endswith('/v1') and not base_url.endswith('/api'):
            base_url += '/v1'
            
        api_url = f"{base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        print(f"🤖 [LOG] {label}【本地模式】 - 接口: {api_url} | 模型: {target_model}")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
    else:
        messages.append({"role": "user", "content": prompt})

    # 估算输入大小（方便调试性能问题）
    total_input_chars = sum(len(m["content"]) for m in messages)
    print(f"📊 [LOG] {label} 输入统计 - 消息数: {len(messages)} | 总字符数: {total_input_chars} | 估算 tokens: ~{total_input_chars // 2}")

    # 设置 max_tokens 上限，防止无限生成
    if max_tokens is None:
        effective_max_tokens = 2048 if summary_mode != "online" else 8192
    else:
        effective_max_tokens = max_tokens

    payload = {
        "model": target_model,
        "messages": messages,
        "stream": False,
        "temperature": temperature,
        "max_tokens": effective_max_tokens
    }

    if summary_mode != "online":
        print(f"🔒 [LOG] {label}【本地模式】进入排队队列...")
        with local_llm_semaphore:
            print(f"🔓 [LOG] {label}【本地模式】获取执行锁，开始推理...")
            return _execute_llm_call(api_url, payload, headers, timeout, label)
    else:
        return _execute_llm_call(api_url, payload, headers, timeout, label)
