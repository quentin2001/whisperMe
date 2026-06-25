# whisperMe — AI 播客转录工作台

## 项目概述
本地优先的播客转录与知识提炼工具。粘贴播客链接 → 自动下载、转录、识别说话人、AI 总结。

## 技术栈
- **前端**: React 19 + Vite 8 + Tailwind CSS v4（`@tailwindcss/vite` 编译打包，无 CDN 依赖）
- **后端**: FastAPI + Uvicorn + Python 3.10+
- **ASR**: MiMo ASR（在线）/ faster-whisper（本地，需 torch）
- **LLM**: Ollama（本地）/ OpenAI 兼容 API（在线）
- **数据库**: SQLite（WAL 模式，speakers 声纹表）
- **工具**: FFmpeg · yt-dlp · httpx
- **打包**: PyInstaller（单 exe）+ ZIP 分发包 → 双版本发布

## 目录结构
```
backend/app/         # FastAPI 应用
  ├── routers/       # API 路由（tasks/config/system/boards）
  ├── core/          # 核心业务（pipeline/speaker/transcriber/summarizer/downloader/
  │                  #   ffmpeg/llm_utils/network/compat/notifier/queue_manager/prompt_manager）
  │                  #   asr_providers/ 在线 ASR 提供商（mimo/openai/funasr/custom）
  ├── config.py      # Pydantic v2 配置校验 + 环境设置（UTF-8/NVIDIA DLL/HuggingFace 镜像）
  ├── database.py    # SQLite WAL 数据库（含 speakers 表 + update_task_field 轻量更新）
  └── run_server.py  # 自包含服务入口（PyInstaller 打包用）
frontend/src/        # React SPA
  ├── App.jsx        # 主组件
  ├── constants.js   # API_BASE + proxyImage 工具函数
  ├── contexts/      # ThemeContext（暗色模式管理）
  ├── views/         # 页面视图（Library/Workstation/PodcastDetail/Settings）
  └── components/    # UI 组件（Sidebar/Dialog）
frontend/public/     # 静态资源
  └── fonts/         # 本地字体 WOFF2（Noto Sans SC 400/700 + Outfit 400/600/700）
scripts/             # 构建与启动脚本
  ├── build.py       # 发布构建（前端编译 + ZIP 打包 + 可选 exe 构建）
  ├── build_exe.py   # PyInstaller 单文件 exe 编译
  ├── make_icon.py   # SVG → ICO 图标生成
  ├── launcher.py    # 生产模式启动器（品牌横幅 + 后台服务 + 浏览器自动打开）
  ├── start_project.py  # 开发模式启动（后端 + 前端前后进程）
  └── start.sh / stop.sh  # macOS/Linux 启停
assets/              # 图标资源
  ├── logo.svg       # SVG 矢量图标
  └── logo.ico       # Windows .ico 图标
docs/                # 详细文档（architecture/user_guide/changelog/DESIGN/CONTRIBUTING）
```

## 核心功能清单（P0/P1 已完成）
| 功能 | 状态 | 说明 |
|------|------|------|
| SRT/VTT/Text/MD/JSON 导出 | ✅ | `GET /api/tasks/{id}/transcript?format=srt` |
| 说话人系统（SQLite 声纹库） | ✅ | pyannote.audio（需本地模式+torch），动态阈值 + 合并/忘记 + 双级置信度 |
| 引用提取 | ✅ | Prompt 第 6 节：金句/书籍/影视/工具/人物 |
| 并行转录 | ✅ | 线程池 + CAS + GPU 显存自动检测 |
| 增量处理流水线 | ✅ | 音频即时播放 + 转录逐步显示 + AI 总结加载态 + update_task_field 轻量写入 |
| 长播客分段总结 | ✅ | 自动分段 + 15 行重叠 + 合并 |
| 批量转录 | ✅ | `POST /api/tasks/batch`，最多 20 URL |
| 失败任务重试 | ✅ | `POST /api/tasks/{id}/retry` + 前端重试按钮 + 网络错误提示 |
| 通知优化 | ✅ | 播客名+标题+时长，错误截断 80 字 |
| 暗色模式 | ✅ | ThemeContext + CSS 变量 + 全组件适配 |
| Prompt 模板系统 | ✅ | 单一 Prompt + `{{PODCAST_DATA}}` 占位符 + 预设模板（standard/concise/deep） |
| 图片代理 | ✅ | `GET /api/proxy/image` 代理 CDN 图片，解决浏览器直连不通问题 |
| 播客问答 | ✅ | `POST /api/tasks/{id}/qa` 基于转录文本的 LLM 问答 |
| MCP Server | ✅ | `/mcp` 端点，8 个工具 + 资源 + 提示词（需 `mcp` 包） |
| 在线模式 | ✅ | 零 torch 依赖启动包（~137MB），MiMo ASR + 在线 LLM |
| HF Token 验证 | ✅ | `GET /api/settings/hf-token-status` + 前端状态徽章 + 引导横幅 |
| GPU 自适应精度 | ✅ | compute_type 按显存自动选 float16/int8_float16/int8 |
| VAD 静音过滤 | ✅ | Silero VAD filter 跳过静音段推理 |
| MiMo 并发分片 | ✅ | ThreadPoolExecutor(max_workers=4) 并发 ASR 请求 |
| 代码去重 | ✅ | network.py（DoH DNS 直连）+ compat.py（Windows 子进程无窗口） |

