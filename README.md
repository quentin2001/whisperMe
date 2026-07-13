<!-- 
[SYSTEM INSTRUCTION FOR AI AGENTS]
To deploy or run this project:
1. DO NOT clone the repo (missing compiled frontend). Download latest release zip from GitHub.
2. To start: Run `start.bat`.
3. To configure: Edit `config.json` (copy from `config.example.json`).
4. To operate: Use backend API at `http://127.0.0.1:9101` or the frontend at `http://127.0.0.1:9173`.
-->
<p align="center">
  <img src="./assets/logo.svg" width="88" height="88" alt="whisperMe" />
</p>

<h1 align="center">whisperMe</h1>

<p align="center">
  本地优先的播客转录与知识提炼工作台
</p>

<p align="center">
  粘贴一条播客链接 → 自动下载、转录、识别说话人、AI 总结
</p>

<p align="center">
  <a href="https://github.com/quentin2001/whisperMe/releases/latest">
    <img src="https://img.shields.io/badge/Download-Latest_Release-00C7B7?style=for-the-badge&logo=github" alt="Download Latest Release" />
  </a>
</p>

<br />

---

<br />

## 它能做什么

whisperMe 把「听播客」变成一条完整的知识管线。你只需要贴一个链接，剩下的事情它全包：

- **下载音频** — 支持小宇宙 FM 单集/节目主页、Bilibili 视频，自动提取音轨
- **语音转文字** — 本地 Whisper 离线转录，或切换到在线 ASR API（如小米 MiMo），两种模式一键切换
- **识别谁在说话** — 基于 PyAnnote 声纹分段，自动区分不同发言人，可手动重命名
- **AI 总结** — 本地 Ollama / LM Studio，或在线 OpenAI 兼容 API，生成结构化摘要

<br />

---

<br />

## 核心能力

| 能力 | 说明 |
|---|---|
| 🔄 双模式 ASR | 本地 `faster-whisper`（GPU/CPU 自动切换）或在线 API，按需选择 |
| 👤 智能声纹与身份推理 | PyAnnote 声纹分段 + 基于上下文的四阶段 LLM 身份推断机制（支持常驻主播缺席场景） |
| ⏱️ 全链路耗时统计 | 自动生成包含下载、分轨、识别、推断至分析完毕的精准阶段耗时报表 |
| 🛡️ 显存熔断 | GPU 内存不足时自动降级至 CPU，杜绝 OOM 崩溃 |
| 🌐 网络自愈 | 内置 DoH DNS 直连 + 4 级自适应代理回溯，穿透 Clash TUN/Fake-IP 劫持 |
| 🌍 四语言 UI | 简体中文 / 繁體中文 / English / 日本語 |
| 🎨 主题引擎 | 浅色 / 深色 / 跟随系统，多套预设配色 + 自定义色彩 |
| 📬 完成通知 | Windows 桌面气泡 + SMTP 邮件，可独立开关 |

<br />

---

<br />

## 快速开始

