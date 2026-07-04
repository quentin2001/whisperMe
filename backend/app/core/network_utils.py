import os
import sys
import httpx
import urllib.request
import urllib.parse
import ssl
import socket
import json
import subprocess
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from app.config import get_short_path_name
from app.core.network import doh_dns_bypass

# 跨平台 curl 命令名
CURL_CMD = "curl.exe" if sys.platform == "win32" else "curl"
# --ssl-no-revoke 仅 Windows Schannel 支持
CURL_SSL_ARGS = ["--ssl-no-revoke"] if sys.platform == "win32" else []

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def safe_httpx_request(method: str, url: str, headers=None, follow_redirects=False, timeout=15.0, **kwargs):
    """
    安全的 HTTPX 请求包装器，优先使用系统代理，失败后自动切换为直连模式
    """
    if headers is None:
        headers = DEFAULT_HEADERS

    # 1. 尝试使用代理 (trust_env=True)
    try:
        with httpx.Client(headers=headers, trust_env=True, follow_redirects=follow_redirects, timeout=timeout, verify=False, **kwargs) as client:
            if method.upper() == "GET":
                resp = client.get(url)
            elif method.upper() == "POST":
                resp = client.post(url)
            elif method.upper() == "HEAD":
                resp = client.head(url)
            if resp.status_code < 400:
                return resp
            resp.raise_for_status()
    except Exception as e:
        print(f"⚠️ [LOG] safe_httpx_request 代理模式({method} {url})失败: {e}。切换直连模式...")
        
    # 2. 尝试直连 (trust_env=False)
    with httpx.Client(headers=headers, trust_env=False, follow_redirects=follow_redirects, timeout=timeout, verify=False, **kwargs) as client:
        if method.upper() == "GET":
            return client.get(url)
        elif method.upper() == "POST":
            return client.post(url)
        elif method.upper() == "HEAD":
            return client.head(url)

def resolve_host_via_doh(host: str) -> str:
    """
    通过 DoH 查询主机的真实 A 记录 IP
    """
    if not host or host.replace('.', '').isdigit():
        return host
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # 优先通过 AliDNS 官方 DoH 接口获取
    try:
        doh_url = f"https://223.5.5.5/resolve?name={host}&type=A"
        req = urllib.request.Request(doh_url, headers={"Host": "dns.alidns.com"})
        with urllib.request.urlopen(req, context=ctx, timeout=4) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            for ans in res_data.get("Answer", []):
                if ans.get("type") == 1:
                    return ans.get("data")
    except Exception:
        pass
        
    # 备用方案：通过 Google DoH 接口获取
    try:
        doh_url = f"https://8.8.8.8/resolve?name={host}&type=A"
        req = urllib.request.Request(doh_url)
        with urllib.request.urlopen(req, context=ctx, timeout=4) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            for ans in res_data.get("Answer", []):
                if ans.get("type") == 1:
                    return ans.get("data")
    except Exception:
        pass
        
    # 兜底：如果 DoH 失败了，尝试使用普通系统 DNS 解析获取 IP
    try:
        ips = socket.getaddrinfo(host, None)
        if ips:
            return ips[0][4][0]
    except Exception:
        pass
        
    return None

def get_doh_transport(host: str, real_ip: str, **kwargs) -> httpx.HTTPTransport:
    import httpcore
    from httpcore._backends.sync import SyncBackend

    class DoHNetworkBackend(SyncBackend):
        def connect_tcp(self, h, port, timeout=None, local_address=None, **kwa):
            if h == host:
                h = real_ip
            return super().connect_tcp(h, port, timeout, local_address, **kwa)

    transport = httpx.HTTPTransport(**kwargs)
    pool_kwargs = getattr(transport, '_pool_kwargs', {})
    transport._pool = httpcore.ConnectionPool(network_backend=DoHNetworkBackend(), **pool_kwargs)
    return transport

def resolve_redirects_via_doh(url: str, max_redirects: int = 5) -> str:
    """
    在 Python 中使用 httpx 和 DoH 自定义传输层追踪所有 HTTP 3xx 重定向，获取最终直链
    """
    current_url = url
    
    for i in range(max_redirects):
        parsed = urllib.parse.urlparse(current_url)
        host_name = parsed.netloc
        if ":" in host_name:
            host_name = host_name.split(":", 1)[0]
            
        if "xmcdn.com" in host_name or "xyzcdn.net" in host_name:
            break
            
        real_ip = resolve_host_via_doh(host_name)
        if not real_ip:
            break
            
        transport = get_doh_transport(host_name, real_ip, verify=False)
        try:
            with httpx.Client(transport=transport, verify=False, follow_redirects=False, timeout=5.0) as client:
                resp = client.head(current_url, headers=DEFAULT_HEADERS)
                if resp.status_code in (301, 302, 303, 307, 308):
                    loc = resp.headers.get("Location")
                    if loc:
                        current_url = urllib.parse.urljoin(current_url, loc)
                        continue
                break
        except Exception:
            break
            
    return current_url

