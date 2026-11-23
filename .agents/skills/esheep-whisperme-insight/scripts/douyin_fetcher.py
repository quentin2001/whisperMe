#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
douyin_fetcher.py - 抖音超高速音视频流直连提取与解析工具

特性:
- 原生协议极速直连，1-2秒内完成解析与下载，0浏览器开销，无403阻断
- 兼容 douyin.com, v.douyin.com 短链接 (302重定向追踪), iesdouyin.com 移动端链接与分享口令文本
- 提取完整元数据：标题、创作者/昵称、时长、封面图、话题标签、点赞/评论数
- 优先提取并直接下载原生单独音频流 (MP3)，备选拉取视频流并通过 FFmpeg 极速提取

用法示例:
    python douyin_fetcher.py https://www.douyin.com/video/7706576702873800699
    python douyin_fetcher.py "7.12 复制此链接，打开Dou音搜索... https://v.douyin.com/xxxx/" -o ./output.mp3
    python douyin_fetcher.py https://www.douyin.com/video/7706576702873800699 --metadata-only --json
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path

# 将项目 backend/ 添加到 sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[3]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.strategies.douyin_strategy import DouyinStrategy


def fetch_douyin(url_or_text: str, output_path: str = None, metadata_only: bool = False, as_json: bool = False):
    strategy = DouyinStrategy()
    start_time = time.time()

    if not strategy.can_handle(url_or_text):
        # 即使没有明显域名，尝试解析 ID 看是否能识别
        try:
            strategy._resolve_aweme_id(url_or_text)
        except Exception:
            print(f"❌ 错误: 无法识别的抖音链接或文本: {url_or_text}")
            sys.exit(1)

    print(f"🔍 [1/3] 开始解析抖音链接与元数据: {url_or_text}")
    try:
        metadata = strategy.parse_metadata(url_or_text)
    except Exception as e:
        print(f"❌ 解析元数据失败: {e}")
        sys.exit(1)

    parse_elapsed = time.time() - start_time
    print(f"⚡ 解析成功 (耗时: {parse_elapsed:.2f}s)")
    print(f"   📌 标题: {metadata.get('title')}")
    print(f"   👤 创作者: {metadata.get('podcast_name')}")
    print(f"   ⏱️ 时长: {metadata.get('duration')}")
    print(f"   🏷️ 标签: {', '.join(metadata.get('tags', [])) or '无'}")
    print(f"   🖼️ 封面图: {metadata.get('image_url')}")
    print(f"   ❤️ 点赞数: {metadata.get('like_count', 0):,} | 💬 评论数: {metadata.get('comment_count', 0):,}")

    if metadata_only:
        if as_json:
            print("\n--- JSON METADATA ---")
            print(json.dumps(metadata, ensure_ascii=False, indent=2))
        return metadata

    # 确定保存路径
    aweme_id = metadata.get("aweme_id", "douyin_audio")
    if not output_path:
        default_dir = PROJECT_ROOT / "downloads"
        default_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(default_dir / f"douyin_{aweme_id}.mp3")
    else:
        output_dir = os.path.dirname(os.path.abspath(output_path))
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

    print(f"📥 [2/3] 开始极速拉取原生音频直链 -> {output_path}")

    def progress(p):
        sys.stdout.write(f"\r   进度: [{int(p):3d}%] {'=' * int(p // 5)}{' ' * (20 - int(p // 5))}")
        sys.stdout.flush()

    dl_start = time.time()
    try:
        updated_meta = strategy.download_audio(url_or_text, output_path, progress_callback=progress)
        print() # 换行
    except Exception as e:
        print(f"\n❌ 下载音频失败: {e}")
        sys.exit(1)

    dl_elapsed = time.time() - dl_start
    total_elapsed = time.time() - start_time
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024) if os.path.exists(output_path) else 0

    print(f"✅ [3/3] 音频已成功下载完成！")
    print(f"   📁 文件路径: {output_path}")
    print(f"   📦 文件大小: {file_size_mb:.2f} MB")
    print(f"   ⚡ 下载耗时: {dl_elapsed:.2f}s (总耗时: {total_elapsed:.2f}s)")

    if as_json:
        print("\n--- JSON METADATA ---")
        print(json.dumps(updated_meta, ensure_ascii=False, indent=2))

    return updated_meta


def main():
    parser = argparse.ArgumentParser(description="抖音超高速原生音视频流直下与元数据解析工具")
    parser.add_argument("url", nargs="?", default="", help="抖音视频链接、短链接或包含链接的分享文本")
    parser.add_argument("--url", "-u", dest="opt_url", default="", help="指定抖音链接 (选项形式)")
    parser.add_argument("--output", "-o", default=None, help="目标音频文件保存路径 (.mp3)")
    parser.add_argument("--metadata-only", "-m", action="store_true", help="仅提取并展示元数据，不下载音频")
    parser.add_argument("--json", "-j", action="store_true", help="以 JSON 格式输出完整元数据")

    args = parser.parse_args()
    target_url = args.url or args.opt_url
    if not target_url:
        parser.print_help()
        sys.exit(1)

    fetch_douyin(
        url_or_text=target_url,
        output_path=args.output,
        metadata_only=args.metadata_only,
        as_json=args.json
    )


if __name__ == "__main__":
    main()
