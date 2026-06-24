<p align="center">
  <img src="./logo.svg" width="88" height="88" alt="whisperMe" />
</p>

<h1 align="center">whisperMe</h1>

<p align="center">
  本地优先的播客转录与知识提炼工作台
</p>

<p align="center">
  粘贴一条播客链接 → 自动下载、转录、识别说话人、AI 总结
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
| `ffmpeg_path` | ✅ | FFmpeg 可执行文件的绝对路径 |
| `ffmpeg_bin_dir` | ✅ | FFmpeg `bin` 目录的绝对路径 |
| `asr_mode` | — | `local`（离线 Whisper）或 `online`（在线 API，默认） |
| `summary_mode` | — | `local`（本地 Ollama）或 `online`（在线 LLM，默认） |
| `online_api_key` | 仅在线 ASR | 在线语音识别 API Key |
| `online_summary_api_key` | 仅在线 LLM | 在线大模型 API Key |

> 完整配置说明见 [使用手册](docs/user_guide.md)。

### 4. 启动

**方式一：一键启动（Windows）**

双击 `一键启动.bat`，自动拉起前后端服务。

**方式二：手动启动**

```bash
# 终端 1 — 后端（端口 9101）
cd backend
python run.py

# 终端 2 — 前端（端口 9173）
cd frontend
npm run dev
```

启动后浏览器打开 **http://localhost:9173**，粘贴一条播客链接即可开始。

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
├── config.example.json         # 配置模板（脱敏）
├── config.json                 # 运行时配置（本地，git 忽略）
├── start_project.py            # 一键启动脚本
├── 一键启动.bat                 # Windows 双击启动入口
│
├── backend/
│   ├── run.py                  # 后端入口
│   ├── requirements.txt        # Python 依赖
│   └── app/
│       ├── config.py           # Pydantic v2 配置校验
│       ├── database.py         # SQLite WAL 数据库
│       ├── main.py             # FastAPI 路由挂载
│       ├── routers/            # API 路由层
│       │   ├── tasks.py        #   任务管理
│       │   ├── config.py       #   系统设置
│       │   ├── system.py       #   系统状态
│       │   └── boards.py       #   知识卡片
│       └── core/               # 核心业务
│           ├── pipeline.py     #   流水线调度
│           ├── speaker.py      #   声纹识别与推理
│           ├── transcriber.py  #   ASR 转录引擎
│           ├── downloader.py   #   音频下载器
│           ├── summarizer.py   #   LLM 总结器
│           ├── notifier.py     #   通知推送
│           ├── queue_manager.py#   任务队列
│           └── prompt_manager.py#  Prompt 模板
│
├── frontend/
│   └── src/
│       ├── App.jsx             # SPA 主组件
│       ├── index.css           # CSS 变量 & 全局样式
│       ├── components/         # UI 组件（Sidebar/Topbar/Dialog）
│       ├── contexts/           # ThemeContext（暗色模式）
│       └── views/              # 页面视图
│
└── docs/
    ├── architecture.md         # 系统架构设计
    ├── user_guide.md           # 使用手册 & 配置指南
    └── changelog.md            # 变更日志
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
