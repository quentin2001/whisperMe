<p align="center">
  <img src="./logo.svg" width="80" height="80" alt="whisperMe Logo" />
</p>

<h1 align="center">whisperMe</h1>

<p align="center">
  <strong>极简、私密的本地/云端混合式播客转录与 AI 知识提炼工作台</strong>
</p>

---

### 🌟 核心功能

* **📥 极速解析**：支持小宇宙 FM、Bilibili 下载与音视频自动分离。
* **🔄 混合转录**：无缝切换本地离线 Whisper 与高精在线 ASR API（如小米 MiMo ASR）。
* **👤 智能分轨**：基于 PyAnnote 自动进行声纹分段并结合 Shownotes 命名发言人。
* **🛡️ 显存熔断**：FIFO 后台任务排队，显存不足自动降级至 CPU 运行，杜绝 OOM。
* **🧠 认知沙盒**：一键沉淀段落、Anki 闪光卡片自动生成、艾宾浩斯复习与 AI 跨界碰撞。

---

### 🧭 工作流程

```mermaid
graph LR
    A[📥 1. 输入链接] --> B[⚙️ 2. 音频下载]
    B --> C[👤 3. 声纹分轨]
    C --> D[📝 4. AI 总结]
    D --> E[🎰 5. 认知沙盒]
    style A fill:#4F46E5,stroke:#312E81,color:#fff
    style B fill:#0D9488,stroke:#115E59,color:#fff
    style C fill:#0284C7,stroke:#075985,color:#fff
    style D fill:#7C3AED,stroke:#5B21B6,color:#fff
    style E fill:#DB2777,stroke:#9D174D,color:#fff
```

---

### 🚀 快速上手

#### 1. 启动后端 (Port 8000)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

#### 2. 启动前端 (Port 5173)
```bash
cd frontend
npm install
npm run dev
```

---

### ⚙️ 核心配置 (`config.json`)

复制 `config.example.json` 为 `config.json` 并按需修改：
- `ffmpeg_path`: 本地 FFmpeg 绝对路径
- `local_whisper_model_path`: 本地 Whisper 模型路径
- `hf_token`: Hugging Face 令牌（用于 PyAnnote 说话人识别）
- `ollama_url` / `ollama_model`: 本地 LLM 配置
- `asr_mode` / `summary_mode`: `local` (离线模型) 或 `online` (在线 API)
- `smtp_username` / `smtp_password`: SMTP 邮件提醒配置

