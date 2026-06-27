#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
whisperMe CLI - 面向 AI Agent 自动化托管的全能命令行桥接器
零第三方依赖（仅标准库），跨平台支持 Windows/macOS/Linux
"""

import sys
import os
import json
import urllib.request
import urllib.error
import argparse
import subprocess
import time
import socket
from pathlib import Path

# --- 核心路径与配置 ---
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
CONFIG_FILE = ROOT_DIR / "config.json"
PID_FILE = ROOT_DIR / ".whisperMe.pid"
LOG_DIR = ROOT_DIR / "logs"
LOG_FILE = LOG_DIR / "whisperMe.log"

# Agent 如果修改了端口，可通过环境变量重载
API_PORT = int(os.environ.get("WHISPERME_PORT", 9101))
API_HOST = os.environ.get("WHISPERME_HOST", f"http://127.0.0.1:{API_PORT}")

# 保证 log 目录存在
LOG_DIR.mkdir(parents=True, exist_ok=True)

# --- 工具函数 ---

def print_result(data, as_json=False, exit_code=0):
    """统一的输出打印函数，支持人类友好或 JSON 格式"""
    if as_json:
        print(json.dumps(data, ensure_ascii=False))
    else:
        if isinstance(data, dict):
            for k, v in data.items():
                print(f"{k}: {v}")
        elif isinstance(data, list):
            for item in data:
                print(item)
        else:
            print(data)
    sys.exit(exit_code)

def make_request(method, endpoint, payload=None):
    """发起 HTTP 请求到 whisperMe 后端"""
    url = f"{API_HOST}{endpoint}"
    req = urllib.request.Request(url, method=method)
    req.add_header('Content-Type', 'application/json')
    
    data = None
    if payload:
        data = json.dumps(payload).encode('utf-8')
        
    try:
        with urllib.request.urlopen(req, data=data, timeout=10) as response:
            res_body = response.read().decode('utf-8')
            return json.loads(res_body) if res_body else {"status": "success"}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        try:
            err_json = json.loads(err_body)
            msg = err_json.get("detail", err_body)
        except json.JSONDecodeError:
            msg = err_body
        return {"error": f"HTTP {e.code}: {msg}"}
    except urllib.error.URLError as e:
        return {"error": f"连接服务失败 (确保服务正在运行): {str(e.reason)}"}
    except Exception as e:
        return {"error": f"请求异常: {str(e)}"}

def is_server_running():
    """通过 socket 快速检测端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', API_PORT)) == 0

def load_config():
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(config_data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)

def find_python():
    """跨平台寻找虚拟环境中的 Python"""
    venv_python_win = ROOT_DIR / "venv" / "Scripts" / "python.exe"
    venv_python_unix = ROOT_DIR / "venv" / "bin" / "python"
    
    if venv_python_win.exists(): return str(venv_python_win)
    if venv_python_unix.exists(): return str(venv_python_unix)
    return sys.executable

# --- 核心命令域 ---

def cmd_config(args):
    """离线配置域"""
    config = load_config()
    
    if args.sub == "show":
        # 敏感信息打码处理 (面向人类打印时)
        safe_config = config.copy()
        for k in ['hf_token', 'online_api_key', 'online_summary_api_key', 'smtp_password']:
            if safe_config.get(k):
                safe_config[k] = safe_config[k][:3] + "***" + safe_config[k][-3:] if len(safe_config[k])>6 else "***"
        print_result(safe_config if not args.json else config, as_json=args.json)
        
    elif args.sub == "get":
        if args.key in config:
            print_result({args.key: config[args.key]}, as_json=args.json)
        else:
            print_result({"error": f"未找到配置项: {args.key}"}, as_json=args.json, exit_code=1)
            
    elif args.sub == "set":
        for kv in args.key_values:
            if "=" not in kv:
                print_result({"error": f"格式错误, 应为 key=value: {kv}"}, as_json=args.json, exit_code=1)
            k, v = kv.split("=", 1)
            # 简单类型转换
            if v.lower() in ('true', 'false'):
                v = v.lower() == 'true'
            elif v.isdigit():
                v = int(v)
            config[k] = v
            
        save_config(config)
        print_result({"status": "success", "message": f"已更新 {len(args.key_values)} 个配置项"}, as_json=args.json)
        
    elif args.sub == "check":
        missing_req = []
        missing_opt = []
        
        # 必填校验逻辑
        if config.get("asr_mode") == "online" and config.get("online_asr_provider") != "mimo" and not config.get("online_api_key"):
            missing_req.append("online_api_key (非MiMo在线ASR需要提供)")
        if config.get("summary_mode") == "online" and not config.get("online_summary_api_key"):
            missing_req.append("online_summary_api_key (在线总结模型必填)")
            
        # 选填校验逻辑
        if not config.get("hf_token"):
            missing_opt.append("hf_token (选填，配置后可启用声纹分离)")
            
        res = {
            "ready": len(missing_req) == 0,
            "missing_required": missing_req,
            "missing_optional": missing_opt
        }
        print_result(res, as_json=args.json, exit_code=3 if not res["ready"] else 0)

