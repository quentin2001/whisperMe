<p align="center">
  <img src="./logo.svg" width="120" height="120" alt="whisperMe Logo" />
</p>

<h1 align="center">whisperMe</h1>

<p align="center">
  <strong>一款专为播客爱好者与知识整理控量身打造的本地化、私密化播客转录与 AI 知识提炼工作台</strong>
</p>

**whisperMe** 支持一键抓取主流播客平台（如小宇宙 FM、Bilibili、本地音频等），智能提取声纹角色，将长语音精准识别为时间轴剧本，并调用大模型（本地 LLM / 在线 API）生成深度 Grounded 的暗黑卡片风格总结，最终自动通过邮件推送至您的收件箱。


---

### 1. 项目简介与核心功能 (Project Overview & Features)

#### 💡 一句话简介
> 解决本地计算资源受限下的并发堵塞与显存崩盘，实现一键自动化、安全无幻觉的播客声纹转录与卡片式知识提炼。

#### 🌟 核心功能列表
* **📥 播客解析与直链高速下载**：支持小宇宙 FM、Bilibili 原生解析，通过私有 API 提取媒体直链，自动调用 FFmpeg 极速分离音视频并流式输出 MP3，绕过反爬机制与流量限制。
* **🔄 本地与云端双模式切换 (Local & Online)**：
  * **完全本地**：本地 Whisper 转录 + Ollama/LM Studio 离线大模型总结，100% 数据隐私安全。
  * **云端模式**：在线转写（如小米 MiMo ASR）+ OpenAI 兼容大模型（如 MiMo-v2.5 等 1M 长文本模型）。支持本地/云端交叉混合搭配。
* **🛡️ 串行队列约束与显存熔断保护**：
  * 后台 FIFO 单线程排队，杜绝多任务并发导致的 CPU/GPU 过载卡死。
  * 物理显存监控熔断（安全阈值 1.5 GB），不足时声纹分割与本地识别自动降级至 CPU 运行，规避 OOM 崩溃。
* **👤 智能声纹库与发言人自动推定**：
  * 提取 192/512 维声纹特征向量持久化至本地库，新播客可自动匹配历史录入的声音。
  * 结合 Shownotes 上下文大模型推断发言人姓名，自动识别过滤只说“嗯/对/好”的语气词边缘人。
* **🎨 自适应 Tokyo Night 风格 UI**：支持自适应深浅外观（Dark/Light）。浅色模式采用全新的 Primary/Accent 二级主色与 HSL 自适应对比度，消除了浅色下白字模糊与背景黏连的痛点。
* **✉️ 专属配色 SMTP 卡片邮件推送**：任务完成后自动发送格式精美的卡片 HTML 总结邮件（支持等级评级、核心议题提炼、收听建议、金句引用等模块），自适应各类手机和 PC 客户端。

---

### 2. 视觉直观展示 (Showcase / Quick Demo)

#### 🧭 极简用户使用流程 (How It Works)

无需理解复杂的底层显存调度与声纹算法，您只需体验以下简单的一键式处理旅程：

```mermaid
graph TD
    A["📥 1. 输入链接 (小宇宙/B站/本地音频)"] -->|"后台串行排队防卡死"| B["⚙️ 2. 音频下载与格式标准化"]
    B -->|"智能显存安全熔断"| C["👤 3. 声纹分段与发言人自动识别"]
    C -->|"去粗取精/自动过滤语气助词"| D["🧠 4. AI 事实一致性提炼总结"]
    D -->|"任务完成自动发信"| E["📬 5. 收件箱即时接收卡片式报告"]

    style A fill:#4F46E5,stroke:#312E81,stroke-width:2px,color:#fff
    style B fill:#0D9488,stroke:#115E59,stroke-width:2px,color:#fff
    style C fill:#0284C7,stroke:#075985,stroke-width:2px,color:#fff
    style D fill:#7C3AED,stroke:#5B21B6,stroke-width:2px,color:#fff
    style E fill:#DB2777,stroke:#9D174D,stroke-width:2px,color:#fff
```
---

### 3. 快速上手指南 (Quick Start)

让您在 3 分钟内本地跑通 whisperMe 的全链路转录流程。

#### 💻 环境要求 与 平台兼容性 (Platform Compatibility)

* **🖥️ 操作系统支持**:
  * **Windows 10/11**: 完美支持。完整启用 NVIDIA CUDA GPU 硬件加速，支持独创的“1.5 GB 显存安全熔断与降级机制”以防显存溢出 (OOM)。
  * **macOS (Intel / Apple Silicon M系列芯片)**: 完美支持。后端自动规避短路径转换，并在显卡检测上做安全降级适配（声纹分割与 Whisper 均平稳运行在多线程 CPU 模式或 MPS 模式下，完美适配 M 芯片的统一内存架构）。
* **🔌 基础依赖**:
  * **后端 (Backend)**: Python >= 3.10
  * **音频预处理**: FFmpeg (Windows 请在 `config.json` 指定 `.exe` 物理绝对路径；macOS 建议通过 `brew install ffmpeg` 安装并将 `ffmpeg_path` 设为 `"ffmpeg"`)
  * **前端 (Frontend)**: Node.js >= 18, npm

#### 📥 克隆与安装

