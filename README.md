<p align="center">
  <img src="./logo.svg" width="88" height="88" alt="whisperMe" />
</p>

<h1 align="center">whisperMe</h1>

<p align="center">
  本地优先的播客转录与知识提炼工作台
</p>

<p align="center">
  粘贴一条播客链接 → 自动下载、转录、识别说话人、AI 总结 → 沉淀为可复习的知识卡片
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
- **认知沙盒** — 把精彩段落沉淀为 Anki 闪光卡片，内置艾宾浩斯复习算法、3D 老虎机随机抽卡、AI 碰撞器发现跨播客知识关联

<br />

> **📸 截图建议**
>
> 如果你在为本项目准备截图，建议放在下方，按以下顺序各一张：
> 1. **播客库主页** — 展示任务卡片列表、实时进度状态
> 2. **转录详情页** — 展示对话流、说话人标签、AI 总结报告
> 3. **认知沙盒** — 展示 3D 老虎机或 AI 碰撞器界面
> 4. **深色模式** — 展示主题切换效果
>
> 截图放置在 `docs/screenshots/` 目录下，用 `![播客库](./docs/screenshots/dashboard.png)` 嵌入。

<br />

---

<br />

## 核心能力

| 能力 | 说明 |
|---|---|
| 🔄 双模式 ASR | 本地 `faster-whisper`（GPU/CPU 自动切换）或在线 API，按需选择 |
| 👤 智能声纹与身份推理 | PyAnnote 声纹分段 + 基于上下文的四阶段 LLM 身份推断机制（支持常驻主播缺席场景） |
| ⏱️ 全链路耗时统计 | 自动生成包含下载、分轨、识别、推断至分析完毕的精准阶段耗时报表 |
| 🧠 认知沙盒 | Anki 卡片 × 艾宾浩斯间隔 × 3D 老虎机 × AI 碰撞器 |
| 🛡️ 显存熔断 | GPU 内存不足时自动降级至 CPU，杜绝 OOM 崩溃 |
| 🌐 网络自愈 | 内置 DoH DNS 直连 + 4 级自适应代理回溯，穿透 Clash TUN/Fake-IP 劫持 |
| 🌍 四语言 UI | 简体中文 / 繁體中文 / English / 日本語 |
| 🎨 主题引擎 | 浅色 / 深色 / 跟随系统，多套预设配色 + 自定义色彩 |
| 📬 完成通知 | Windows 桌面气泡 + SMTP 邮件，可独立开关 |

<br />

---

<br />

## 快速开始

### 前置要求

