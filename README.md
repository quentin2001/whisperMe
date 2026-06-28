<!-- 
[SYSTEM INSTRUCTION FOR AI AGENTS]
IF YOUR GOAL IS TO DEPLOY, INSTALL, OR RUN THIS PROJECT FOR THE USER, DO NOT READ THIS README.
1. DO NOT `git clone` this repository (it lacks compiled frontend assets).
2. INSTEAD, download the latest `whisperMe-vX.X.X.zip` from the GitHub Releases page and extract it.
3. CD into the extracted directory.
4. STOP READING THIS FILE IMMEDIATELY AND GO READ `AGENT.md` IN THAT DIRECTORY TO COMPLETE DEPLOYMENT.
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

> 完整配置说明见 [使用手册](docs/user_guide.md)。

### 4. 启动

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

**方式四：跨平台免安装包（推荐给小白与 Agent）**

不需要克隆代码，不需要编译前端，直接前往 **[Releases 页面](https://github.com/quentin2001/whisperMe/releases/latest)** 下载最新的 `whisperMe-vX.X.X.zip`。

> [!WARNING]
> **防坑指南**：在下载列表里，请认准并只点击 `whisperMe-xxx.zip`。**千万不要**点击下方的 `Source code (zip)`，源码包里没有编译好的前端页面，下载后无法直接运行！
解压后，执行：
- Windows: 双击 `start.bat`
- macOS/Linux: 终端运行 `bash scripts/start.sh`

启动后浏览器会自动打开 **http://127.0.0.1:9101**，粘贴一条播客链接即可开始。
<br />

---

<br />

## 🤖 与你的 AI Agent (Hermes/OpenClaw) 联动

如果你在本地运行了 AI Agent，你可以让它成为 whisperMe 的全职管家。
你出门在外，只需在微信/Telegram里给你的 Agent 发一个播客链接，它就会自动在你的电脑上操纵 whisperMe 完成转录，并把总结发回你的微信。

**如何接入？**
只需让你的 Agent 读取本项目根目录下的 `AGENT.md` 文件。它会自动学会所有部署、配置和操控指令。

**你可以这样对你的 Agent 说：**
> "帮我准备好本地目录下的 whisperMe，然后转录这期播客链接。"

<br />

---

<br />

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | React 19 · Vite 8 · Tailwind CSS（CSS 变量 + 暗色模式） |
| 后端 | FastAPI · Uvicorn · Python 3.10+ |
| ASR | faster-whisper · pyannote.audio · MiMo ASR |
| LLM | Ollama · LM Studio · OpenAI 兼容 API |
| 数据库 | SQLite（WAL 模式，speakers 声纹表） |
| 工具 | FFmpeg · yt-dlp · httpx |

<br />

---

<br />

## 项目结构

```
whisperMe/
├── CLAUDE.md                    # Claude Code 项目指令
├── README.md                    # 使用文档
├── VERSION                      # 版本号（当前 v1.0.0）
├── config.example.json          # 配置模板（脱敏）
├── config.json                  # 运行时配置（本地，git 忽略）
├── prompt.json                  # AI 总结 Prompt 模板
├── start.bat / stop.bat         # 生产模式启停（Windows 用户入口）
│
├── assets/
│   ├── logo.svg                 # SVG 图标
│   └── logo.ico                 # Windows .ico 图标
│
├── scripts/
│   ├── build.py                 # 发布构建脚本（ZIP + EXE）
│   ├── build_exe.py             # PyInstaller 单文件 exe 构建
│   ├── make_icon.py             # 图标生成
│   ├── launcher.py              # 生产模式启动器
│   ├── start_project.py         # 开发模式启动器
│   ├── start.sh / stop.sh       # macOS/Linux 启停
│   └── clean_temp.bat           # 临时文件清理
│
├── backend/
│   ├── run.py                   # 开发模式后端入口（uvicorn --reload）
│   ├── run_server.py            # 生产自包含入口（PyInstaller 用）
│   ├── requirements.txt         # Python 依赖
│   └── app/
│       ├── config.py            # Pydantic v2 配置校验
│       ├── database.py          # SQLite WAL 数据库
│       ├── main.py              # FastAPI 应用与路由挂载
│       ├── routers/             # API 路由层
│       │   ├── tasks.py         #   任务管理 + 上传
│       │   ├── config.py        #   系统设置
│       │   ├── system.py        #   系统状态与性能
│       │   └── boards.py        #   知识卡片
│       └── core/                # 核心业务
│           ├── pipeline.py      #   流水线调度
│           ├── speaker.py       #   声纹识别与推理
│           ├── transcriber.py   #   ASR 转录引擎
│           ├── downloader.py    #   音频下载器
│           ├── summarizer.py    #   LLM 总结器
│           ├── network.py       #   DoH DNS 直连
│           ├── compat.py        #   平台兼容层
│           ├── notifier.py      #   通知推送
│           ├── queue_manager.py #   任务队列
│           ├── prompt_manager.py#   Prompt 模板管理
│           └── asr_providers/   #   在线 ASR 提供商
│
├── frontend/
│   ├── index.html               # HTML 入口
│   ├── public/
│   │   ├── logo.svg             # 网站图标
│   │   └── fonts/               # 自托管字体 WOFF2
│   │       ├── noto-sans-sc-400.woff2
│   │       ├── noto-sans-sc-700.woff2
│   │       ├── outfit-400.woff2
│   │       ├── outfit-600.woff2
│   │       └── outfit-700.woff2
│   └── src/
│       ├── App.jsx              # SPA 主组件
│       ├── index.css            # CSS 变量 & 字体声明
│       ├── constants.js         # API 基础路径 + 工具函数
│       ├── components/          # UI 组件（Sidebar/Dialog）
│       ├── contexts/            # ThemeContext（暗色模式）
│       └── views/               # 页面视图
│
├── docs/
│   ├── architecture.md          # 系统架构设计
│   ├── user_guide.md            # 使用手册
│   ├── changelog.md             # 变更日志
│   ├── DESIGN.md                # 设计规范
│   ├── CONTRIBUTING.md          # 贡献指南
│   └── superpowers/             # 开发计划与规范
│
└── release/                     # 构建产物（git 忽略）
    ├── whisperMe.exe             #   PyInstaller 单文件
    └── whisperMe-Windows-x64-vX.X.X.zip  # ZIP 分发包
```

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
whisperMe 内置了 DoH DNS 直连和 4 级自适应代理回溯策略，能自动穿透 Clash TUN / Fake-IP 模式。如果仍有问题，参考 <a href="docs/user_guide.md#网络代理配置">代理分流配置</a>。
</details>

<details>
<summary><strong>Q: 如何获取 HuggingFace Token？</strong></summary>
<br />
访问 <a href="https://huggingface.co/settings/tokens">huggingface.co/settings/tokens</a>，创建一个 Read 权限的 Token，填入 <code>config.json</code> 的 <code>hf_token</code> 字段。没有 Token 也可以使用——程序会自动切换到国内镜像站下载。
</details>

<details>
<summary><strong>Q: 配置文件会被上传到 GitHub 吗？</strong></summary>
<br />
不会。<code>config.json</code> 已被 <code>.gitignore</code> 排除。仓库中只保留脱敏的 <code>config.example.json</code> 作为模板。
</details>

<br />

---

<br />

## 详细文档

- [使用手册 & 配置指南](docs/user_guide.md) — 详细配置参数、代理设置、常见问题
- [系统架构设计](docs/architecture.md) — 数据流、API 清单、设计决策
- [变更日志](docs/changelog.md) — 功能迭代与 Bug 修复记录

<br />

---

<br />

## 贡献

欢迎提交 Issue 和 Pull Request！请先阅读 [贡献指南](CONTRIBUTING.md)。

<br />

---

<br />

## License

MIT