```bash
# 1. 克隆仓库
git clone https://github.com/quentin2001/whisperMe.git
cd whisperMe

# 2. 安装后端 Python 依赖
cd backend
python -m venv venv
venv\Scripts\activate  # Windows 激活虚拟环境
# source venv/bin/activate  # Linux/Mac 激活虚拟环境
pip install -r requirements.txt

# 3. 安装前端 Node 依赖
cd ../frontend
npm install
```

#### 🚀 启动项目

请确保您的本地大模型服务（如 Ollama 或 LM Studio）已正常启动，然后在不同的终端窗口中分别运行后端与前端服务：

* **启动后端 API 服务 (端口 8000)**:
  ```bash
  cd backend
  venv\Scripts\activate
  python run.py
  ```
* **启动前端 Web 工作台 (端口 5173)**:
  ```bash
  cd frontend
  npm run dev
  ```
启动后在浏览器中打开 `http://localhost:5173` 即可开始使用。

---

### 4. 配置与环境变量说明 (Configuration)

请将项目根目录下的 `config.example.json` 复制并重命名为 `config.json`，然后根据本地实际路径和参数进行配置：

| 配置项 / 变量名 | 类型 | 是否必填 | 默认值 | 作用描述 |
| :--- | :--- | :--- | :--- | :--- |
| `ffmpeg_path` | String | 是 | - | 本地 FFmpeg.exe 的物理绝对路径 |
| `ffmpeg_bin_dir` | String | 是 | - | FFmpeg bin 目录绝对路径 |
| `local_whisper_model_path` | String | 是 | - | 本地下载好的 Whisper 模型存放绝对路径 |
| `hf_token` | String | 否 | `""` | Hugging Face 授权 Token，用于自动加载 PyAnnote 声纹管道（若无则降级为纯 ASR） |
| `ollama_url` | String | 否 | `http://localhost:11434` | 本地 LLM（Ollama / LM Studio）接口根地址 |
| `ollama_model` | String | 否 | `qwen2.5:7b-instruct` | 本地总结模型代号 |
| `smtp_server` | String | 否 | `smtp.qq.com` | 发送总结邮件的 SMTP 服务器地址 |
| `smtp_port` | Number | 否 | `465` | SMTP 发送端口 |
| `smtp_username` | String | 否 | `""` | 用于发送邮件的邮箱账号 |
| `smtp_password` | String | 否 | `""` | 发送邮箱的 SMTP 客户端授权密码 |
| `smtp_sender` | String | 否 | `""` | 邮件发件人显示邮箱 |
| `notification_email` | String | 否 | `""` | 接收卡片式总结报告的电子邮箱 |
| `enable_win_notification` | Boolean | 否 | `true` | 是否启用 Windows 桌面气泡通知 |
| `asr_mode` | String | 否 | `local` | 语音转录引擎模式：`local` (本地大模型) / `online` (在线 API) |
| `online_api_key` | String | 否 | `""` | 在线 ASR API 授权 Key |
| `online_base_url` | String | 否 | `https://token-plan-sgp.xiaomimimo.com/v1` | 在线 ASR API 基准地址 |
| `online_model` | String | 否 | `mimo-v2.5-asr` | 在线 ASR 语音模型标识 |
| `summary_mode` | String | 否 | `local` | 总结报告引擎模式：`local` (本地 Ollama/LM Studio) / `online` (在线 API) |
| `online_summary_api_key` | String | 否 | `""` | 在线 LLM 总结 API 授权 Key |
| `online_summary_base_url` | String | 否 | `https://api.openai.com/v1` | 在线 LLM 总结 API 代理地址 |
| `online_summary_model` | String | 否 | `gpt-4o-mini` | 在线 LLM 总结模型标识 |

---

### 5. 核心工作流与架构设计 (Workflow & Architecture)

以下为 `whisperMe` 全链路处理流程的数据流向和生命周期图示：

```mermaid
graph TD
    A["用户输入播客 URL"] --> B["FastAPI 接口层 /api/tasks"]
    B --> C["任务序列化写入 tasks_db.json"]
    C --> D["TaskQueueManager 后台排队线程"]
    D -->|"串行取出"| E["Downloader 抓取模块"]
    E -->|"1. curl / 移动端网页私有 API 高速下载"| F["音频及元数据下载完成"]
    F -->|"2. FFmpeg 预处理"| G["16kHz 单声道 WAV"]
    G --> H["Transcriber 转录模块"]
    H -->|"3. 监控 VRAM"| I{"剩余 VRAM < 1.5GB?"}
    I -->|"是"| J["自动熔断: 降级到 CPU 运行"]
    I -->|"否"| K["运行 CUDA 加速声纹分割"]
    J --> L["PyAnnote 声纹角色切分"]
    K --> L
    L --> M{"ASR 识别模式"}
    M -->|"local"| N["本地 Whisper 引擎识别"]
    M -->|"online"| O["压缩分片并发送 Mimo ASR API"]
    N --> P["交叉合并文本时间轴与声纹角色"]
    O --> P
    P -->|"过滤无意义短词"| Q["自动标记语气词发言人"]
    Q --> R["Summarizer 总结模块"]
    R -->|"大模型事实总结"| S["生成 Grounded 总结报告"]
    S --> T["Notifier 提醒模块"]
    T -->|"发送桌面通知"| U["任务完成状态变更并持久化"]
    T -->|"SMTP 发送 HTML 邮件"| U
    U --> V["前端 React 工作台渲染展示"]
```
