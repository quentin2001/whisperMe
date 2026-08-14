---
name: esheep-whisperme-insight
description: >-
  Use when transcribing audio or video content to text and generating
  AI-powered deep content analysis reports. Supports cloud ASR APIs
  (MiMo, OpenAI Whisper, custom HTTP), local ASR service detection,
  and local/URL media files. After transcription, leverages the agent's
  own context window for structured insight generation.
metadata:
  author: quentin2001
  version: "1.0.0"
  source: https://github.com/quentin2001/whisperMe
---

# esheep-whisperme-insight

## Overview

将音频/视频内容转录为文字，然后利用 Agent 自身的上下文窗口进行深度内容挖掘与结构化分析。

**核心原则**: ASR 转录走云端 API（或用户已有的本地 ASR 服务），AI 分析不调用外部 LLM，直接由 Agent 自身完成——Agent 就是最强的 LLM。

## When to Use

- 用户提供了音频/视频文件（本地路径或 URL）需要转录
- 需要从播客、会议录音、讲座、访谈中提取深度洞察
- 用户要求生成结构化的内容分析报告

**When NOT to Use:**
- 用户已经有了文字转录稿，只需要分析 → 直接使用 `references/prompt-templates.md` 中的 Prompt 模板
- 用户需要实时语音识别（流式 ASR）→ 本 Skill 处理的是离线文件

## Core Workflow

```
媒体输入 (本地文件 / URL)
    │
    ▼
[Step 0 - 可选] 算力检测 → 参考 references/gpu-probe-guide.md
    │
    ▼
[Step 1] 媒体获取
    ├── 本地文件 → 直接使用
    └── URL → curl/wget 下载到临时目录
    │
    ▼
[Step 2] ASR 转录 → 运行 scripts/asr_cloud.py
    ├── 路径 A: 云端 API (mimo / openai / custom)
    ├── 路径 B: 本地 ASR 服务 (--probe-local 检测)
    └── 路径 C: 用户已有转录文本 → 跳过
    │
    ▼
[Step 3] 文本去噪
    │  去除中文语气词填充（嗯、啊、呃、对对对...）
    │
    ▼
[Step 4] Agent 上下文内 AI 深度分析
    │  将转录文本注入当前对话
    │  应用 references/prompt-templates.md 中的深度分析模板
    │
    ▼
输出: 结构化 Markdown 深度分析报告
```

## Step 1: Media Acquisition

### 本地文件
直接确认文件存在并检查格式（支持 mp3/wav/flac/m4a/mp4/mkv/webm 等 ffmpeg 兼容格式）。

### URL 下载
```bash
# 音频/视频直链
curl -L -o media_file.mp3 "<URL>"

# 如果是 YouTube/Bilibili 等平台链接，需要 yt-dlp
yt-dlp -x --audio-format mp3 -o "media_file.%(ext)s" "<URL>"
```

**判断逻辑**: URL 以 `.mp3/.wav/.mp4/.mkv/.webm` 等结尾 → 直链下载。否则尝试 yt-dlp。

## Step 2: ASR Transcription

运行内置脚本完成转录：

```bash
# 使用 MiMo ASR（推荐，中文效果最佳）
python scripts/asr_cloud.py <media_file> \
  --provider mimo \
  --api-key <MIMO_API_KEY> \
  --model mimo-v2.5-asr

# 使用 OpenAI Whisper API
python scripts/asr_cloud.py <media_file> \
  --provider openai \
  --api-key <OPENAI_API_KEY>

# 探测本地 ASR 服务
python scripts/asr_cloud.py --probe-local
```

脚本路径: 本 Skill 目录下的 `scripts/asr_cloud.py`。
**前置依赖**: Python 3.8+、系统已安装 ffmpeg。

脚本输出 JSON Lines 格式到 stdout：
```json
{"start": 0.0, "end": 5.2, "text": "大家好，欢迎收听本期播客"}
{"start": 5.2, "end": 12.8, "text": "今天我们聊一聊人工智能的最新进展"}
```

### ASR API Key 获取

如果用户没有 API Key，引导获取：
- **MiMo ASR**: 访问 https://mimo.xiaomi.com 注册获取
- **OpenAI Whisper**: 使用已有的 OpenAI API Key，或兼容服务（Groq、Together 等）

### 本地 ASR 服务优先

运行 `--probe-local` 检测用户本地是否已有 ASR 服务运行。如果检测到 whisperMe 服务（localhost:9101），优先通过其 API 提交任务。

## Step 3: Transcript Denoising

对中文转录文本执行去噪，移除高频语气词填充：

```python
import re
# 纯语气词行过滤
filler_pattern = re.compile(
    r'^[\s]*(嗯+|啊+|呃+|额+|哦+|唉+|哎+|诶+|对对对|是是是|好好好|'
    r'对的对的|没错没错|就是就是|然后然后)[\s。，、！？.,!?]*$'
)
# 行内语气词清理
filler_inline = re.compile(
    r'(?:^|(?<=[。，、！？.,!?\s]))'
    r'(?:嗯+|啊+|呃+|额+|哦+|就是说|那个|然后嘛|对吧|你知道吗|怎么说呢)'
    r'(?=[。，、！？.,!?\s]|$)'
)
```

Agent 在将转录文本注入自身上下文前应先执行此去噪步骤。

## Step 4: AI Insight Generation

**这是本 Skill 的核心价值所在。**

Agent 将去噪后的转录文本直接作为自身对话上下文的一部分，应用 `references/prompt-templates.md` 中的**深度分析模板**生成结构化报告。

### 执行要点

1. **构造数据块**: 组装转录文本 + 可用的元数据（标题、描述、评论等）
2. **选择模板**: 从 `references/prompt-templates.md` 读取深度分析 Prompt
3. **发言人检测**: 如果转录文本中没有区分不同发言人，追加「单发言人防幻觉约束」（模板中有）
4. **长文本策略**: 如果转录超过 50,000 字符：
   - 分段注入上下文，每段生成局部总结
   - 最后合并为完整报告
5. **直接输出**: Agent 在当前对话中直接输出 Markdown 格式的分析报告

### 数据注入格式

```markdown
# 事实源数据

## 媒体元数据
- 标题: {title}
- 来源: {source}
- 时长: {duration}

## 转录文本
---
{transcript_text}
---
```

## GPU Capability Probe (Optional)

当用户询问是否可以用本地模型时，参考 `references/gpu-probe-guide.md` 执行算力检测。

快速检测命令：
```bash
# Windows
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader

# Linux/Mac
nvidia-smi 2>/dev/null || echo "No NVIDIA GPU"
```

根据 VRAM 大小给出建议：
- ≥ 8GB VRAM → 推荐本地 faster-whisper large-v3
- 4-8GB → faster-whisper medium
- < 4GB 或无 GPU → 推荐云端 ASR（MiMo 或 OpenAI Whisper）

## Common Mistakes

| 错误 | 正确做法 |
|---|---|
| 在分析报告中编造转录文本里没有的人名 | 严格遵守防幻觉守则，未提及则标注"未讨论" |
| 忘记去噪直接分析，浪费 token | 先去噪再注入上下文 |
| 长播客一次性注入超出上下文 | 分段总结后合并 |
| 没有 ffmpeg 就尝试运行 asr_cloud.py | 先检查 `ffmpeg -version`，缺失则引导安装 |
| 视频文件当做不支持的格式 | ffmpeg 自动提取音轨，视频和音频处理流程一致 |
