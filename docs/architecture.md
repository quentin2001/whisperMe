# whisperMe — 系统架构设计文档

> 最后更新：2026-07-03 · 深度代码审计后更新

---

## 1. 总体架构

whisperMe 采用经典的前后端分离 **SPA + REST API** 架构，部署于本地桌面环境（Windows）。系统集成了复杂的本地计算（ASR、LLM）与在线 API 回退机制。

```mermaid
graph TB
    subgraph Frontend ["🖥️ Frontend (Vite + React)"]
        A[App.jsx — 巨型 SPA 路由与全局状态枢纽]
        A2[contexts/ThemeContext — 暗色模式管理]
        B[views/ — 页面级业务视图 (Library, Workstation, Detail, Settings)]
        C[components/ — 独立组件 (Sidebar, Dialog)]
        D[index.css — CSS 变量 / 暗色主题 / 滚动条]
    end

    subgraph Backend ["⚙️ Backend (FastAPI + Uvicorn)"]
        E[main.py — App 挂载、Lifespan与后台任务分发]
        F[config.py — 全局配置与 BaseModel 校验 (热重载)]
        G[database.py — SQLite 并发 WAL 数据库 (God Class)]
        H[routers/ — 路由层 tasks/config/system/boards]
        I[core/pipeline.py — 流水线调度核心]
        J[core/speaker.py — 声纹匹配与智能推理]
        K[core/transcriber.py — ASR 识别引擎 (包含 VRAM 管理)]
        L[core/downloader.py — 音频下载器 (多平台解析)]
        M[core/summarizer.py — LLM 总结器]
        N[core/queue_manager.py — SQLite 任务队列管理器]
        O[mcp_server.py — AI Agent MCP 接口]
    end

    subgraph Storage ["💾 本地存储"]
        P[config.json — 全局配置文件]
        Q[whisperMe.db — SQLite 数据库（含 speakers 声纹表）]
        R[prompt.json — AI 总结 Prompt 模板]
        S[downloads/ & transcripts/ — 持久化文件]
    end

    A -->|HTTP REST / WS| H
    O -->|直接调用| G
    H --> G
    H --> N
    N --> I
    I --> G
    I --> L
    I --> K
    I --> M
    I --> J
```

---

## 2. 项目目录树

```text
whisperMe/
├── CLAUDE.md                    # Claude Code 项目指令
├── README.md                    # 使用文档
├── VERSION                      # 版本号
├── config.example.json          # 配置模板
├── prompt.json                  # AI 总结 Prompt 模板
├── start.bat / stop.bat         # 生产模式启停（Windows）
│
├── scripts/                     # 运维与打包脚本
│   ├── build.py / build_exe.py  # 发布与构建脚本
│   ├── launcher.py              # 生产模式后台启动器
│   ├── start_project.py         # 开发模式双开启动器
│   └── whisperme-cli.py         # CLI 工具 (6 个命令域，Agent 友好)
│
├── backend/
│   ├── run.py / run_server.py   # FastAPI 启动入口 (Dev/Prod)
│   └── app/
│       ├── config.py            # 全局配置校验与环境 Patch
│       ├── database.py          # SQLite 数据层控制 ( WAL )
│       ├── main.py              # FastAPI 主程序
│       ├── mcp_server.py        # MCP 协议服务端
│       ├── routers/             # API 路由层
│       │   ├── boards.py        # 知识卡片与对撞机
│       │   ├── config.py        # 系统设置与热更
│       │   ├── system.py        # 性能监控、版本、图片代理
│       │   └── tasks.py         # 核心任务管理、问答、导出
│       └── core/                # 核心业务
│           ├── downloader.py    # 播客/视频下载器 (多级回退)
│           ├── pipeline.py      # 流水线编排作业
│           ├── speaker.py       # 声纹与大模型推断
│           ├── transcriber.py   # 模型缓存与转录 (Whisper/在线)
│           ├── summarizer.py    # LLM 分析与内容生成
│           ├── network.py       # DoH 直连与代理穿透
│           ├── notifier.py      # 桌面/邮件/Webhook 推送
│           ├── queue_manager.py # DB驱动的任务队列
│           ├── llm_utils.py     # LLM 调用基建
│           └── asr_providers/   # 多种在线 ASR 厂商实现
│
└── frontend/
    ├── vite.config.js / tailwind.config.js
    └── src/
        ├── App.jsx              # SPA 核心与全局状态总线
        ├── data.js              # i18n 字典与 Theme 预设
        ├── index.css            # 设计令牌与全局样式
        ├── components/          # Sidebar, Dialog 等
        └── views/
            ├── LibraryView.jsx       # 播客库主视图 (含 Web Audio 玩具)
            ├── WorkstationView.jsx   # 沙盒知识视图
            ├── PodcastDetailView.jsx # 超大详情页 (音频、字幕、评论联动)
            └── SettingsView.jsx      # 系统级配置中心
```

---

## 3. 数据流与核心模块

### 3.1 核心数据流转 (Pipeline)
一条播客 URL 进入系统后的完整生命周期由 `core/pipeline.py` 的 `run_podcast_pipeline` 编排：
1. **下载阶段** (`downloader.py`)：通过 httpx / curl / yt-dlp 策略尝试下载，解析音频及 Shownotes。
2. **预处理**：FFmpeg 转换为 Mono 16kHz WAV。
3. **声纹分离** (`transcriber.py / speaker.py`)：使用 PyAnnote 生成声纹分段，提取声纹特征 (Embedding)。
4. **语音转录** (`transcriber.py`)：使用 Faster-Whisper 或在线 ASR 转录为文本。
5. **智能切分与匹配**：按段落聚合并通过 Cosine 相似度 + LLM 推理识别真实说话人身份。
6. **AI 分析总结** (`summarizer.py`)：构建庞大 Prompt 交由 Ollama / 在线大模型生成 Markdown 报告。
7. **触达通知** (`notifier.py`)：Windows 弹窗、邮件或 Webhook 推送。

