import os
import sys
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
        msg = logging.Formatter.format(self, record)
        # 用彩色包裹级别名称和时间
        return f"{color}{msg}{COLOR_RESET}"

# 确保 logs 目录存在
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE_PATH = LOG_DIR / "backend.log"

# 创建根记录器
logger = logging.getLogger("whisperMe")
logger.setLevel(logging.INFO)

# 避免重复添加 Handler
if not logger.handlers:
    # 1. 控制台彩色输出 Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter(
        fmt="%(asctime)s [%(levelname)s] (%(filename)s:%(lineno)d) - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 2. 物理文件滚动日志 Handler (每天/超过10MB自动滚动，保留5个)
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