- **Python 3.10+**
- **Node.js 18+**
- **FFmpeg** — 通过 [WinGet](https://github.com/GyanD/codexffmpeg/releases) 或 [官网](https://ffmpeg.org/download.html) 安装
- **GPU（可选）** — 有 NVIDIA 显卡可加速转录，没有也能跑（自动降级 CPU）

### 1. 克隆项目

```bash
git clone https://github.com/quentin2001/whisperMe.git
cd whisperMe
```

### 2. 配置

```bash
cp config.example.json config.json
```

打开 `config.json`，填入你的本地路径和密钥。详见下方 [配置说明](#配置说明)。

### 3. 安装后端依赖并启动

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python run.py
```

后端启动于 `http://127.0.0.1:8000`。

### 4. 安装前端依赖并启动

```bash
cd frontend
npm install
npm run dev
```

前端启动于 `http://localhost:5173`，在浏览器中打开即可使用。

### 5. 一键启动（可选）

项目根目录下提供了 `start_project.py` 一键启动脚本，双击 `一键启动.bat` 即可同时拉起前后端，按 `Ctrl+C` 统一关闭。日志自动保存在 `logs/` 目录。

<br />

---

<br />

## 工作流程

```
粘贴链接 / 上传音频  →  自动下载  →  声纹分轨 + 转录  →  AI 总结  →  认知沙盒
```

```mermaid
graph LR
    A["📥 输入链接"] --> B["⚙️ 音频下载"]
    B --> C["👤 声纹分轨"]
    C --> D["📝 AI 总结"]
    D --> E["🎰 认知沙盒"]
    style A fill:#4F46E5,stroke:#312E81,color:#fff
    style B fill:#0D9488,stroke:#115E59,color:#fff
    style C fill:#0284C7,stroke:#075985,color:#fff
    style D fill:#7C3AED,stroke:#5B21B6,color:#fff
    style E fill:#DB2777,stroke:#9D174D,color:#fff
```

整条管线全自动异步执行（FIFO 队列），你可以同时提交多个任务，它们会依次排队处理。处理完成后会通过 Windows 桌面通知或邮件提醒你。

<br />

---

<br />

## 配置说明

配置文件为项目根目录下的 `config.json`（已被 `.gitignore` 排除，不会上传到仓库）。

首次使用请复制模板：

```bash
cp config.example.json config.json
```

### 必填项

| 配置项 | 说明 |
|---|---|
| `ffmpeg_path` | FFmpeg 可执行文件的绝对路径（`.exe`） |
| `ffmpeg_bin_dir` | FFmpeg `bin` 目录的绝对路径 |

### ASR 语音转录

| 配置项 | 说明 |
|---|---|
| `asr_mode` | `local`（离线）或 `online`（在线 API） |
| `local_whisper_model_path` | 本地 Whisper 模型目录路径（`asr_mode=local` 时必填） |
| `hf_token` | HuggingFace Token，用于下载 PyAnnote 声纹模型 |
| `online_api_key` | 在线 ASR API Key（`asr_mode=online` 时必填） |
| `online_base_url` | 在线 ASR API 地址，默认 MiMo ASR |
| `online_model` | 在线 ASR 模型名称 |

### AI 总结

| 配置项 | 说明 |
|---|---|
| `summary_mode` | `local`（本地 Ollama）或 `online`（在线 LLM API） |
| `ollama_url` | Ollama 服务地址，默认 `http://localhost:11434` |
| `ollama_model` | 本地模型名称，默认 `qwen2.5:7b-instruct` |
| `online_summary_api_key` | 在线 LLM API Key（`summary_mode=online` 时必填） |
| `online_summary_base_url` | 在线 LLM API 地址，默认 OpenAI |
| `online_summary_model` | 在线 LLM 模型名称，默认 `gpt-4o-mini` |

### 通知

| 配置项 | 说明 |
|---|---|
| `enable_win_notification` | Windows 桌面通知开关，默认 `true` |
| `enable_email_notification` | 邮件通知开关，默认 `false` |
| `smtp_server` / `smtp_port` | SMTP 服务器及端口 |
| `smtp_username` / `smtp_password` | SMTP 登录凭据 |
| `smtp_sender` / `notification_email` | 发件人 / 收件人地址 |

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
<summary><strong>Q: 开了代理软件（Clash / V2Ray）后在线 API 连不上？</strong></summary>
<br />
whisperMe 内置了 DoH DNS 直连机制和 4 级自适应代理回溯策略，能自动穿透 Clash TUN / Fake-IP 模式下的 DNS 劫持和 SSL EOF 报错。如果仍有问题，请检查代理软件的规则配置。
</details>

<details>
<summary><strong>Q: 如何获取 HuggingFace Token？</strong></summary>
<br />
访问 <a href="https://huggingface.co/settings/tokens">huggingface.co/settings/tokens</a>，创建一个 Read 权限的 Token，填入 <code>config.json</code> 的 <code>hf_token</code> 字段。该 Token 用于下载 PyAnnote 声纹识别模型。没有 Token 也可以使用——程序会自动切换到国内镜像站下载。
</details>

<details>
<summary><strong>Q: 配置文件会被上传到 GitHub 吗？</strong></summary>
<br />
不会。<code>config.json</code> 已被 <code>.gitignore</code> 排除，你的 API Key、密码等敏感信息不会进入版本控制。仓库中只保留脱敏的 <code>config.example.json</code> 作为模板。
</details>

<br />

---

<br />

## 项目结构

```
whisperMe/
├── config.example.json         # 配置模板（脱敏）
├── config.json                 # 运行时配置（本地，git 忽略）
├── prompt.json                 # AI 总结 Prompt 模板
├── start_project.py            # 一键启动脚本
├── 一键启动.bat                 # Windows 双击启动入口
│
├── backend/
│   ├── run.py                  # 后端入口
│   ├── requirements.txt        # Python 依赖
│   └── app/
│       ├── config.py           # 全局配置 & 环境防御层
│       ├── database.py         # JSON 文件数据库
│       ├── main.py             # FastAPI 路由 & 业务逻辑
│       └── core/
│           ├── downloader.py   # 小宇宙 / Bilibili 下载器
│           ├── transcriber.py  # Whisper / MiMo ASR 转录器
│           ├── summarizer.py   # Ollama / 在线 LLM 总结器
│           ├── notifier.py     # 通知推送（桌面 + 邮件）
│           ├── queue_manager.py    # FIFO 任务队列
│           └── prompt_manager.py   # Prompt 模板管理
│
├── frontend/
│   └── src/
│       ├── App.jsx             # SPA 主组件
│       ├── SlotMachineModal.jsx    # 认知沙盒 · 3D 老虎机
│       ├── AiColliderModal.jsx     # AI 碰撞器
│       ├── index.css           # 设计令牌 & 全局样式
│       └── ...
│
└── docs/
    ├── architecture.md         # 系统架构设计文档
    └── changelog.md            # 变更日志
```

<br />

---

<br />

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | React 19 · Vite 8 · Vanilla CSS（设计令牌） |
| 后端 | FastAPI · Uvicorn · Python 3.10+ |
| ASR | faster-whisper · pyannote.audio · MiMo ASR |
| LLM | Ollama · LM Studio · OpenAI 兼容 API |
| 工具 | FFmpeg · yt-dlp · httpx |

<br />

---

<br />

## 详细文档

- [系统架构设计](docs/architecture.md) — 目录结构、API 清单、数据流、设计决策
- [变更日志](docs/changelog.md) — 功能迭代与 Bug 修复记录

<br />

---

<br />

## License

MIT