### 3.2 任务队列调度 (Queue Manager)
- 基于 SQLite 持久化的 FIFO 队列。
- 后台守护线程轮询 `tasks` 表，支持断点恢复与并发数量限制 (`max_concurrent_tasks`)。

---

## 4. 核心 API/组件接口契约

系统在前端 SPA 和后端 FastAPI 之间采用 RESTful JSON 通信（WebSocket 仅用于实时性能数据）。

### 4.1 关键后端 API 契约
- `POST /api/tasks`：提交 URL 任务。参数 `{ "url": str, "asr_mode": str }`
- `GET /api/tasks/{task_id}`：获取完整转录、总结、分轨与元数据。
- `POST /api/tasks/{task_id}/qa`：基于当前播客超长文本的问答请求。
- `POST /api/upload`：本地音频直接上传建任务。
- `GET /api/proxy/image?url=xxx`：解决部分平台防盗链的代理中转。
- `POST /api/cards/create`：从字幕段落中沉淀知识卡片。

### 4.2 关键前端状态契约 (App.jsx)
由于未使用 Redux/Zustand，前端重度依赖 `App.jsx` 进行状态下发。核心 Props 契约包括：
- `activeTask` / `tasks`：当前选中的任务与全量列表。
- `configData`：系统的完整运行时配置。
- `t(zh, en)`：自研的轻量级 i18n 翻译函数。
- `audioPlayerRef`：全局共享的音频播放器控制柄，用于时间戳的跨组件跳转。

---

## 5. 关键设计决策 (原作者架构初衷)

> 💡 **架构师注：此部分完整保留了作者在项目设计之初的核心业务思想。**

| 决策 | 理由 |
|------|------|
| SQLite WAL + 线程隔离连接池 | 解决多线程读写下的 I/O 并发卡顿。通过 WAL 模式支持读写并行，去除读锁限制，提供秒级面板渲染，配合 30s `busy_timeout` 与外键级联确保数据一致性 |
| 延迟加载 (Lazy Loading) 机制 | 彻底重写 ASR 导入逻辑。在在线 ASR 模式下不载入 `torch` 等庞大依赖，实现零 AI 运行库的超轻量启动，利于 SaaS 低成本快速发布 |
| 显存常驻与 TTL 自动释放 | `ModelCacheManager` 单例缓存 WhisperModel 解决本地转录时重复加载模型的 I/O 痛点，支持超时自动释放 GPU 显存，对低配主机的多任务稳定性友好 |
| 8.3 短路径转换 | 规避 Windows 中文用户名或含有空格的路径导致的 C++ 底层库（FFmpeg/Faster-Whisper）报错 |
| HuggingFace 镜像自动切换 | 国内用户无需配置代理即可下载 PyAnnote/Embedding 模型 |
| 显存熔断降级 | GPU 内存不足时自动切换至 CPU 模式，避免 OOM 崩溃 |
| 单文件 SPA (App.jsx) | 减少组件间通信复杂度，适合快速迭代的个人项目 |
| SQLite 驱动持久化任务队列 | 将原有内存 FIFO 队列升级为数据库驱动，支持断电重启自动恢复续传，并引入全局 Pipeline 取消/中断路由与物理大文件清理机制 |
| 双模式 ASR/LLM | 支持纯离线和云端 API 两种模式，灵活适配不同场景 |
| DoH & 4级自适应抓取 | 规避本地 Clash TUN/Fake-IP 导致的 DNS 劫持与 SSL 连接阻线，实现 100% 网络自愈 |

---

## 6. 历史偏离说明 (代码审计补充)

经过 2026 年 7 月的全方位代码审计，发现当前代码实现与历史设计的偏离及隐患：

1. **SPA 复杂度的严重失控**：原设计“单文件 SPA (App.jsx) 减少组件间通信复杂度”，但在当前实现中，`App.jsx` 已膨胀为拥挤的“God Component”（近 700 行），且衍生出了极其庞大的子视图（如 `PodcastDetailView.jsx` 达 1650+ 行）。这种模式已严重影响性能（引发无节制的渲染瀑布）。
2. **前后端路由污染**：后端原本设计的模块化 `routers` 层，目前已被大量的业务逻辑（File I/O、LLM调用、数据库硬编码 SQL、甚至 Ebbinghaus 算法）严重污染，变成了典型的 Fat Controller，缺乏 Service 中间层。
3. **并发隐患与安全漏洞**：
   - 现有的图片代理 `/api/proxy/image` 缺乏域名白名单，存在严重的 SSRF 安全漏洞。
   - 网络穿透模块 `network.py` 中存在非线程安全的猴子补丁（全局覆盖 `socket.getaddrinfo`）。
   - `database.py` 已膨胀至千行级别的 God Class，缺乏 ORM 或 Repository 模式拆分。
4. **LLM 调用泛滥与重复**：至少有 4 处模块自行封装并硬编码了与大模型交互的网络层逻辑。

针对上述偏离与技术债，后续重构策略详见 `docs/refactor_plan.md`。
