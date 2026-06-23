"""
ASR Provider 注册表与工厂函数

用法:
    from app.core.asr_providers import get_provider
    provider = get_provider("mimo")
    segments = provider.transcribe(wav_path, diarization_segments, progress_callback)
"""
from app.core.asr_providers.base import ASRProvider

# Provider 注册表 (延迟导入避免循环依赖)
_PROVIDER_REGISTRY: dict[str, type[ASRProvider]] = {}


def _ensure_registry():
    """懒加载注册所有 Provider"""
    if _PROVIDER_REGISTRY:
        return

    from app.core.asr_providers.mimo import MiMoASRProvider
    from app.core.asr_providers.openai_whisper import OpenAIWhisperProvider
    from app.core.asr_providers.funasr import FunASRProvider
    from app.core.asr_providers.custom_http import CustomHTTPProvider

    _PROVIDER_REGISTRY["mimo"] = MiMoASRProvider
    _PROVIDER_REGISTRY["openai"] = OpenAIWhisperProvider
    _PROVIDER_REGISTRY["funasr"] = FunASRProvider
    _PROVIDER_REGISTRY["custom"] = CustomHTTPProvider


def get_provider(name: str) -> ASRProvider:
    """
    根据名称获取 ASR Provider 实例。
    未知名称将 fallback 到 MiMo (baseline)。

    Args:
        name: Provider 名称 ("mimo", "openai", "funasr", "custom")

    Returns:
        ASRProvider 实例
    """
    _ensure_registry()

    key = name.strip().lower() if name else "mimo"
    provider_cls = _PROVIDER_REGISTRY.get(key)

    if provider_cls is None:
        print(f"⚠️ [LOG] 未知的 ASR Provider: '{name}'，回退到 MiMo baseline")
        provider_cls = _PROVIDER_REGISTRY["mimo"]

    print(f"📡 [LOG] 正在初始化 ASR Provider: {provider_cls.__name__} ({key})")
    return provider_cls()


def list_providers() -> list[dict]:
    """列出所有可用的 Provider（供前端使用）"""
    _ensure_registry()
    result = []
    for key, cls in _PROVIDER_REGISTRY.items():
        try:
            instance = cls()
            result.append({
                "id": key,
                "name": instance.get_display_name()
            })
        except Exception:
            result.append({"id": key, "name": cls.__name__})
    return result
