<p align="center">
  <img src="./logo.svg" width="88" height="88" alt="whisperMe" />
</p>

<h1 align="center">whisperMe</h1>

<p align="center">
  本地优先的播客转录与知识提炼工作台
</p>

  粘贴一条播客链接 → 自动下载、转录、识别说话人、AI 总结

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

> **📸 截图建议**
>
> 如果你在为本项目准备截图，建议放在下方，按以下顺序各一张：
> 1. **播客库主页** — 展示任务卡片列表、实时进度状态
> 2. **转录详情页** — 展示对话流、说话人标签、AI 总结报告
> 3. **深色模式** — 展示主题切换效果
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
- **FFmpeg** — 通过 [WinGet](https://github.com/GyanD/codexffmpeg/releases) 或 [官网](https://ffmpeg.org/download.html) 安装---

<br />

## 配置与常见问题

详细的 `config.json` 配置文件参数说明（如 FFmpeg 路径、ASR 引擎及 LLM 密钥等配置项），以及代理连不上、HuggingFace Token 等常见问题，已整理至独立文档中：

👉 **[使用手册 & 配置指南 (User Guide)](docs/user_guide.md)**

<br />称 |

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

- [使用手册 & 配置指南](docs/user_guide.md) — 详细配置说明与常见问题解答
- [系统架构设计](docs/architecture.md) — 目录结构、API 清单、数据流、设计决策
- [变更日志](docs/changelog.md) — 功能迭代与 Bug 修复记录

<br />

---

<br />

## License

MIT
