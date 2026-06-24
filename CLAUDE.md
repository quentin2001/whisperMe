# whisperMe — AI 播客转录工作台

## 项目概述
本地优先的播客转录与知识提炼工具。粘贴播客链接 → 自动下载、转录、识别说话人、AI 总结。

## 技术栈
- **前端**: React 19 + Vite 8 + Tailwind CSS（CSS 变量 + 暗色模式）
- **后端**: FastAPI + Uvicorn + Python 3.10+
- **ASR**: faster-whisper / pyannote.audio / MiMo ASR（在线）
- **LLM**: Ollama（本地）/ OpenAI 兼容 API（在线）
- **数据库**: SQLite（WAL 模式，speakers 声纹表）
- **工具**: FFmpeg · yt-dlp · httpx

## 目录结构
```
backend/app/         # FastAPI 应用
  ├── routers/       # API 路由（tasks/config/system/boards）
  ├── core/          # 核心业务（pipeline/speaker/transcriber/summarizer/queue_manager）
  ├── config.py      # Pydantic v2 配置校验
  └── database.py    # SQLite WAL 数据库（含 speakers 表）
frontend/src/        # React SPA
  ├── App.jsx        # 主组件
  ├── contexts/      # ThemeContext（暗色模式管理）
  ├── views/         # 页面视图
  └── components/    # UI 组件（Sidebar/Topbar）
docs/                # 详细文档
```

## 核心功能清单（P0/P1 已完成）
| 功能 | 状态 | 说明 |
|------|------|------|
| SRT/VTT/Text/JSON 导出 | ✅ | `GET /api/tasks/{id}/transcript?format=srt` |
| 说话人系统（SQLite 声纹库） | ✅ | 动态阈值 + 合并/忘记 + 置信度显示 |
| 引用提取 | ✅ | Prompt 第 6 节：金句/书籍/影视/工具/人物 |
| 并行转录 | ✅ | 线程池 + CAS + GPU 显存自动检测 |
| 长播客分段总结 | ✅ | 自动分段 + 15 行重叠 + 合并 |
| 批量转录 | ✅ | `POST /api/tasks/batch`，最多 20 URL |
| 通知优化 | ✅ | 播客名+标题+时长，错误截断 80 字 |
| 暗色模式 | ✅ | ThemeContext + CSS 变量 + 全组件适配 |
| Prompt 模板系统 | ✅ | 单一 Prompt + `{{PODCAST_DATA}}` 占位符 + 预设模板（标准/简洁/深度） |

## 编码规范
- Python: 使用 Pydantic v2 做数据校验，标准 logging 替代 loguru
- React: 函数式组件，CSS 变量定义在 index.css `:root` 和 `.dark`
- 样式: Tailwind CSS `darkMode: "class"`，颜色用 `var(--xxx)` 而非硬编码 hex
- API: RESTful，路由按模块拆分到 routers/
- 配置: config.json（git 忽略），config.example.json（脱敏模板）

## 端口配置
- 后端: 8001（因 8000 被 Windows TCP 残留占用，重启后可改回）
- 前端: 5173（Vite dev server）
- 启动脚本: `一键启动.bat` → `start_project.py`

## 网络代理配置
开发环境使用 Clash Verge 代理，需分流：
- **直连（DIRECT）**: 小宇宙 FM、Bilibili、HuggingFace 镜像、ModelScope、小米 MiMo ASR
- **走代理**: Anthropic API、OpenAI API、GitHub
- 配置文件: `~/.config/clash-verge/profiles/rPXnhgo6q7d4.yaml`
- 详见 [使用手册](docs/user_guide.md#网络代理配置)

## 关键约束
- **禁止** 在 config.json 中硬编码 API Key
- **禁止** 顶部全局 import torch 等大库（按需延迟加载）
- **数据库只读不删**：没有明确主动指示，数据库内容只可读不可删
- 本地 ASR 模型支持显存常驻缓存 + TTL 自动释放
- 支持零外部 AI 依赖的在线模式极速启动
- **Prompt 系统**: 单一 Prompt 格式，使用 `{{PODCAST_DATA}}` 占位符。存储在 `backend/data/prompt.json`，默认值在 `prompt_manager.py`。预设模板：standard / concise / deep

## API 端点速览
```
GET    /api/tasks                        # 任务列表
POST   /api/tasks                        # 创建任务
POST   /api/tasks/batch                  # 批量创建（最多 20）
GET    /api/tasks/{id}                   # 任务详情
DELETE /api/tasks/{id}                   # 删除任务
GET    /api/tasks/{id}/transcript?format # 导出转录（srt/vtt/text/json）
GET    /api/tasks/speakers/list          # 说话人列表
POST   /api/tasks/speakers/merge         # 合并说话人
POST   /api/tasks/speakers/forget        # 忘记说话人
GET    /api/config                       # 系统配置
POST   /api/config                       # 保存配置
GET    /api/prompt                       # 获取 Prompt
POST   /api/prompt                       # 保存 Prompt
GET    /api/prompt/templates             # 列出预设模板
GET    /api/prompt/template/{id}         # 获取指定模板内容
GET    /api/performance                  # 性能监控
GET    /api/version/check                # 版本检查
POST   /api/upload                       # 上传音频
```

## 详细文档
- [系统架构](docs/architecture.md) — 数据流、API 清单、设计决策
- [使用手册](docs/user_guide.md) — 配置参数、常见问题
- [变更日志](docs/changelog.md) — 功能迭代记录