## 编码规范
- Python: Pydantic v2 数据校验，标准 logging 替代 loguru
- React: 函数式组件，CSS 变量定义在 index.css `:root` 和 `.dark`
- 样式: Tailwind CSS v4（`@import "tailwindcss"` + `@theme` 块），颜色用 `var(--xxx)`
- **字体**: Noto Sans SC（中文）+ Outfit（英文），自托管 WOFF2，`@font-face` 声明，零外部请求
- API: RESTful，路由按模块拆分到 routers/
- 配置: config.json（git 忽略），config.example.json（脱敏模板）
- **前端网络**: 图片通过 `/api/proxy/image` 代理加载，`constants.js` 中的 `proxyImage()` 统一处理

## 端口配置
- 后端: 9101
- 前端: 9173（Vite dev server）
- 开发启动: `python scripts/start_project.py`（前后端双进程）
- 生产启动: 双击 `start.bat`（Windows）或运行 `scripts/start.sh`（macOS）
- 单文件启动: 双击 `release/whisperMe.exe`（PyInstaller 一键打包）
- 停止: `stop.bat` / `stop.sh` 或访问 `/api/shutdown`

## 三种启动路径
| 方式 | 入口 | 用户 | 前端 | 需要 Python |
|------|------|------|------|-------------|
| **开发** | `python scripts/start_project.py` | 开发者 | Vite dev (9173) | ✅ |
| **ZIP** | 双击 `start.bat` | 进阶用户 | FastAPI 托管 (9101) | ✅ |
| **EXE** | 双击 `whisperMe.exe` | 小白用户 | FastAPI 托管 (9101) | ❌ |

## 两种运行模式
| 模式 | 包大小 | torch | 声纹识别 | 适用场景 |
|------|--------|-------|----------|----------|
| **在线模式** | ~137MB | ❌ | ❌（需本地模式） | 新手、极速启动 |
| **本地模式** | ~5GB+ | ✅ | ✅ pyannote | 开发者、GPU 用户 |

在线模式使用 MiMo ASR + 在线 LLM，不需要 GPU。说话人识别依赖 pyannote.audio（需 torch），仅本地模式可用。

## RTX 3070 本地模式优化
- **compute_type**: 自动检测 GPU 总显存，4-10GB → `int8_float16`（甜点值），≥10GB → `float16`
- **默认模型**: `large-v3-turbo`（速度提升 ~6x vs large-v3）
- **VAD filter**: Silero VAD 跳过静音段，减少无效推理
- **WAV 预处理**: Whisper 直接读取 MP3，省去 WAV 转码步骤
- **CPU 线程**: cpu_threads=6, num_workers=1（CPU 模式）

## 网络代理配置
开发环境使用 Clash Verge 代理，需分流：
- **直连（DIRECT）**: 小宇宙 FM、Bilibili、HuggingFace 镜像、ModelScope、小米 MiMo ASR
- **走代理**: Anthropic API、OpenAI API、GitHub
- DoH DNS 直连模块: `backend/app/core/network.py`（绕过 Clash fake-IP 198.18.x.x）
- 详见 [使用手册](docs/user_guide.md#网络代理配置)

## 关键约束
- **禁止** 在 config.json 中硬编码 API Key
- **禁止** 顶部全局 import torch 等大库（按需延迟加载）
- **数据库只读不删**：没有明确主动指示，数据库内容只可读不可删
- 本地 ASR 模型支持显存常驻缓存 + TTL 自动释放
- 支持零外部 AI 依赖的在线模式极速启动
- **Prompt 系统**: 单一 Prompt 格式，使用 `{{PODCAST_DATA}}` 占位符。存储在项目根目录 `prompt.json`，默认值在 `prompt_manager.py`。预设模板：standard / concise / deep
- **Agent 接口**: CORS 已放通本地任意端口，未来 AI Agent 可通过 REST API 操控 whisperMe（`/docs` 查看 OpenAPI 文档）
- **环境变量**: 仅劫持 TEMP/TMP 到 temp_sandbox，不覆盖其他系统变量
- **版本管理**: `VERSION` 文件统一管理版本号，`config.py` 和 `build.py` 动态读取

## API 端点速览
```
GET    /api/tasks                        # 任务列表
POST   /api/tasks                        # 创建任务
POST   /api/tasks/batch                  # 批量创建（最多 20）
GET    /api/tasks/{id}                   # 任务详情
DELETE /api/tasks/{id}                   # 删除任务
POST   /api/tasks/{id}/retry             # 重试失败任务
POST   /api/tasks/{id}/cancel            # 取消任务
GET    /api/tasks/{id}/transcript?format # 导出转录（srt/vtt/text/json/markdown）
POST   /api/tasks/{id}/qa                # 播客问答（基于转录文本）
GET    /api/tasks/speakers/list          # 说话人列表
POST   /api/tasks/speakers/merge         # 合并说话人
POST   /api/tasks/speakers/forget        # 忘记说话人
GET    /api/config                       # 系统配置
POST   /api/config                       # 保存配置
GET    /api/settings/hf-token-status     # HF Token 验证状态
GET    /api/prompt                       # 获取 Prompt
POST   /api/prompt                       # 保存 Prompt
GET    /api/prompt/templates             # 列出预设模板
GET    /api/prompt/template/{id}         # 获取指定模板内容
GET    /api/performance                  # 性能监控
GET    /api/version/check                # 版本检查
GET    /api/proxy/image                  # 图片代理（解决 CDN 不可达）
POST   /api/upload                       # 上传音频
POST   /api/shutdown                     # 优雅关闭服务
```

## 详细文档
- [系统架构](docs/architecture.md) — 数据流、API 清单、设计决策
- [使用手册](docs/user_guide.md) — 配置参数、常见问题
- [变更日志](docs/changelog.md) — 功能迭代记录
- [设计规范](docs/DESIGN.md) — 视觉设计与交互规范
- [贡献指南](docs/CONTRIBUTING.md) — 参与贡献指南
