import os
import re
import json
import hashlib
import subprocess
import httpx
from bs4 import BeautifulSoup
import yt_dlp
from app.config import (
    FFMPEG_PATH, 
    FFMPEG_BIN_DIR, 
    SHORT_DOWNLOADS_DIR, 
    TEMP_SANDBOX_DIR
)

# 递归在嵌套字典/列表中搜索特定键
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

# 深度搜索特定路径下的数据，获取小宇宙评论
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
    # 按点赞数降序排序
    comments_list.sort(key=lambda x: x.get("likes", 0), reverse=True)
    return comments_list

def clean_html_to_text(html_content: str) -> str:
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    # Replace <br> and <br/> with newline
    for br in soup.find_all(["br", "br/"]):
        br.replace_with("\n")
    # Add newlines around paragraph-like block elements
    for block in soup.find_all(["p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li"]):
        block.insert_before("\n")
        block.insert_after("\n")
    # Get text with no separator
    text = soup.get_text(separator="")
    # Normalize consecutive newlines
    import re
    text = re.sub(r'\n\s*\n', '\n\n', text)
    # Remove leading/trailing spaces on each line
    lines = [line.strip() for line in text.split('\n')]
    return '\n'.join(lines).strip()

class PodcastDownloader:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def resolve_host_via_doh(self, host: str) -> str:
        """
        通过 DoH 查询主机的真实 A 记录 IP
        """
        if not host or host.replace('.', '').isdigit():
            return host
        
        import urllib.request
        import json
        import ssl
        
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
            
        return None

    def resolve_redirects_via_doh(self, url: str, max_redirects: int = 5) -> str:
        """
        在 Python 中使用 DoH 绕过 Fake-IP 透明代理，手动追踪所有 HTTP 3xx 重定向，获取最终音频下载直链
        """
        import urllib.request
        import urllib.parse
        import ssl
        import socket
        
        current_url = url
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
                
        opener = urllib.request.build_opener(
            NoRedirectHandler, 
            urllib.request.HTTPSHandler(context=ctx), 
            urllib.request.ProxyHandler({})
        )
        
        for i in range(max_redirects):
            parsed = urllib.parse.urlparse(current_url)
            host_name = parsed.netloc
            if ":" in host_name:
                host_name = host_name.split(":", 1)[0]
                
            # 如果是 Tencent CDN 或者是已知的最终音频域名，直接终止重定向追踪以规避后续握手异常
            if "xmcdn.com" in host_name or "xyzcdn.net" in host_name:
                break
                
            real_ip = self.resolve_host_via_doh(host_name)
            if not real_ip:
                break
                
            original_getaddrinfo = socket.getaddrinfo
            
            def custom_getaddrinfo(h, port, family=0, type=0, proto=0, flags=0):
                if h == host_name:
                    return original_getaddrinfo(real_ip, port, family, type, proto, flags | socket.AI_NUMERICHOST)
                return original_getaddrinfo(h, port, family, type, proto, flags)
                
            socket.getaddrinfo = custom_getaddrinfo
            
            try:
                req = urllib.request.Request(current_url, headers=headers)
                with opener.open(req, timeout=5) as resp:
                    code = resp.getcode()
                    if code in (301, 302, 303, 307, 308):
                        loc = resp.headers.get("Location")
                        if loc:
                            current_url = urllib.parse.urljoin(current_url, loc)
                            continue
                    break
            except urllib.error.HTTPError as e:
                code = e.getcode()
                if code in (301, 302, 303, 307, 308):
                    loc = e.headers.get("Location")
                    if loc:
                        current_url = urllib.parse.urljoin(current_url, loc)
                        continue
                break
            except Exception:
                break
            finally:
                socket.getaddrinfo = original_getaddrinfo
                
        return current_url

    def parse_metadata(self, url: str) -> dict:
        """
        仅抓取并解析链接元数据而不下载音频文件
        """
        # 判断是否为小宇宙链接
        if "xiaoyuzhoufm.com" in url:
            return self.parse_xiaoyuzhou(url)
            
        # 判断是否为 Bilibili 链接
        elif "bilibili.com" in url or "b23.tv" in url:
            real_url = url
            if "b23.tv" in url:
                try:
                    with httpx.Client(trust_env=False, follow_redirects=True) as client:
                        resp = client.head(url, timeout=5.0)
                        real_url = str(resp.url)
                except Exception as e:
                    print(f"⚠️ [LOG] 还原 Bilibili 短链接失败: {e}")
            
            bv_match = re.search(r"(BV[a-zA-Z0-9]+)", real_url)
            if not bv_match:
                raise Exception("未能在链接中解析出 Bilibili BV 号")
            bvid = bv_match.group(1)
            
            mobile_url = f"https://m.bilibili.com/video/{bvid}"
            mobile_headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
                "Referer": "https://m.bilibili.com/"
            }
            
            with httpx.Client(trust_env=False) as client:
                r = client.get(mobile_url, headers=mobile_headers, timeout=15.0)
                if r.status_code != 200:
                    raise Exception(f"请求 Bilibili 移动端网页失败: HTTP {r.status_code}")
                
                html = r.text
                state_match = re.search(r"window\.__INITIAL_STATE__\s*=\s*({.*?});", html)
                if not state_match:
                    raise Exception("未能从 Bilibili 移动端网页中解析 window.__INITIAL_STATE__")
                
                state = json.loads(state_match.group(1))
                view_info = state.get("video", {}).get("viewInfo", {})
                title = view_info.get("title", "未知 Bilibili 视频")
                desc = view_info.get("desc", "")
                uploader = view_info.get("owner", {}).get("name", "B站UP主")
                
                return {
                    "title": title,
                    "podcast_name": uploader,
                    "audio_url": url,
                    "shownotes": desc,
                    "like_count": view_info.get("stat", {}).get("like", 0),
                    "comment_count": view_info.get("stat", {}).get("reply", 0),
                    "comments": [],
                    "image_url": view_info.get("pic", ""),
                    "source": "bilibili_private"
                }
        else:
            # 使用 yt-dlp 抓取通用媒体信息 (不下载)
            ydl_opts = {
                'ffmpeg_location': FFMPEG_BIN_DIR,
                'quiet': True,
                'nocheckcertificate': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', '未知音频')
                return {
                    "title": title,
                    "podcast_name": info.get('uploader', '未知上传者'),
                    "audio_url": url,
                    "shownotes": info.get('description', ''),
                    "like_count": info.get('like_count', 0),
                    "comment_count": info.get('comment_count', 0),
                    "comments": [],
                    "image_url": info.get('thumbnail', ''),
                    "source": "ytdlp"
                }

    def parse_xiaoyuzhou(self, url: str) -> dict:
        """
        抓取并解析小宇宙播客单集页面
        """
        # 使用 curl.exe 绕过 Cloudflare TLS 校验与代理拦截，确保 100% 成功抓取 HTML
        print(f"📡 [LOG] 正在使用 curl.exe 绕过 Cloudflare 抓取小宇宙页面: {url}")
        
        # 使用 DoH 绕过本地 Clash DNS 劫持与 SSL 拦截
        resolve_ip = None
        try:
            resolve_ip = self.resolve_host_via_doh("www.xiaoyuzhoufm.com")
            if resolve_ip:
                print(f"🎯 [LOG] 通过 DoH 解析出小宇宙真实 IP: {resolve_ip}")
        except Exception as e:
            print(f"⚠️ [LOG] DoH 解析失败 (将尝试普通直连方式): {e}")

        # 清理代理环境变量，防止 curl.exe 被代理劫持导致 SSL 握手失败 (如 Clash 35 错误)
        clean_env = os.environ.copy()
        for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
            clean_env.pop(key, None)
            
        cmd = ["curl.exe", "-k", "-s"]
        if resolve_ip:
            cmd.extend(["--resolve", f"www.xiaoyuzhoufm.com:443:{resolve_ip}"])
        cmd.append(url)
        
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=clean_env)
        if res.returncode != 0:
            raise Exception(f"curl.exe 抓取页面失败，返回码: {res.returncode}")
        
        html = res.stdout
        soup = BeautifulSoup(html, 'html.parser')
        next_data_tag = soup.find('script', id='__NEXT_DATA__')
        if not next_data_tag:
            raise Exception("无法在页面中找到 __NEXT_DATA__ 数据标签")
        
        data = json.loads(next_data_tag.string)
        
        # 使用递归方法弹性搜索核心字段，防止 NextJS props 结构变动
        episode_data = find_nested_key(data, "episode")
        
        if not episode_data:
            # 备用方案：在整个 JSON 中搜索音频地址和标题
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

        # Extract pubDate
        pub_date = ""
        if episode_data:
            pub_date = episode_data.get("pubDate") or ""
        if not pub_date:
            pub_date = find_nested_key(data, "pubDate") or ""

        # Extract cover image URL
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

        # 抓取评论列表
        comments = extract_xiaoyuzhou_comments(data)

        # 获取 Shownotes 中的文本（去除 HTML 标签）
        clean_shownotes = clean_html_to_text(shownotes) if shownotes else ""

        return {
            "title": title,
            "podcast_name": podcast_name,
            "audio_url": audio_url,
            "shownotes": clean_shownotes,
            "like_count": like_count,
            "comment_count": comment_count,
            "comments": comments[:30],  # 取前 30 条热门评论进行情感/含金量分析
            "image_url": image_url,
            "pub_date": pub_date,
            "source": "xiaoyuzhou"
        }

    def download_url_audio(self, url: str, progress_callback=None) -> tuple[str, dict]:
        """
        下载链接音频，支持本地路径绕过、小宇宙解析和 yt-dlp 兜底
        返回: (本地下载文件路径, 播客元数据字典)
        """
        # 1. 物理安全护城河：如果是本地已存在的音频文件，直接豁免网络请求，秒级导入
        if os.path.exists(url) and os.path.isfile(url):
            print(f"📁 [LOG] 识别为本地文件路径，跳过网络请求直接导入: {url}")
            filename = os.path.basename(url)
            name_without_ext = os.path.splitext(filename)[0]
            metadata = {
                "title": name_without_ext,
                "podcast_name": "本地导入",
                "audio_url": url,
                "shownotes": "本地导入的音频文件，完全离线处理。",
                "like_count": 0,
                "comment_count": 0,
                "comments": [],
                "source": "local"
            }
            return url, metadata

        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        
        # 判断是否为小宇宙链接
        if "xiaoyuzhoufm.com" in url:
            print("🎙️ [LOG] 识别为小宇宙链接，启动专有轻量级解析引擎...")
            metadata = self.parse_xiaoyuzhou(url)
            audio_url = metadata["audio_url"]
            file_ext = "mp3"
            
            # 如果音频链接有具体的后缀，进行截取
            match_ext = re.search(r'\.(\w+)(?:\?|$)', audio_url)
            if match_ext:
                file_ext = match_ext.group(1)
                
            local_filename = os.path.join(SHORT_DOWNLOADS_DIR, f"{url_hash}.{file_ext}")
            
            # 增加本地缓存检测，如果文件已存在且大小正常，则直接秒级导入，绕过所有网络层
            if os.path.exists(local_filename) and os.path.getsize(local_filename) > 1024*1024:
                print(f"🎯 [LOG] 检测到本地小宇宙音频已存在且大小正常，跳过下载: {local_filename}")
                if progress_callback:
                    progress_callback(100.0)
                return local_filename, metadata

            # 首先，我们在 Python 里使用 DoH 追踪所有的 3xx 重定向，获取最终的直链 URL！
            final_audio_url = audio_url
            try:
                final_audio_url = self.resolve_redirects_via_doh(audio_url)
                print(f"🎯 [LOG] 通过 DoH 追踪重定向后的最终音频直链: {final_audio_url}")
            except Exception as e_red:
                print(f"⚠️ [LOG] DoH 追踪重定向失败: {e_red}，将使用原链接")

            # 优先使用 Python httpx (禁用代理) 进行流式高速下载，实时回传进度以优化用户界面体验
            print(f"📡 [LOG] 正在从直链直连下载音频 (httpx): {final_audio_url} -> {local_filename}")
            try:
                with httpx.Client(headers=self.headers, verify=False, trust_env=False, timeout=120.0) as client:
                    with client.stream("GET", final_audio_url) as r:
                        if r.status_code != 200:
                            raise Exception(f"HTTP status code {r.status_code}")
                        total_bytes = int(r.headers.get("content-length", 0))
                        downloaded_bytes = 0
                        with open(local_filename, "wb") as f:
                            for chunk in r.iter_bytes(chunk_size=1024*1024):
                                f.write(chunk)
                                downloaded_bytes += len(chunk)
                                if progress_callback and total_bytes > 0:
                                    percent = (downloaded_bytes / total_bytes) * 100.0
                                    progress_callback(percent)
                print(f"🟢 [LOG] 音频下载完成 (httpx) -> {local_filename}")
            except Exception as e:
                print(f"⚠️ [LOG 警告] httpx 下载失败: {e}，正在切换为 curl.exe 进行兜底下载...")
                # 物理清除可能损坏的未完成文件
                if os.path.exists(local_filename):
                    try:
                        os.remove(local_filename)
                    except Exception:
                        pass
                # 兜底使用 curl.exe (清理代理环境变量防止被劫持导致 SSL 失败)
                clean_env = os.environ.copy()
                for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
                    clean_env.pop(key, None)

                # 使用 final_audio_url 进行解析与下载
                from urllib.parse import urlparse
                final_audio_host = ""
                final_audio_port = 443
                try:
                    parsed_final = urlparse(final_audio_url)
                    final_audio_host = parsed_final.netloc
                    final_audio_port = 80 if parsed_final.scheme == "http" else 443
                except Exception:
                    pass

                # 用 DoH 解析最终主机的 IP
                final_cdn_ip = None
                if final_audio_host:
                    try:
                        final_cdn_ip = self.resolve_host_via_doh(final_audio_host)
                    except Exception as de:
                        print(f"⚠️ [LOG] 解析最终主机 DoH 失败: {de}")

                cmd = ["curl.exe", "--ssl-no-revoke", "--noproxy", "*", "-k", "-L", "-s"]
                if final_cdn_ip and final_audio_host:
                    cmd.extend(["--resolve", f"{final_audio_host}:{final_audio_port}:{final_cdn_ip}"])
                cmd.extend(["-o", local_filename, final_audio_url])
                
                res = subprocess.run(cmd, capture_output=True, env=clean_env)
                if res.returncode != 0:
                    raise Exception(f"curl.exe 下载音频失败，返回码: {res.returncode}")
            
            if progress_callback:
                progress_callback(100.0)
            return local_filename, metadata
        elif "bilibili.com" in url or "b23.tv" in url:
            local_filename = os.path.join(SHORT_DOWNLOADS_DIR, f"{url_hash}.mp3")
            if os.path.exists(local_filename) and os.path.getsize(local_filename) > 1024*1024:
                print(f"🎯 [LOG] 检测到本地 Bilibili 音频文件已存在，跳过下载与提取: {local_filename}")
                metadata = self.parse_metadata(url)
                if progress_callback:
                    progress_callback(100.0)
                return local_filename, metadata

            print("🎬 [LOG] 检测到 Bilibili 链接，启动私有高性能下载引擎...")
            real_url = url
            if "b23.tv" in url:
                try:
                    with httpx.Client(trust_env=False, follow_redirects=True) as client:
                        resp = client.head(url, timeout=5.0)
                        real_url = str(resp.url)
                except Exception as e:
                    print(f"⚠️ [LOG] 还原 Bilibili 短链接失败: {e}")
            
            bv_match = re.search(r"(BV[a-zA-Z0-9]+)", real_url)
            if not bv_match:
                raise Exception("未能在链接中解析出 Bilibili BV 号")
            bvid = bv_match.group(1)
            
            mobile_url = f"https://m.bilibili.com/video/{bvid}"
            mobile_headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
                "Referer": "https://m.bilibili.com/"
            }
            
            print(f"🟢 [LOG] 抓取移动端页面: {mobile_url}")
            with httpx.Client(trust_env=False) as client:
                r = client.get(mobile_url, headers=mobile_headers, timeout=15.0)
                if r.status_code != 200:
                    raise Exception(f"请求 Bilibili 移动端网页失败: HTTP {r.status_code}")
                
                html = r.text
                state_match = re.search(r"window\.__INITIAL_STATE__\s*=\s*({.*?});", html)
                if not state_match:
                    raise Exception("未能从 Bilibili 移动端网页中解析 window.__INITIAL_STATE__")
                
                state = json.loads(state_match.group(1))
                view_info = state.get("video", {}).get("viewInfo", {})
                aid = view_info.get("aid")
                cid = view_info.get("cid")
                title = view_info.get("title", "未知 Bilibili 视频")
                desc = view_info.get("desc", "")
                uploader = view_info.get("owner", {}).get("name", "B站UP主")
                
                if not aid or not cid:
                    raise Exception("解析 Bilibili 视频 aid 或 cid 失败")
                
                playurl_api = f"https://api.bilibili.com/x/player/playurl?avid={aid}&cid={cid}&qn=16&type=&otype=json&platform=html5&high_quality=1"
                print(f"🟢 [LOG] 请求 Playurl API...")
                api_headers = {
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15",
                    "Referer": f"https://www.bilibili.com/video/{bvid}/"
                }
                
                r_api = client.get(playurl_api, headers=api_headers, timeout=10.0)
                if r_api.status_code != 200:
                    raise Exception(f"Playurl API 请求失败: HTTP {r_api.status_code}")
                
                api_data = r_api.json()
                if api_data.get("code") != 0:
                    raise Exception(f"Playurl API 错误 ({api_data.get('code')}): {api_data.get('message')}")
                
                durl = api_data.get("data", {}).get("durl", [])
                if not durl:
                    raise Exception("未找到 Bilibili 流媒体下载地址")
                
                play_url = durl[0].get("url")
                
                temp_mp4 = os.path.join(SHORT_DOWNLOADS_DIR, f"{url_hash}.mp4")
                print(f"🟢 [LOG] 开始下载媒体流 -> {temp_mp4}")
                stream_headers = {
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15",
                    "Referer": f"https://www.bilibili.com/video/{bvid}/"
                }
                
                downloaded = 0
                total_bytes = durl[0].get("size", 0)
                
                with open(temp_mp4, "wb") as f:
                    with client.stream("GET", play_url, headers=stream_headers, timeout=30.0) as response:
                        if response.status_code != 200:
                            raise Exception(f"视频流下载请求失败: HTTP {response.status_code}")
                        for chunk in response.iter_bytes(chunk_size=16384):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback and total_bytes > 0:
                                percent = (downloaded / total_bytes) * 90.0
                                progress_callback(percent)
                                
            local_filename = os.path.join(SHORT_DOWNLOADS_DIR, f"{url_hash}.mp3")
            print(f"🟢 [LOG] 提取音频 -> {local_filename}")
            
            ffmpeg_cmd = [FFMPEG_PATH, "-y", "-i", temp_mp4, "-vn", "-acodec", "libmp3lame", "-ab", "128k", local_filename]
            res = subprocess.run(ffmpeg_cmd, capture_output=True)
            
            if res.returncode != 0:
                print("⚠️ [LOG 警告] 使用指定 FFMPEG_PATH 提取失败，尝试全局 ffmpeg 兜底...")
                res_fallback = subprocess.run(["ffmpeg", "-y", "-i", temp_mp4, "-vn", "-acodec", "libmp3lame", "-ab", "128k", local_filename], capture_output=True)
                if res_fallback.returncode != 0:
                    if os.path.exists(temp_mp4):
                        try:
                            os.remove(temp_mp4)
                        except Exception:
                            pass
                    raise Exception(f"FFmpeg 提取音频失败: {res.stderr.decode('utf-8', errors='ignore')}")
            
            if os.path.exists(temp_mp4):
                try:
                    os.remove(temp_mp4)
                except Exception:
                    pass
            
            metadata = {
                "title": title,
                "podcast_name": uploader,
                "audio_url": url,
                "shownotes": desc,
                "like_count": view_info.get("stat", {}).get("like", 0),
                "comment_count": view_info.get("stat", {}).get("reply", 0),
                "comments": [],
                "image_url": view_info.get("pic", ""),
                "source": "bilibili_private"
            }
            
            if progress_callback:
                progress_callback(100.0)
            return local_filename, metadata
        else:
            local_filename = os.path.join(SHORT_DOWNLOADS_DIR, f"{url_hash}.mp3")
            if os.path.exists(local_filename) and os.path.getsize(local_filename) > 1024*1024:
                print(f"🎯 [LOG] 检测到本地通用音频已存在，跳过 yt-dlp 下载: {local_filename}")
                metadata = self.parse_metadata(url)
                if progress_callback:
                    progress_callback(100.0)
                return local_filename, metadata

            # 使用 yt-dlp 下载通用播客（如 YouTube 等）
            print("🎬 [LOG] 识别为通用媒体链接，启动 yt-dlp 抓取...")
            safe_outtmpl = os.path.join(SHORT_DOWNLOADS_DIR, f"{url_hash}.%(ext)s")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': safe_outtmpl,
                'ffmpeg_location': FFMPEG_BIN_DIR,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '128',
                }],
                'quiet': True,
                'nocheckcertificate': True,  # 忽略 SSL 证书校验
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', '未知音频')
                metadata = {
                    "title": title,
                    "podcast_name": info.get('uploader', '未知上传者'),
                    "audio_url": url,
                    "shownotes": info.get('description', ''),
                    "like_count": info.get('like_count', 0),
                    "comment_count": info.get('comment_count', 0),
                    "comments": [],
                    "image_url": info.get('thumbnail', ''),
                    "source": "ytdlp"
                }
                
            local_filename = os.path.join(SHORT_DOWNLOADS_DIR, f"{url_hash}.mp3")
            return local_filename, metadata

    def preprocess_audio(self, input_path: str) -> str:
        """
        使用 FFmpeg 将音频文件标准化为单声道、16kHz WAV 格式
        这是 Whisper & PyAnnote 声纹的最优输入格式
        """
        filename = os.path.basename(input_path)
        name_without_ext = os.path.splitext(filename)[0]
        output_wav = os.path.join(TEMP_SANDBOX_DIR, f"{name_without_ext}_standardized.wav")
        
        # 统一转成 8.3 格式
        from app.config import get_short_path_name
        short_input = get_short_path_name(input_path)
        short_output = get_short_path_name(output_wav)
        
        print(f"🎛️ [LOG] 本地 FFmpeg 启动预处理 -> {short_output}")
        # -ac 1 (单声道), -ar 16000 (16000Hz 采样率)
        cmd = [
            FFMPEG_PATH, 
            '-y', 
            '-i', short_input, 
            '-ac', '1', 
            '-ar', '16000', 
            short_output
        ]
        
        # 运行 FFmpeg 并隐藏输出
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            err_msg = res.stderr.decode('utf-8', errors='ignore')
            raise Exception(f"FFmpeg 音频预处理失败: {err_msg}")
            
        return output_wav
