# 操作系统路径与环境配置指南 (OS Paths & Env Config)

whisperMe 在处理跨平台的音频、临时文件以及模型缓存时，针对不同操作系统的路径差异与特性进行了深度适配。本文档主要介绍相关的底层处理逻辑与环境配置项。

## 1. Windows 8.3 短路径 (Short Paths)

在 Windows 环境下，由于部分第三方音频处理工具（例如 `ffmpeg`）及某些 C++ 底层库（如 `faster-whisper` 引用的底层代码）对路径中包含**中文字符**或**特殊空格**的兼容性较差，whisperMe 会自动尝试将这些路径转换为 Windows 8.3 短路径格式（例如 `C:\Users\ADMINI~1\AppData\Local\Temp`）。

**行为说明**：
- 在调用 `ffmpeg` 进行音频裁剪（尤其是 `subprocess` 传参）前，系统会调用内核 API (`GetShortPathNameW`) 获取无中文的短路径。
- 如果您的临时文件夹路径（通常为 `C:\Users\您的用户名\AppData\Local\Temp`）包含中文字符，该机制将有效防止“文件找不到”或“解码失败”的底层报错。

## 2. TEMP/TMP 环境变量重定向

为了避免因 C 盘空间不足或用户名含中文字符导致的写入失败，whisperMe 支持通过 `config.json` 或环境变量重定向所有的临时文件生成位置。

**配置方法**：
可以在 `config.json` 中配置：
```json
{
  "temp_dir": "D:\\whisperMeTemp"
}
```
引擎启动时会自动接管并注入 `TEMP` 和 `TMP` 环境变量至所有子进程。

## 3. HuggingFace 模型缓存与镜像 (Linux / macOS / Windows)

PyAnnote 模型与 Whisper 模型在默认情况下会被下载到以下目录：
- **Windows**: `%USERPROFILE%\.cache\huggingface`
- **macOS / Linux**: `~/.cache/huggingface`

**HF 镜像源自动分发**：
如果在国内网络环境下下载慢或超时，程序会自动检测操作系统的语言环境（Locale）。
若系统检测到所处地区为中国大陆，将默认激活**镜像源加速**：
`HF_ENDPOINT=https://hf-mirror.com`

若您处于海外或使用了全局代理工具，可在 `config.json` 显式关闭：
```json
{
  "use_hf_mirror": false
}
```

## 4. 不同系统的 FFMPEG 寻址策略

whisperMe 内置了免配置的 FFmpeg 探测机制：
- **Windows**: 优先在当前项目根目录下的 `bin` 或系统 `PATH` 中寻找 `ffmpeg.exe`。
- **macOS**: 寻找 `/opt/homebrew/bin/ffmpeg` 或系统 `PATH`。
- **Linux**: 寻找 `/usr/bin/ffmpeg` 或 `/usr/local/bin/ffmpeg`。

如果您的 FFmpeg 安装在特殊位置，您可以直接在 `config.json` 中指定绝对路径：
```json
{
  "ffmpeg_path": "C:\\MyTools\\ffmpeg\\bin\\ffmpeg.exe"
}
```
