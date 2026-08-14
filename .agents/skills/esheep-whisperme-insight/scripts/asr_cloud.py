import os
import sys
import json
import math
import base64
import urllib.request
import urllib.parse
import urllib.error
import subprocess
import argparse
import tempfile
import time
import re

# ==============================================================================
# Helper Functions
# ==============================================================================

def log_progress(msg: str):
    """Print progress info to stderr so stdout stays clean for JSON output."""
    sys.stderr.write(f"[INFO] {msg}\n")
    sys.stderr.flush()

def log_error(msg: str):
    """Print error info to stderr."""
    sys.stderr.write(f"[ERROR] {msg}\n")
    sys.stderr.flush()

def download_url(url: str, dest_path: str):
    """Download a file from a URL to a local destination."""
    log_progress(f"Downloading media from {url}...")
    try:
        urllib.request.urlretrieve(url, dest_path)
        log_progress(f"Downloaded to {dest_path}")
    except Exception as e:
        log_error(f"Failed to download URL (下载失败): {e}")
        sys.exit(1)

def get_media_duration(file_path: str) -> float:
    """Get the duration of a media file in seconds using ffmpeg."""
    try:
        cmd = ["ffmpeg", "-i", file_path]
        # ffmpeg outputs info to stderr
        result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
        output = result.stderr
        
        # Look for "Duration: HH:MM:SS.ss"
        match = re.search(r"Duration:\s*(\d{2}):(\d{2}):(\d{2}\.\d+)", output)
        if match:
            hours, minutes, seconds = match.groups()
            duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            return duration
        else:
            log_error(f"Could not parse duration from ffmpeg output for {file_path}")
            return 0.0
    except FileNotFoundError:
        log_error("ffmpeg is not installed or not in PATH (未找到 ffmpeg). Please install ffmpeg.")
        sys.exit(1)
    except Exception as e:
        log_error(f"Error getting media duration: {e}")
        return 0.0

def extract_mp3_chunk(input_path: str, offset: float, duration: float, output_path: str):
    """Extract an audio chunk from media using ffmpeg."""
    try:
        cmd = [
            "ffmpeg", "-y", "-i", input_path, 
            "-ss", str(offset), "-t", str(duration),
            "-codec:a", "libmp3lame", "-b:a", "32k", "-ac", "1",
            output_path
        ]
        result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
        if result.returncode != 0:
            log_error(f"ffmpeg chunk extraction failed (分片提取失败): {result.stderr}")
            return False
        return True
    except Exception as e:
        log_error(f"Error during chunk extraction: {e}")
        return False

def audio_file_to_base64(file_path: str) -> str:
    """Convert an audio file to base64 string with mime type."""
    ext = os.path.splitext(file_path)[1].lower()
    mime = "audio/mp3" if ext == ".mp3" else "audio/wav"
    with open(file_path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode("utf-8")

def build_multipart_form(fields: dict, file_path: str, file_field_name: str = "file") -> tuple:
    """Build a multipart/form-data payload."""
    boundary = "----WebKitFormBoundary" + base64.b64encode(os.urandom(16)).decode('utf-8').replace("=", "")
    body = bytearray()
    
    # Add text fields
    for k, v in fields.items():
        if v is not None:
            body.extend(f"--{boundary}\r\n".encode('utf-8'))
            body.extend(f"Content-Disposition: form-data; name=\"{k}\"\r\n\r\n".encode('utf-8'))
            body.extend(f"{v}\r\n".encode('utf-8'))
            
    # Add file field
    if file_path and os.path.exists(file_path):
        filename = os.path.basename(file_path)
        body.extend(f"--{boundary}\r\n".encode('utf-8'))
        body.extend(f"Content-Disposition: form-data; name=\"{file_field_name}\"; filename=\"{filename}\"\r\n".encode('utf-8'))
        body.extend(f"Content-Type: audio/mpeg\r\n\r\n".encode('utf-8'))
        with open(file_path, "rb") as f:
            body.extend(f.read())
        body.extend(b"\r\n")
        
    body.extend(f"--{boundary}--\r\n".encode('utf-8'))
    return body, boundary

def extract_json_path(data: dict, path: str):
    """Simple JSONPath-like extractor supporting $.key1.key2 and $.key1[0].key2 patterns."""
    if not path or not path.startswith('$.'):
        return data
        
    path = path[2:] # remove $.
    path_parts = path.replace('[', '.').replace(']', '').split('.')
    path_parts = [p for p in path_parts if p]
    
    curr = data
    for part in path_parts:
        if isinstance(curr, dict):
            curr = curr.get(part)
        elif isinstance(curr, list) and part.isdigit():
            idx = int(part)
            if idx < len(curr):
                curr = curr[idx]
            else:
                return None
        else:
            return None
    return curr

# ==============================================================================
# Provider Implementations
# ==============================================================================

def call_mimo(file_path: str, api_key: str, base_url: str, model: str) -> list:
    """Call Xiaomi MiMo ASR API."""
    if not base_url:
        base_url = "https://token-plan-sgp.xiaomimimo.com/v1"
    if not model:
        model = "mimo-v2.5-asr"
        
    endpoint = f"{base_url}/chat/completions"
    audio_base64 = audio_file_to_base64(file_path)
    
    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [{
                "type": "input_audio",
                "input_audio": {
                    "data": audio_base64,
                    "format": "mp3"
                }
            }]
        }],
        "stream": False
    }
    
    req = urllib.request.Request(endpoint, data=json.dumps(payload).encode('utf-8'))
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")
    
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            resp_body = response.read().decode('utf-8')
            resp_json = json.loads(resp_body)
            
            # MiMo specific extraction
            try:
                text = resp_json["choices"][0]["message"]["content"]
                return [{"text": text}]
            except (KeyError, IndexError) as e:
                log_error(f"Unexpected MiMo response format: {resp_body}")
                return []
    except urllib.error.HTTPError as e:
        log_error(f"MiMo API HTTP Error: {e.code} - {e.read().decode('utf-8')}")
        return []
    except Exception as e:
        log_error(f"MiMo API Error: {e}")
        return []