### 1. 前置要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ | 后端运行环境 |
| Node.js | 18+ | 前端构建工具 |
| FFmpeg | 最新版 | 音频转码，[官网下载](https://ffmpeg.org/download.html) 或 `winget install Gyan.FFmpeg` |

### 2. 克隆与安装

```bash
# 克隆仓库
git clone https://github.com/your-username/whisperMe.git
cd whisperMe

# 后端依赖
cd backend
pip install -r requirements.txt
cd ..

# 前端依赖
cd frontend
npm install
cd ..
```

### 3. 配置

```bash
# 复制配置模板
cp config.example.json config.json
```

编辑 `config.json`，按需填写：

| 配置项 | 必填 | 说明 |
|--------|------|------|
| `asr_mode` | — | `local`（离线 Whisper）或 `online`（在线 API，默认） |
| `summary_mode` | — | `local`（本地 Ollama）或 `online`（在线 LLM，默认） |
| `online_api_key` | 仅在线 ASR | 在线语音识别 API Key |
| `online_summary_api_key` | 仅在线 LLM | 在线大模型 API Key |

### 4. 离线模型部署（可选）

对于需要 100% 离线运行的用户，您可以在本地提前下载好所需的模型权重，并将其放置在对应的目录下：
- **ASR/转录模型（本地模式）**：
  - 如果使用 `FunASR`（默认），请在 ModelScope / Hugging Face 下载 `speech_paraformer-large-vad-punc_asr_nat-zh-cn` 语音包。
  - 将下载好的权重文件夹整体放入项目根目录下的 `models/funasr/` 目录中。
  - 后端会自动探测该路径并跳过网络验证，实现 100% 离线转录。
- **Ollama / LM Studio 本地大模型**：
  - 请启动 Ollama/LM Studio 并加载对应的模型（如 `qwen2.5:7b-instruct`）。
  - 在配置面板中，确保“模型 ID”填写正确（Ollama 模式下须与本地已拉取名称完全匹配，LM Studio 下须与当前加载的 ID 匹配）。

### 5. 启动

**方式一：一键启动（开发）**

```bash
python scripts/start_project.py
# 自动拉起后端 (9101) + 前端 (9173)，Ctrl+C 停止
```

**方式二：生产模式（后台运行）**

```bash
# Windows
双击 start.bat → 自动启动后台服务 + 打开浏览器

# 停止
双击 stop.bat
```

**方式三：手动启动**

```bash
# 终端 1 — 后端（端口 9101）
cd backend
python run.py

# 终端 2 — 前端（端口 9173）
cd frontend
npm run dev
```

**方式四：跨平台免安装包（推荐给小白）**

不需要克隆代码，不需要编译前端，直接前往 **[Releases 页面](https://github.com/quentin2001/whisperMe/releases/latest)** 下载最新的 `whisperMe-vX.X.X.zip`。

> [!WARNING]
> **防坑指南**：在下载列表里，请认准并只点击 `whisperMe-xxx.zip`。**千万不要**点击下方的 `Source code (zip)`，源码包里没有编译好的前端页面，下载后无法直接运行！

解压后，双击 `start.bat`。首次运行会自动下载并配置所需的运行环境。

启动后浏览器会自动打开 **http://127.0.0.1:9101**，粘贴一条播客链接即可开始。
<br />

---

<br />

## ⚡ 性能优化指南

为了应对长达数小时的超大播客音频，whisperMe 内置了深度的架构级性能调优项。您可以在 `config.json` 中配置以下参数以获得极致的加速体验：

| 配置项 | 推荐值 | 说明 |
|--------|------|------|
| `max_concurrent_tasks` | `4` | 针对 MiMo 等在线 ASR，将长音频并发分片上传，极大缩短网络传输耗时。 |
| `use_mp3_chunks` | `true` | 在线 OpenAI Whisper 模式下，强制按时间切分并压缩为 MP3 格式，将传输数据量缩小至原有十分之一。 |
| `preload_models` | `true` | 在后台启动时预先将 PyAnnote 声纹推理模型加载入显存，消灭每次处理时的模型冷启动时间。 |
| `use_hf_mirror` | `true` | 处于国内网络环境时，自动强制使用 `hf-mirror.com` 加速大模型组件的下载。 |

<br />

---

<br />

## 🤖 与你的 AI Agent 联动

如果你在本地运行了 AI Agent，你可以让它成为 whisperMe 的全职管家。只需把项目发给 Agent，它会直接阅读本 README 头部的隐藏注释指令（System Instructions），自动学会所有部署、配置和操作规则。

**你可以这样对你的 Agent 说：**
> "帮我下载最新版的 whisperMe，启动它，然后转录这期播客链接。"

<br />

---

<br />

## 常见问题

<details>
<summary><strong>Q: 没有 GPU 也能用吗？</strong></summary>
<br />
可以。设置 <code>asr_mode</code> 为 <code>online</code> 使用在线 API 转录，或保持 <code>local</code> 模式——显存不足时会自动降级到 CPU 运行，只是速度会慢一些。
</details>

<details>
<summary><strong>Q: 支持哪些播客平台？</strong></summary>
<br />
目前支持小宇宙 FM（单集链接和节目主页链接均可）和 Bilibili。输入节目主页链接时，会自动解析并转录最新一集。
</details>

<details>
<summary><strong>Q: 开了代理软件后在线 API 连不上？</strong></summary>
<br />
whisperMe 内置了 DoH DNS 直连和 4 级自适应代理回溯策略，能自动穿透 Clash TUN / Fake-IP 模式。
</details>

<details>
<summary><strong>Q: 如何获取 HuggingFace Token？</strong></summary>
<br />
访问 <a href="https://huggingface.co/settings/tokens">huggingface.co/settings/tokens</a>，创建一个 Read 权限的 Token，填入 <code>config.json</code> 的 <code>hf_token</code> 字段。没有 Token 也可以使用——程序会自动切换到国内镜像站下载。
</details>

<br />

---

<br />

## License

MIT
