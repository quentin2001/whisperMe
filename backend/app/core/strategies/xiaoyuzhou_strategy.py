import os
import re
import json
import httpx
import subprocess
from bs4 import BeautifulSoup
from app.core.strategies.base import DownloaderStrategy
from app.core.network_utils import (
    safe_httpx_request,
    resolve_host_via_doh,
    resolve_redirects_via_doh,
    find_nested_key,
    clean_html_to_text,
    DEFAULT_HEADERS,
    CURL_CMD
)

def extract_xiaoyuzhou_comments(data):
    comments_list = []
    seen = set()
    
    def dfs_search(obj):
        if isinstance(obj, dict):
            if "text" in obj and ("author" in obj or "user" in obj):
                author = obj.get("author", {}).get("nickname", "听友") if isinstance(obj.get("author"), dict) else "听友"
                text = obj.get("text", "")
                likes = obj.get("likeCount", 0)
                if text:
                    key = (author, text)
                    if key not in seen:
                        seen.add(key)
                        comments_list.append({
                            "author": author,
                            "content": text,
                            "likes": likes
                        })
            for k, v in obj.items():
                if k == "replyToComment":
                    continue
                dfs_search(v)
        elif isinstance(obj, list):
            for item in obj:
                dfs_search(item)

    dfs_search(data)
    comments_list.sort(key=lambda x: x.get("likes", 0), reverse=True)
    return comments_list