def call_openai(file_path: str, api_key: str, base_url: str, model: str) -> list:
    """Call OpenAI Whisper API."""
    if not base_url:
        base_url = "https://api.openai.com/v1"
    if not model:
        model = "whisper-1"
        
    endpoint = f"{base_url}/audio/transcriptions"
    
    fields = {
        "model": model,
        "response_format": "verbose_json"
    }
    
    body, boundary = build_multipart_form(fields, file_path, "file")
    
    req = urllib.request.Request(endpoint, data=body)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Authorization", f"Bearer {api_key}")
    
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            resp_body = response.read().decode('utf-8')
            resp_json = json.loads(resp_body)
            
            if "segments" in resp_json:
                results = []
                for seg in resp_json["segments"]:
                    results.append({
                        "start": seg.get("start", 0.0),
                        "end": seg.get("end", 0.0),
                        "text": seg.get("text", "")
                    })
                return results
            elif "text" in resp_json:
                return [{"text": resp_json["text"]}]
            else:
                log_error(f"Unexpected OpenAI response format: {resp_body}")
                return []
    except urllib.error.HTTPError as e:
        log_error(f"OpenAI API HTTP Error: {e.code} - {e.read().decode('utf-8')}")
        return []
    except Exception as e:
        log_error(f"OpenAI API Error: {e}")
        return []

def call_custom(file_path: str, api_key: str, endpoint: str, method: str, headers: str, body_template: str, jsonpath: str) -> list:
    """Call a Custom HTTP ASR API."""
    if not endpoint:
        log_error("Custom provider requires --custom-endpoint")
        return []
        
    audio_base64_str = audio_file_to_base64(file_path)
    
    # Process headers
    req_headers = {}
    if headers:
        try:
            req_headers = json.loads(headers)
        except json.JSONDecodeError:
            log_error("Invalid JSON format for --custom-headers")
            return []
            
    # Process body
    data = None
    if body_template:
        body_str = body_template.replace("{{audio_base64}}", audio_base64_str)
        data = body_str.encode('utf-8')
        
    req = urllib.request.Request(endpoint, data=data, method=method)
    for k, v in req_headers.items():
        if v == "{{api_key}}":
            v = api_key
        elif "{api_key}" in v:
            v = v.replace("{api_key}", api_key)
        req.add_header(k, v)
        
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            resp_body = response.read().decode('utf-8')
            resp_json = json.loads(resp_body)
            
            if jsonpath:
                text = extract_json_path(resp_json, jsonpath)
                if text is not None:
                    return [{"text": str(text)}]
                else:
                    log_error(f"Failed to extract text using JSONPath {jsonpath} from response")
                    return []
            else:
                return [{"text": resp_body}]
    except urllib.error.HTTPError as e:
        log_error(f"Custom API HTTP Error: {e.code} - {e.read().decode('utf-8')}")
        return []
    except Exception as e:
        log_error(f"Custom API Error: {e}")
        return []

# ==============================================================================
# Utility Commands
# ==============================================================================

def probe_local():
    """Probe common local ASR service endpoints."""
    endpoints = [
        {"name": "Ollama", "url": "http://localhost:11434/"},
        {"name": "LM Studio", "url": "http://localhost:1234/v1/models"},
        {"name": "Whisper local", "url": "http://localhost:10095/v1/models"}
    ]
    
    log_progress("Probing local endpoints...")
    found = False
    for ep in endpoints:
        try:
            req = urllib.request.Request(ep["url"], method="GET")
            # Set small timeout
            with urllib.request.urlopen(req, timeout=2) as response:
                log_progress(f"✅ Found local service: {ep['name']} at {ep['url']} (Status: {response.status})")
                found = True
        except Exception:
            pass
            
    if not found:
        log_progress("❌ No common local services detected.")
    sys.exit(0)

