"""Shared LLM calling utility for boards, Q&A, and MCP tools."""
import httpx
from app.config import config
from app.core import logger
print = logger.info


def call_llm(prompt: str, summary_mode: str = None, label: str = "LLM调用",
             temperature: float = 0.1, timeout: float = 120.0) -> str:
    """Call the configured LLM (local Ollama or online OpenAI-compatible API).

    Args:
        prompt: The full prompt to send.
        summary_mode: "local" or "online". Defaults to config value.
        label: Label for log messages.
        temperature: LLM temperature parameter.
        timeout: HTTP request timeout in seconds.

    Returns:
        The LLM's response text.

    Raises:
        Exception: If the LLM API returns a non-200 status.
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
        api_url = f"{base_url}/v1/chat/completions" if '/v1' not in base_url else f"{base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        print(f"🤖 [LOG] {label}【本地模式】 - 接口: {api_url} | 模型: {target_model}")

    payload = {
        "model": target_model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "temperature": temperature
    }

    with httpx.Client(timeout=timeout, trust_env=False) as client:
        response = client.post(api_url, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"LLM API error (code {response.status_code}): {response.text}")
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