class XiaoyuzhouStrategy(DownloaderStrategy):
    def can_handle(self, url: str) -> bool:
        return "xiaoyuzhoufm.com" in url

    def parse_metadata(self, url: str) -> dict:
        print(f"📡 [LOG] 开始解析小宇宙页面: {url}")
        
        if "/podcast/" in url:
            print("🎙️ [LOG] 识别为小宇宙播客节目主页，正在自动获取最新单集...")
            html_home = None
            try:
                with httpx.Client(headers=DEFAULT_HEADERS, follow_redirects=True, trust_env=True, timeout=15.0, verify=False) as client:
                    r = client.get(url)
                    if r.status_code == 200:
                        html_home = r.text
            except Exception:
                pass
            if not html_home:
                try:
                    with httpx.Client(headers=DEFAULT_HEADERS, follow_redirects=True, trust_env=False, timeout=15.0, verify=False) as client:
                        r = client.get(url)
                        if r.status_code == 200:
                            html_home = r.text
                except Exception:
                    pass
            if not html_home:
                try:
                    cmd = [CURL_CMD, "-k", "-L", "-s", url]
                    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=15)
                    if res.returncode == 0 and res.stdout.strip():
                        html_home = res.stdout
                except Exception:
                    pass
            if not html_home:
                try:
                    resolve_ip = resolve_host_via_doh("www.xiaoyuzhoufm.com")
                    clean_env = os.environ.copy()
                    for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
                        clean_env.pop(key, None)
                    cmd = [CURL_CMD, "-k", "-L", "-s", "--noproxy", "*"]
                    if resolve_ip:
                        cmd.extend(["--resolve", f"www.xiaoyuzhoufm.com:443:{resolve_ip}"])
                    cmd.append(url)
                    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=clean_env, timeout=15)
                    if res.returncode == 0 and res.stdout.strip():
                        html_home = res.stdout
                except Exception:
                    pass
            if html_home:
                episodes = re.findall(r'/episode/([a-zA-Z0-9]+)', html_home)
                if episodes:
                    unique_episodes = list(dict.fromkeys(episodes))
                    latest_ep_id = unique_episodes[0]
                    url = f"https://www.xiaoyuzhoufm.com/episode/{latest_ep_id}"
                    print(f"🎯 [LOG] 成功获取最新单集链接: {url}")
                else:
                    raise Exception("未能在播客节目主页中找到任何单集链接")
            else:
                raise Exception("无法抓取播客节目主页，请检查网络设置")

        html = None
        
        try:
            with httpx.Client(headers=DEFAULT_HEADERS, follow_redirects=True, trust_env=True, timeout=15.0, verify=False) as client:
                r = client.get(url)
                if r.status_code == 200:
                    html = r.text
                    print("🟢 [LOG] 成功通过 httpx (使用代理) 获取页面")
        except Exception as e:
            print(f"⚠️ [LOG] httpx (使用代理) 失败: {e}")
            
        if not html:
            try:
                with httpx.Client(headers=DEFAULT_HEADERS, follow_redirects=True, trust_env=False, timeout=15.0, verify=False) as client:
                    r = client.get(url)
                    if r.status_code == 200:
                        html = r.text
                        print("🟢 [LOG] 成功通过 httpx (直连) 获取页面")
            except Exception as e:
                print(f"⚠️ [LOG] httpx (直连) 失败: {e}")
                
        if not html:
            try:
                cmd = [CURL_CMD, "-k", "-L", "-s", url]
                res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=15)
                if res.returncode == 0 and res.stdout.strip():
                    html = res.stdout
                    print("🟢 [LOG] 成功通过 curl.exe (使用代理) 获取页面")
            except Exception as e:
                print(f"⚠️ [LOG] curl.exe (使用代理) 失败: {e}")
                
        if not html:
            try:
                resolve_ip = resolve_host_via_doh("www.xiaoyuzhoufm.com")
                clean_env = os.environ.copy()
                for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
                    clean_env.pop(key, None)
                cmd = [CURL_CMD, "-k", "-L", "-s", "--noproxy", "*"]
                if resolve_ip:
                    cmd.extend(["--resolve", f"www.xiaoyuzhoufm.com:443:{resolve_ip}"])
                cmd.append(url)
                res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=clean_env, timeout=15)
                if res.returncode == 0 and res.stdout.strip():
                    html = res.stdout
                    print("🟢 [LOG] 成功通过 curl.exe (直连 DoH) 获取页面")
            except Exception as e:
                print(f"⚠️ [LOG] curl.exe (直连 DoH) 失败: {e}")

        if not html:
            raise Exception("所有网页抓取策略均失败，无法获取小宇宙单集页面内容，请检查网络设置或稍后再试。")
            
        soup = BeautifulSoup(html, 'html.parser')
        next_data_tag = soup.find('script', id='__NEXT_DATA__')
        if not next_data_tag:
            raise Exception("无法在页面中找到 __NEXT_DATA__ 数据标签")
        
        data = json.loads(next_data_tag.string)
        
        episode_data = find_nested_key(data, "episode")
        
        if not episode_data:
            audio_url = find_nested_key(data, "audioUrl")
            if not audio_url:
                enclosure = find_nested_key(data, "enclosure")
                if isinstance(enclosure, dict):
                    audio_url = enclosure.get("url")
            title = find_nested_key(data, "title") or "未命名播客"
            shownotes = find_nested_key(data, "shownotes") or find_nested_key(data, "description") or ""
            podcast_name = "未知播客"
            podcast_data = find_nested_key(data, "podcast")
            if podcast_data and "title" in podcast_data:
                podcast_name = podcast_data["title"]
            like_count = find_nested_key(data, "clapCount") or find_nested_key(data, "likeCount") or 0
            comment_count = find_nested_key(data, "commentCount") or 0
        else:
            audio_url = episode_data.get("audioUrl")
            if not audio_url and "enclosure" in episode_data:
                enclosure = episode_data.get("enclosure")
                if isinstance(enclosure, dict):
                    audio_url = enclosure.get("url")
            if not audio_url and "media" in episode_data:
                media = episode_data.get("media")
                if isinstance(media, dict):
                    audio_url = media.get("source", {}).get("url")
                    
            title = episode_data.get("title", "未命名播客")
            shownotes = episode_data.get("shownotes") or episode_data.get("description") or ""
            podcast_name = episode_data.get("podcast", {}).get("title", "未知播客")
            like_count = episode_data.get("clapCount") or episode_data.get("likeCount", 0)
            comment_count = episode_data.get("commentCount", 0)

        pub_date = ""
        if episode_data:
            pub_date = episode_data.get("pubDate") or ""
        if not pub_date:
            pub_date = find_nested_key(data, "pubDate") or ""

        image_url = ""
        if episode_data:
            image_data = episode_data.get("image") or episode_data.get("podcast", {}).get("image")
            if isinstance(image_data, dict):
                image_url = image_data.get("picUrl") or ""
        if not image_url:
            podcast_data = find_nested_key(data, "podcast")
            if podcast_data and "image" in podcast_data:
                image_data = podcast_data["image"]
                if isinstance(image_data, dict):
                    image_url = image_data.get("picUrl") or ""
            if not image_url:
                image_url = find_nested_key(data, "picUrl") or ""

        if not audio_url:
            raise Exception("解析失败，未能在网页中找到音频下载直链")

        comments = extract_xiaoyuzhou_comments(data)
        clean_shownotes = clean_html_to_text(shownotes) if shownotes else ""

        return {
            "title": title,
            "podcast_name": podcast_name,
            "audio_url": audio_url,
            "shownotes": clean_shownotes,
            "like_count": like_count,
            "comment_count": comment_count,
            "comments": comments[:30],
            "image_url": image_url,
            "pub_date": pub_date,
            "source": "xiaoyuzhou"
        }

    def download_audio(self, url: str, local_path: str, progress_callback=None) -> dict:
        print("🎙️ [LOG] 识别为小宇宙链接，启动专有轻量级解析引擎...")
        metadata = self.parse_metadata(url)
        audio_url = metadata["audio_url"]
        
        if os.path.exists(local_path) and os.path.getsize(local_path) > 1024*1024:
            print(f"🎯 [LOG] 检测到本地小宇宙音频已存在且大小正常，跳过下载: {local_path}")
            if progress_callback:
                progress_callback(100.0)
            return metadata

        final_audio_url = audio_url
        try:
            final_audio_url = resolve_redirects_via_doh(audio_url)
            print(f"🎯 [LOG] 通过 DoH 追踪重定向后的最终音频直链: {final_audio_url}")
        except Exception as e_red:
            print(f"⚠️ [LOG] DoH 追踪重定向失败: {e_red}，将使用原链接")

        download_success = False
        
        # 策略 1: httpx (使用代理)
        print(f"📡 [LOG] 尝试通过 httpx (使用代理) 下载音频: {final_audio_url} -> {local_path}")
        try:
            with httpx.Client(headers=DEFAULT_HEADERS, verify=False, trust_env=True, timeout=120.0) as client:
                with client.stream("GET", final_audio_url) as r:
                    if r.status_code != 200:
                        raise Exception(f"HTTP status code {r.status_code}")
                    total_bytes = int(r.headers.get("content-length", 0))
                    downloaded_bytes = 0
                    with open(local_path, "wb") as f:
                        for chunk in r.iter_bytes(chunk_size=1024*1024):
                            f.write(chunk)
                            downloaded_bytes += len(chunk)
                            if progress_callback and total_bytes > 0:
                                percent = (downloaded_bytes / total_bytes) * 100.0
                                progress_callback(percent)
            print(f"🟢 [LOG] 音频下载完成 (httpx 代理模式) -> {local_path}")
            download_success = True
        except Exception as e_proxy:
            print(f"⚠️ [LOG] httpx (使用代理) 下载失败: {e_proxy}。正在切换为 httpx (直连模式) 下载...")
            if os.path.exists(local_path):
                try:
                    os.remove(local_path)
                except Exception:
                    pass
                    
        # 策略 2: httpx (直连)
        if not download_success:
            print(f"📡 [LOG] 尝试通过 httpx (直连) 下载音频: {final_audio_url} -> {local_path}")
            try:
                with httpx.Client(headers=DEFAULT_HEADERS, verify=False, trust_env=False, timeout=120.0) as client:
                    with client.stream("GET", final_audio_url) as r:
                        if r.status_code != 200:
                            raise Exception(f"HTTP status code {r.status_code}")
                        total_bytes = int(r.headers.get("content-length", 0))
                        downloaded_bytes = 0
                        with open(local_path, "wb") as f:
                            for chunk in r.iter_bytes(chunk_size=1024*1024):
                                f.write(chunk)
                                downloaded_bytes += len(chunk)
                                if progress_callback and total_bytes > 0:
                                    percent = (downloaded_bytes / total_bytes) * 100.0
                                    progress_callback(percent)
                print(f"🟢 [LOG] 音频下载完成 (httpx 直连模式) -> {local_path}")
                download_success = True
            except Exception as e_direct:
                print(f"⚠️ [LOG] httpx (直连) 下载失败: {e_direct}。正在准备切换为 curl.exe 兜底下载...")
                if os.path.exists(local_path):
                    try:
                        os.remove(local_path)
                    except Exception:
                        pass
                        
        # 策略 3: curl.exe (代理)
        if not download_success:
            print(f"📡 [LOG] 尝试通过 curl.exe (使用代理) 下载音频: {final_audio_url} -> {local_path}")
            try:
                from app.core.network_utils import CURL_SSL_ARGS
                cmd = [CURL_CMD, *CURL_SSL_ARGS, "-k", "-L", "-s", "-o", local_path, final_audio_url]
                res = subprocess.run(cmd, capture_output=True)
                if res.returncode == 0 and os.path.exists(local_path) and os.path.getsize(local_path) > 1024*1024:
                    print(f"🟢 [LOG] 音频下载完成 (curl.exe 代理模式) -> {local_path}")
                    download_success = True
                else:
                    raise Exception(f"curl.exe exit code {res.returncode}")
            except Exception as e_curl_proxy:
                print(f"⚠️ [LOG] curl.exe (使用代理) 下载失败: {e_curl_proxy}。正在准备切换为 curl.exe (直连 DoH) 兜底...")
                if os.path.exists(local_path):
                    try:
                        os.remove(local_path)
                    except Exception:
                        pass
                        
        # 策略 4: curl.exe (直连 DoH)
        if not download_success:
            print(f"📡 [LOG] 尝试通过 curl.exe (直连 DoH) 下载音频: {final_audio_url} -> {local_path}")
            try:
                clean_env = os.environ.copy()
                for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
                    clean_env.pop(key, None)
                from urllib.parse import urlparse
                from app.core.network_utils import CURL_SSL_ARGS
                final_audio_host = ""
                final_audio_port = 443
                try:
                    parsed_final = urlparse(final_audio_url)
                    final_audio_host = parsed_final.netloc
                    final_audio_port = 80 if parsed_final.scheme == "http" else 443
                except Exception:
                    pass
                final_cdn_ip = None
                if final_audio_host:
                    final_cdn_ip = resolve_host_via_doh(final_audio_host)
                cmd = [CURL_CMD, *CURL_SSL_ARGS, "--noproxy", "*", "-k", "-L", "-s"]
                if final_cdn_ip and final_audio_host:
                    cmd.extend(["--resolve", f"{final_audio_host}:{final_audio_port}:{final_cdn_ip}"])
                cmd.extend(["-o", local_path, final_audio_url])
                res = subprocess.run(cmd, capture_output=True, env=clean_env)
                if res.returncode != 0 or not os.path.exists(local_path) or os.path.getsize(local_path) <= 1024*1024:
                    raise Exception(f"curl.exe exit code {res.returncode}")
                print(f"🟢 [LOG] 音频下载完成 (curl.exe 直连 DoH) -> {local_path}")
                download_success = True
            except Exception as e_curl_direct:
                print(f"❌ [LOG] curl.exe (直连 DoH) 下载失败: {e_curl_direct}")
                if os.path.exists(local_path):
                    try:
                        os.remove(local_path)
                    except Exception:
                        pass
                        
        if not download_success:
            raise Exception("所有音频下载策略均已失败，请检查网络连接")
        
        if progress_callback:
            progress_callback(100.0)
        return metadata