# ==============================================================================
# Main
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Standalone zero-dependency cloud ASR client with audio chunking via ffmpeg.",
        epilog="""
Examples:
  # MiMo ASR
  python asr_cloud.py audio.mp3 --provider mimo --api-key YOUR_KEY
  
  # OpenAI Whisper
  python asr_cloud.py video.mp4 --provider openai --api-key YOUR_KEY
  
  # Custom API
  python asr_cloud.py audio.wav --provider custom \\
    --custom-endpoint http://localhost:8000/asr \\
    --custom-method POST \\
    --custom-headers '{"Content-Type": "application/json"}' \\
    --custom-body-template '{"audio": "{{audio_base64}}"}' \\
    --custom-response-jsonpath '$.data.text'
        """,
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument("media", nargs="?", help="Local path or URL to media file (audio/video)")
    parser.add_argument("--provider", choices=["mimo", "openai", "custom"], required=False, help="ASR provider to use")
    parser.add_argument("--api-key", default="", help="API key for the provider")
    parser.add_argument("--base-url", default="", help="Base URL for mimo or openai")
    parser.add_argument("--model", default="", help="Model name")
    parser.add_argument("--chunk-duration", type=int, default=120, help="Duration of each audio chunk in seconds (default: 120)")
    
    parser.add_argument("--custom-endpoint", default="", help="Endpoint URL for custom provider")
    parser.add_argument("--custom-method", default="POST", help="HTTP method for custom provider (default: POST)")
    parser.add_argument("--custom-headers", default="", help="JSON string of HTTP headers for custom provider")
    parser.add_argument("--custom-body-template", default="", help="JSON body template for custom provider. Use {{audio_base64}} placeholder")
    parser.add_argument("--custom-response-jsonpath", default="", help="JSONPath to extract text from custom provider response")
    
    parser.add_argument("--probe-local", action="store_true", help="Probe common local ASR service endpoints and exit")
    
    args = parser.parse_args()
    
    if args.probe_local:
        probe_local()
        
    if not args.media:
        parser.print_help()
        sys.exit(1)
        
    if not args.provider:
        log_error("--provider is required when not probing")
        sys.exit(1)
        
    # Handle URL vs Local file
    media_path = args.media
    is_temp = False
    if media_path.startswith("http://") or media_path.startswith("https://"):
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".tmp")
        os.close(tmp_fd)
        download_url(media_path, tmp_path)
        media_path = tmp_path
        is_temp = True
        
    try:
        duration = get_media_duration(media_path)
        log_progress(f"Media duration: {duration:.2f} seconds")
        
        if duration == 0:
            # Fallback to single chunk processing if duration cannot be determined
            duration = args.chunk_duration
            
        chunk_duration = float(args.chunk_duration)
        total_chunks = math.ceil(duration / chunk_duration)
        
        tmp_dir = tempfile.mkdtemp()
        
        for i in range(total_chunks):
            offset = i * chunk_duration
            chunk_file = os.path.join(tmp_dir, f"chunk_{i}.mp3")
            
            log_progress(f"Processing chunk {i+1}/{total_chunks} (offset: {offset:.2f}s)...")
            success = extract_mp3_chunk(media_path, offset, chunk_duration, chunk_file)
            
            if not success:
                continue
                
            segments = []
            if args.provider == "mimo":
                segments = call_mimo(chunk_file, args.api_key, args.base_url, args.model)
            elif args.provider == "openai":
                segments = call_openai(chunk_file, args.api_key, args.base_url, args.model)
            elif args.provider == "custom":
                segments = call_custom(
                    chunk_file, args.api_key, args.custom_endpoint, 
                    args.custom_method, args.custom_headers, 
                    args.custom_body_template, args.custom_response_jsonpath
                )
                
            for seg in segments:
                # Adjust timestamps for the chunk offset if provider returned them
                start = seg.get("start", 0.0) + offset
                end = seg.get("end", chunk_duration) + offset
                text = seg.get("text", "")
                
                # Output JSON line to stdout
                sys.stdout.write(json.dumps({"start": start, "end": end, "text": text}, ensure_ascii=False) + "\n")
                sys.stdout.flush()
                
            # Cleanup chunk
            if os.path.exists(chunk_file):
                os.remove(chunk_file)
                
        # Cleanup temp dir
        os.rmdir(tmp_dir)
        
    finally:
        if is_temp and os.path.exists(media_path):
            os.remove(media_path)

if __name__ == "__main__":
    main()