def cmd_server(args):
    """服务启停管理"""
    running = is_server_running()
    
    if args.sub == "status":
        pid = None
        if PID_FILE.exists():
            with open(PID_FILE, 'r') as f:
                pid = f.read().strip()
        status_info = {"status": "running" if running else "stopped", "port": API_PORT, "pid": pid}
        print_result(status_info, as_json=args.json)
        
    elif args.sub == "start":
        if running:
            print_result({"status": "already_running", "message": "服务已在运行中"}, as_json=args.json)
            return
            
        # 拉起后台进程 (通过 launcher.py)
        launcher_script = SCRIPT_DIR / "launcher.py"
        python_exe = find_python()
        
        try:
            if sys.platform == "win32":
                # Windows 静默后台启动
                subprocess.Popen([python_exe, str(launcher_script)], creationflags=0x08000000)
            else:
                # macOS/Linux 守护进程启动
                with open(os.devnull, 'w') as devnull:
                    subprocess.Popen([python_exe, str(launcher_script)], stdout=devnull, stderr=devnull, start_new_session=True)
            
            # 轮询等待端口占用
            for _ in range(15):
                time.sleep(1)
                if is_server_running():
                    print_result({"status": "started", "message": f"服务已在后台启动 (端口: {API_PORT})"}, as_json=args.json)
                    return
                    
            print_result({"status": "error", "message": "服务启动超时，请检查日志"}, as_json=args.json, exit_code=1)
        except Exception as e:
            print_result({"error": str(e)}, as_json=args.json, exit_code=1)
            
    elif args.sub == "stop":
        if not running and not PID_FILE.exists():
            print_result({"status": "already_stopped", "message": "服务未运行"}, as_json=args.json)
            return
            
        # 优先使用 API 优雅关闭
        if running:
            res = make_request("POST", "/api/shutdown")
            if "error" not in res:
                time.sleep(2) # 等待释放
        
        # 兜底：强杀 PID
        if PID_FILE.exists():
            try:
                with open(PID_FILE, 'r') as f:
                    pid = int(f.read().strip())
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
                else:
                    os.kill(pid, signal.SIGTERM)
                PID_FILE.unlink()
            except Exception:
                pass
                
        print_result({"status": "stopped", "message": "服务已停止"}, as_json=args.json)
        
    elif args.sub == "logs":
        if not LOG_FILE.exists():
            print_result({"error": "日志文件不存在"}, as_json=args.json, exit_code=1)
        
        lines = args.tail
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                content = f.readlines()[-lines:]
            if args.json:
                print_result({"logs": content}, as_json=True)
            else:
                print("".join(content))
        except Exception as e:
            print_result({"error": str(e)}, as_json=args.json, exit_code=1)

def cmd_task(args):
    """任务管理域"""
    if args.sub == "create":
        payload = {"url": args.url}
        if args.asr:
            payload["asr_mode"] = args.asr
        res = make_request("POST", "/api/tasks", payload)
        print_result(res, as_json=args.json, exit_code=2 if "error" in res else 0)
        
    elif args.sub == "list":
        res = make_request("GET", "/api/tasks")
        if args.json or "error" in res:
            print_result(res, as_json=args.json, exit_code=2 if "error" in res else 0)
        else:
            # 人类友好输出
            print(f"{'ID':<38} | {'状态':<15} | {'进度':<5} | {'标题'}")
            print("-" * 80)
            for t in res.get("tasks", []):
                print(f"{t['id']} | {t['status']:<15} | {t.get('progress', 0):>3}% | {t.get('title', '未知')[:30]}")
                
    elif args.sub == "status":
        res = make_request("GET", f"/api/tasks/{args.id}")
        if args.json or "error" in res:
            print_result(res, as_json=args.json, exit_code=2 if "error" in res else 0)
        else:
            print(f"任务 ID: {res.get('id')}")
            print(f"标题: {res.get('title')}")
            print(f"状态: {res.get('status')} (进度: {res.get('progress')}%)")
            print(f"时长: {res.get('duration_str')}")
            if res.get("summary"):
                print("\n[AI 总结 (片段)]:")
                print(res.get("summary")[:200] + "...\n")
                
    elif args.sub == "export":
        fmt = args.format
        res = make_request("GET", f"/api/tasks/{args.id}/transcript?format={fmt}")
        if "error" in res:
            print_result(res, as_json=args.json, exit_code=2)
        else:
            if args.json:
                print_result(res, as_json=True)
            else:
                # 导出通常只打印纯内容，方便 Agent 收集
                print(res.get("content", ""))

