# whisperMe - Local Podcast Processor & AI Summary Generator

[English](#english) | [中文说明](#中文说明)

---

## English

`whisperMe` is a lightweight, local, and private podcast transcription and analysis workspace. It downloads podcast audio, standardizes the format, performs local speaker diarization (voice separation), transcribes speech-to-text (locally or online), automatically summarizes the content using LLMs (Ollama / LM Studio / OpenAI), and sends a beautifully styled HTML summary card directly to your inbox.

### 🌟 Key Features

1. **Strict Concurrency Resource Control**: Implements a sequential FIFO task queue (`TaskQueueManager`) to run tasks strictly one-by-one, preventing local workstations from freezing or crashing due to high CPU/GPU load.
2. **GPU VRAM Safety Safeguards**: Automatically monitors available VRAM (threshold: 1.5 GB). If VRAM is too tight (e.g., when running local LLMs), PyAnnote diarization and Whisper transcription automatically downgrade to CPU execution, preventing CUDA Out-Of-Memory (OOM) errors and WDDM memory page-swapping thrashing.
3. **Facts-Grounded "Anti-Hallucination" Prompts**: Summary prompts are strictly reinforced with negation guidelines and context constraints. The LLM summarizes based *only* on the actual dialog transcript and listener comments, completely avoiding hallucinations or brainstorming.
4. **Card-Style HTML Email Alerts**: Sends a premium, dark-themed HTML summary card to your SMTP email upon completion. Includes "Information Density" ratings (A+ to D), listener sentiment charts, core takeaways, and quotes.
5. **Smart Voiceprint matching & Speaker Renaming**:
   - PyAnnote speaker diarization maps speech segments.
   - Voice embeddings (512-d) are saved to a local voice database (`speaker_fingerprints.json`).
   - LLMs dynamically deduce host/guest names from conversation context.
   - Modifying a speaker's nickname updates the voice database, automatically renaming them in all future tasks.
6. **Automatic Interjection Filtering**: Identifies and labels speakers who only say short words (like "mm-hmm", "yes", "right") as "未识别语气词" (unidentified filler words).

### 🛠️ Architecture & Stack

* **Backend**: FastAPI (Python 3.10+) + PyTorch + faster-whisper + pyannote.audio + SMTP
* **Frontend**: React + Vite + Tailwind/Vanilla CSS
* **Storage**: Lightweight local JSON databases (`tasks_db.json`, `speaker_fingerprints.json`)
* **Deduction Engine**: Local LLM (Ollama / LM Studio) or OpenAI-compatible API

---

## 中文说明

`whisperMe` 是一个轻量级、本地化且高度重视隐私的播客转录与知识提取工作台。它可以一键下载播客单集音频，标准化音频格式，运行本地声纹角色分割（Diarization），进行语音识别转文字，调用大模型（本地 Ollama / LM Studio 或在线 API）生成摘要报告，最后自动将精美暗黑卡片风格的 HTML 总结卡片发送至您的邮箱。

### 🌟 核心特性

1. **严格的硬件资源控制**：引入后台串行 FIFO 任务队列（`TaskQueueManager`），任务排队严格单线程顺序运行，保护本地电脑硬件不因超负荷而死机。
2. **动态显存可用性熔断**：在执行声纹分割与本地 Whisper 前，自动监控 GPU 可用显存（阈值 1.5 GB）。若显存不足（例如本地正在运行大模型），自动熔断并降级至 CPU 运行，杜绝 CUDA 显存溢出（OOM）或 Windows WDDM 共享显存页置换引起的系统极度卡顿。
3. **防幻觉事实锚定提示词**：提炼提示词内置严格的 Grounding 防伪防脑补规则，禁止大模型利用固有知识发散，所有结论必须 100% 且仅基于转录本及听众真实评论。
4. **精美暗黑卡片邮件提醒**：任务成功后通过 SMTP 发送精美的暗黑卡片风格 HTML 邮件。包含播客含金量评级（A+ ~ D 级）、适合人群、核心主旨、核心议题提炼以及精选金句等。
5. **智能声纹库与上下文改名**：
   - 提取发言人的 512 维特征向量，持久化至本地声纹特征库（`speaker_fingerprints.json`）。
   - 结合 Shownotes 与转录文本，由大模型智能推理发言人真实姓名。
   - 手动修改昵称后自动绑定声纹，未来遇到相同声纹时自动匹配为该姓名。
6. **无意义语气词自动标记**：全自动识别在整期播客中仅说短语、语气词（如“嗯”、“对”、“好的”）的边缘发言人，并自动标记为“未识别语气词”。

### 🛠️ 技术栈与架构

* **后端 (Backend)**: FastAPI (Python 3.10+) + PyTorch + faster-whisper + pyannote.audio + SMTP 邮件客户端
* **前端 (Frontend)**: React + Vite + 精美 Vanilla/Vanilla CSS
* **数据存储**: 轻量级本地 JSON 数据库，完全离线
* **大模型引擎**: 本地 Ollama / LM Studio 或 OpenAI 兼容在线接口

---

## 🚀 Installation & Setup / 快速开始

### 1. Clone & Setup Config
Copy `config.example.json` to `config.json` in the project root, and fill in your local configurations:
```bash
cp config.example.json config.json
```
*Make sure to configure your `ffmpeg_path`, `hf_token` (Hugging Face token for PyAnnote models), and email SMTP parameters if you want email cards.*

### 2. Start Backend
Ensure Python 3.10+ is installed:
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate # Linux/Mac

pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Start Frontend
Ensure NodeJS is installed:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` to start using your private podcast assistant!
