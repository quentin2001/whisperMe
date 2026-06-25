"""Unified DoH DNS bypass for environments with VPN/Clash fake-IP interference.

Provides resolve_host_via_doh() and doh_dns_bypass() context manager.
Used by transcriber, summarizer, downloader, and ASR providers to bypass
Clash fake-IP (198.18.x.x) DNS hijacking via direct DoH resolution.
"""
import socket
import httpx
from urllib.parse import urlparse
from contextlib import contextmanager

# 静态 IP 映射（已知域名 → 真实 IP 兜底，防止 DoH 本身也被拦截）
STATIC_IP_MAPS = {
    "token-plan-sgp.xiaomimimo.com": "8.222.147.102",
}


def resolve_host_via_doh(host: str) -> str | None:
    """通过 DoH 解析域名真实 IP（绕过 Clash fake-IP 198.18.x.x 范围）。

    依次尝试: 静态映射 → 阿里 DoH → 腾讯 DoH → 系统 DNS
    """
    if not host:
        return None

    # 硬编码静态 IP 兜底
    if host in STATIC_IP_MAPS:
        return STATIC_IP_MAPS[host]

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
    """上下文管理器：临时绕过代理 DNS 劫持，直连目标真实 IP。

    用法:
        with doh_dns_bypass("https://api.openai.com/v1/chat/completions"):
            client.post(...)  # 走直连真实 IP
    """
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