def cmd_ask(args):
    """播客互动问答"""
    res = make_request("POST", f"/api/tasks/{args.id}/qa", {"question": args.question})
    if "error" in res:
        print_result(res, as_json=args.json, exit_code=2)
    else:
        if args.json:
            print_result(res, as_json=True)
        else:
            print(f"Q: {args.question}")
            print(f"A: {res.get('answer')}")

def cmd_health(args):
    """系统健康检查"""
    res_perf = make_request("GET", "/api/performance")
    res_deps = make_request("GET", "/api/dependencies")
    
    if "error" in res_perf:
        print_result({"status": "unreachable", "error": res_perf["error"]}, as_json=args.json, exit_code=2)
    else:
        out = {
            "status": "healthy",
            "cpu_percent": res_perf.get("cpu_percent"),
            "ram_used_gb": res_perf.get("ram_used_gb"),
            "gpu": res_perf.get("gpu"),
            "dependencies": res_deps
        }
        print_result(out, as_json=args.json)

def cmd_prompt(args):
    """Prompt 模板管理域"""
    if args.sub == "show":
        res = make_request("GET", "/api/prompt")
        if "error" in res:
            print_result(res, as_json=args.json, exit_code=2)
        else:
            if args.json:
                print_result(res, as_json=True)
            else:
                print("当前 AI 提示词模板:\n")
                print("-" * 50)
                print(res.get("prompt", ""))
                print("-" * 50)
                
    elif args.sub == "set":
        payload = {"prompt": args.content}
        res = make_request("POST", "/api/prompt", payload)
        if "error" in res:
            print_result(res, as_json=args.json, exit_code=2)
        else:
            print_result({"status": "success", "message": "提示词已更新生效"}, as_json=args.json)

# --- 主入口 ---

def main():
    parser = argparse.ArgumentParser(description="whisperMe Agent CLI - 全能命令行桥接器")
    parser.add_argument("--json", action="store_true", help="强制输出为 JSON 格式 (Agent 友好)")
    subparsers = parser.add_subparsers(dest="cmd", required=True)
    
    # config
    p_config = subparsers.add_parser("config", help="配置管理")
    sp_config = p_config.add_subparsers(dest="sub", required=True)
    sp_config.add_parser("show")
    sp_config.add_parser("check")
    p_c_get = sp_config.add_parser("get")
    p_c_get.add_argument("key")
    p_c_set = sp_config.add_parser("set")
    p_c_set.add_argument("key_values", nargs="+", help="key=value format")
    
    # server
    p_server = subparsers.add_parser("server", help="后台服务管理")
    sp_server = p_server.add_subparsers(dest="sub", required=True)
    sp_server.add_parser("start")
    sp_server.add_parser("stop")
    sp_server.add_parser("status")
    p_s_logs = sp_server.add_parser("logs")
    p_s_logs.add_argument("--tail", type=int, default=50)
    
    # task
    p_task = subparsers.add_parser("task", help="任务管理")
    sp_task = p_task.add_subparsers(dest="sub", required=True)
    p_t_create = sp_task.add_parser("create")
    p_t_create.add_argument("url")
    p_t_create.add_argument("--asr", choices=["online", "local"])
    sp_task.add_parser("list")
    p_t_status = sp_task.add_parser("status")
    p_t_status.add_argument("id")
    p_t_export = sp_task.add_parser("export")
    p_t_export.add_argument("id")
    p_t_export.add_argument("--format", choices=["text", "srt", "vtt", "json", "markdown"], default="markdown")
    
    # prompt
    p_prompt = subparsers.add_parser("prompt", help="AI 提示词管理")
    sp_prompt = p_prompt.add_subparsers(dest="sub", required=True)
    sp_prompt.add_parser("show")
    p_p_set = sp_prompt.add_parser("set")
    p_p_set.add_argument("content", help="完整的提示词内容")

    # ask
    p_ask = subparsers.add_parser("ask", help="基于播客内容问答")
    p_ask.add_argument("id", help="任务 ID")
    p_ask.add_argument("question", help="你的问题")
    
    # health
    subparsers.add_parser("health", help="系统健康检查")
    
    # version
    subparsers.add_parser("version", help="版本信息")

    args = parser.parse_args()

    # 路由
    if args.cmd == "config": cmd_config(args)
    elif args.cmd == "server": cmd_server(args)
    elif args.cmd == "task": cmd_task(args)
    elif args.cmd == "prompt": cmd_prompt(args)
    elif args.cmd == "ask": cmd_ask(args)
    elif args.cmd == "health": cmd_health(args)
    elif args.cmd == "version":
        ver_file = ROOT_DIR / "VERSION"
        ver = ver_file.read_text().strip() if ver_file.exists() else "unknown"
        print_result({"version": ver}, as_json=args.json)

if __name__ == "__main__":
    main()