def download_file_with_fallback(url: str, local_path: str, progress_callback=None):
    """使用 4 级 fallback 策略下载文件"""
    downloaded = False

    # 1. httpx 代理
    try:
        print(f"[LOG] 尝试 httpx 代理下载...")
        with httpx.Client(timeout=300.0, trust_env=True, follow_redirects=True, verify=False) as client:
            with client.stream("GET", url, headers={"User-Agent": "whisperMe/1.0"}) as resp:
                if resp.status_code == 200:
                    total = int(resp.headers.get("content-length", 0))
                    downloaded_bytes = 0
                    with open(local_path, "wb") as f:
                        for chunk in resp.iter_bytes(chunk_size=8192):
                            f.write(chunk)
                            downloaded_bytes += len(chunk)
                            if progress_callback and total > 0:
                                progress_callback(min(95.0, (downloaded_bytes / total) * 95.0))
                    downloaded = True
    except Exception as e:
        print(f"[LOG] httpx 代理下载失败: {e}")

    # 2. httpx 直连 (DoH)
    if not downloaded:
        try:
            print(f"[LOG] 尝试 httpx 直连 (DoH) 下载...")
            with doh_dns_bypass(url):
                with httpx.Client(timeout=300.0, trust_env=False, follow_redirects=True, verify=False) as client:
                    with client.stream("GET", url, headers={"User-Agent": "whisperMe/1.0"}) as resp:
                        if resp.status_code == 200:
                            total = int(resp.headers.get("content-length", 0))
                            downloaded_bytes = 0
                            with open(local_path, "wb") as f:
                                for chunk in resp.iter_bytes(chunk_size=8192):
                                    f.write(chunk)
                                    downloaded_bytes += len(chunk)
                                    if progress_callback and total > 0:
                                        progress_callback(min(95.0, (downloaded_bytes / total) * 95.0))
                            downloaded = True
        except Exception as e:
            print(f"[LOG] httpx 直连下载失败: {e}")

    # 3. curl 代理
    if not downloaded:
        try:
            print(f"[LOG] 尝试 curl 代理下载...")
            cmd = [CURL_CMD, "-L", "-o", get_short_path_name(local_path), "-s", "--max-time", "300", url]
            res = subprocess.run(cmd, capture_output=True, timeout=310)
            if res.returncode == 0 and os.path.exists(local_path):
                downloaded = True
        except Exception as e:
            print(f"[LOG] curl 代理下载失败: {e}")

    # 4. curl DoH 直连
    if not downloaded:
        try:
            print(f"[LOG] 尝试 curl DoH 直连下载...")
            real_ip = resolve_host_via_doh(urlparse(url).hostname)
            if real_ip:
                cmd = [CURL_CMD, "-L", "-o", get_short_path_name(local_path), "-s",
                       "--max-time", "300", "--resolve",
                       f"{urlparse(url).hostname}:443:{real_ip}", url]
                res = subprocess.run(cmd, capture_output=True, timeout=310)
                if res.returncode == 0 and os.path.exists(local_path):
                    downloaded = True
        except Exception as e:
            print(f"[LOG] curl DoH 下载失败: {e}")

    if not downloaded:
        raise Exception("所有下载方式均失败")
    if progress_callback:
        progress_callback(100.0)

def clean_html_to_text(html_content: str) -> str:
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    for br in soup.find_all(["br", "br/"]):
        br.replace_with("\n")
    for block in soup.find_all(["p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li"]):
        block.insert_before("\n")
        block.insert_after("\n")
    text = soup.get_text(separator="")
    text = re.sub(r'\n\s*\n', '\n\n', text)
    lines = [line.strip() for line in text.split('\n')]
    return '\n'.join(lines).strip()

def get_audio_duration_str(file_path: str) -> str:
    try:
        from app.config import FFMPEG_PATH
        cmd = [FFMPEG_PATH, "-i", file_path]
        res = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
        output = res.stderr or ""
        match = re.search(r"Duration:\s*(\d{2}:\d{2}:\d{2})", output)
        if match:
            duration_str = match.group(1)
            parts = duration_str.split(":")
            if parts[0] == "00":
                return f"{parts[1]}:{parts[2]}"
            return duration_str
            
        cmd_fallback = ["ffmpeg", "-i", file_path]
        res_fallback = subprocess.run(cmd_fallback, capture_output=True, text=True, errors="ignore")
        output_fallback = res_fallback.stderr or ""
        match_fallback = re.search(r"Duration:\s*(\d{2}:\d{2}:\d{2})", output_fallback)
        if match_fallback:
            duration_str = match_fallback.group(1)
            parts = duration_str.split(":")
            if parts[0] == "00":
                return f"{parts[1]}:{parts[2]}"
            return duration_str
    except Exception as e:
        print(f"⚠️ [LOG] 获取音频时长失败: {e}")
    return "00:00"

def find_nested_key(data, target_key):
    if isinstance(data, dict):
        if target_key in data:
            return data[target_key]
        for k, v in data.items():
            res = find_nested_key(v, target_key)
            if res is not None:
                return res
    elif isinstance(data, list):
        for item in data:
            res = find_nested_key(item, target_key)
            if res is not None:
                return res
    return None
