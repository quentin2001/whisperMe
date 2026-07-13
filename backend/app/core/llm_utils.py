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


def _execute_llm_call(api_url: str, payload: dict, headers: dict, timeout: float, label: str) -> str:
    response = None
    
    # Tier 1: Try system proxy
    try:
        with httpx.Client(timeout=timeout, trust_env=True) as client:
            response = client.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
    except Exception as e_proxy:
        print(f"⚠️ [LOG] {label} 代理请求失败: {e_proxy}。尝试直连...")

    # Tier 2: Direct connection with DoH bypass
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


def call_llm(prompt: str, summary_mode: str = None, label: str = "LLM调用",
             temperature: float = 0.1, timeout: float = 120.0) -> str:
    """Call the configured LLM (local Ollama or online OpenAI-compatible API).

    Implements a two-tier network fallback strategy:
    1. Try with system proxy (trust_env=True)
    2. Fallback to direct connection using DoH DNS bypass (trust_env=False)
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
        if '/v1' not in base_url and '11434' not in base_url: api_url = f"{base_url}/v1/chat/completions"
        elif '11434' in base_url and '/v1' not in base_url: api_url = f"{base_url}/v1/chat/completions"
        else: api_url = f"{base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        print(f"🤖 [LOG] {label}【本地模式】 - 接口: {api_url} | 模型: {target_model}")

    payload = {
        "model": target_model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "temperature": temperature
    }

    if summary_mode != "online":
        print(f"🔒 [LOG] {label}【本地模式】进入排队队列...")
        with local_llm_semaphore:
            print(f"🔓 [LOG] {label}【本地模式】获取执行锁，开始推理...")
            return _execute_llm_call(api_url, payload, headers, timeout, label)
    else:
        return _execute_llm_call(api_url, payload, headers, timeout, label)
