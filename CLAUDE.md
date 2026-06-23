# whisperMe — AI 播客转录工作台

## 项目概述
本地优先的播客转录与知识提炼工具。粘贴播客链接 → 自动下载、转录、识别说话人、AI 总结。

## 技术栈
- **前端**: React 19 + Vite 8 + Vanilla CSS（设计令牌）
- **后端**: FastAPI + Uvicorn + Python 3.10+
- **ASR**: faster-whisper / pyannote.audio / MiMo ASR（在线）
- **LLM**: Ollama（本地）/ OpenAI 兼容 API（在线）
- **数据库**: SQLite（WAL 模式）
- **工具**: FFmpeg · yt-dlp · httpx

## 目录结构
```
backend/app/         # FastAPI 应用
  ├── routers/       # API 路由（tasks/config/system/boards）
  ├── core/          # 核心业务（pipeline/speaker/transcriber/summarizer）
  ├── config.py      # Pydantic v2 配置校验
  └── database.py    # SQLite WAL 数据库
frontend/src/        # React SPA
  ├── App.jsx        # 主组件
  ├── views/         # 页面视图
  └── components/    # UI 组件
docs/                # 详细文档
```

## 编码规范
- Python: 使用 Pydantic v2 做数据校验，标准 logging 替代 loguru
- React: 函数式组件，CSS 设计令牌定义在 index.css
- API: RESTful，响应格式 `{code, data, message}`
- 配置: config.json（git 忽略），config.example.json（脱敏模板）

## 网络代理配置
开发环境使用 Clash Verge 代理，需分流：
- **直连（DIRECT）**: 小宇宙 FM、Bilibili、HuggingFace 镜像、ModelScope、小米 MiMo ASR
- **走代理**: Anthropic API、OpenAI API、GitHub
- 配置文件: `~/.config/clash-verge/profiles/rPXnhgo6q7d4.yaml`
- 详见 [使用手册](docs/user_guide.md#网络代理配置)

## 关键约束
- **禁止** 在 config.json 中硬编码 API Key
- **禁止** 顶部全局 import torch 等大库（按需延迟加载）
- 本地 ASR 模型支持显存常驻缓存 + TTL 自动释放
- 支持零外部 AI 依赖的在线模式极速启动

## 详细文档
- [系统架构](docs/architecture.md) — 数据流、API 清单、设计决策
- [使用手册](docs/user_guide.md) — 配置参数、常见问题
- [变更日志](docs/changelog.md) — 功能迭代记录
