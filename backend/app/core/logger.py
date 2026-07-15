import os
import sys
import copy
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ANSI 颜色转义序列
COLOR_RESET = "\033[0m"
COLOR_DEBUG = "\033[36m"    # 青色
COLOR_INFO = "\033[32m"     # 绿色
COLOR_WARNING = "\033[33m"  # 黄色
COLOR_ERROR = "\033[31m"    # 红色
COLOR_CRITICAL = "\033[35m" # 紫色

class NoiseLogFilter(logging.Filter):
    def filter(self, record):
        if record.name == "uvicorn.access" and len(record.args) >= 3:
            path = record.args[2]
            # Silence polling endpoints and static resources
            if any(p in path for p in ["/api/tasks", "hf-token-status", "/api/models/registry", "static"]) or path.endswith((".js", ".css", ".png", ".ico")):
                return False
        return True

class ColoredFormatter(logging.Formatter):
    """自定义带彩色的日志格式器"""
    
    def format(self, record):
        # 针对不同的日志级别添加彩色前缀
        level = record.levelno
        if level == logging.DEBUG:
            color = COLOR_DEBUG
        elif level == logging.INFO:
            color = COLOR_INFO
        elif level == logging.WARNING:
            color = COLOR_WARNING
        elif level == logging.ERROR:
            color = COLOR_ERROR
        elif level == logging.CRITICAL:
            color = COLOR_CRITICAL
        else:
            color = COLOR_RESET
            
        # 复制 record 以免影响文件日志输出
        record_copy = copy.copy(record)
        msg = logging.Formatter.format(self, record_copy)
        # 用彩色包裹级别名称和时间
        return f"{color}{msg}{COLOR_RESET}"

# 确保 logs 目录存在
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE_PATH = LOG_DIR / "backend.log"

# 创建根记录器
logger = logging.getLogger("whisperMe")
logger.setLevel(logging.INFO)

# Create or reuse handlers
console_handler = None
file_handler = None

for h in logger.handlers:
    if isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler):
        console_handler = h
    elif isinstance(h, RotatingFileHandler):
        file_handler = h

if console_handler is None:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter(
        fmt="%(asctime)s [%(levelname)s] (%(filename)s:%(lineno)d) - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

# Add NoiseLogFilter to console_handler
if not any(isinstance(f, NoiseLogFilter) for f in console_handler.filters):
    console_handler.addFilter(NoiseLogFilter())

if file_handler is None:
    file_handler = RotatingFileHandler(
        filename=str(LOG_FILE_PATH),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] (%(filename)s:%(lineno)d) - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

# 封装调试与日志追踪方法
def info(msg, *args, **kwargs):
    logger.info(msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    logger.error(msg, *args, **kwargs)

def warning(msg, *args, **kwargs):
    logger.warning(msg, *args, **kwargs)

def debug(msg, *args, **kwargs):
    logger.debug(msg, *args, **kwargs)
