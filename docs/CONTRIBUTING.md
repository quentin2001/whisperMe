# 贡献指南 (Contributing Guide)

感谢你对 whisperMe 的关注！以下是参与贡献的方式。

---

## 报告问题

使用 [GitHub Issues](../../issues) 提交 Bug 报告或功能建议，请包含：

- **环境信息**：操作系统、Python 版本、Node.js 版本、GPU 型号（如有）
- **复现步骤**：尽可能详细的步骤描述
- **期望 vs 实际行为**
- **日志输出**：如有报错，请附上 `logs/` 目录下的相关日志

---

## 开发环境搭建

### 前置要求

- Python 3.10+
- Node.js 18+
- FFmpeg
- Git

### 步骤

```bash
# 1. Fork 并克隆
git clone https://github.com/your-username/whisperMe.git
cd whisperMe

# 2. 后端
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
pip install -r requirements.txt
cd ..

# 3. 前端
cd frontend
npm install
cd ..

# 4. 配置
cp config.example.json config.json
# 编辑 config.json 填入你的 FFmpeg 路径和 API Key

# 5. 启动
# 终端 1:
cd backend && python run.py
# 终端 2:
cd frontend && npm run dev
```

---

## 项目架构概览

```
backend/app/
├── config.py           # Pydantic v2 配置校验 + 环境防御
├── database.py         # SQLite WAL 数据库
├── main.py             # FastAPI 路由挂载入口
├── routers/            # API 路由层（tasks/config/system/boards）
└── core/               # 核心业务
    ├── pipeline.py     #   流水线调度（下载→转录→总结）
    ├── speaker.py      #   声纹识别 + LLM 身份推理
    ├── transcriber.py  #   ASR 引擎（本地 Whisper / 在线 API）
    ├── downloader.py   #   音频下载（小宇宙/Bilibili）
    ├── summarizer.py   #   LLM 总结（本地 Ollama / 在线）
    ├── queue_manager.py#   SQLite 持久化任务队列
    ├── prompt_manager.py#  Prompt 模板管理
    └── notifier.py     #   通知推送（桌面/邮件）

frontend/src/
├── App.jsx             # SPA 主组件 + 路由
├── index.css           # CSS 变量 + 暗色模式
├── components/         # 通用组件（Sidebar/Topbar/Dialog）
├── contexts/           # ThemeContext
└── views/              # 页面视图（Library/Detail/Workstation/Settings）
```

---

## 编码规范

### Python 后端

- 使用 **Pydantic v2** 做数据校验
- 使用 Python 标准 `logging` 模块，不用 `loguru`
- 延迟导入大库（`torch`、`faster_whisper` 等），不在顶部全局 import
- API 路由按模块拆分到 `routers/`

### React 前端

- 函数式组件 + Hooks
- 样式使用 **CSS 变量**（定义在 `index.css`），不用硬编码颜色值
- 暗色模式通过 `.dark` class 切换
- 通用组件放 `components/`，页面级视图放 `views/`

### 提交规范

提交信息使用中文或英文均可，建议格式：

```
<类型>: <简要描述>

类型包括：feat / fix / refactor / docs / style / chore
```

示例：
- `feat: 新增批量转录接口`
- `fix: 修复暗色模式下文字对比度不足`
- `docs: 更新 README 快速开始章节`

---

## 提交 Pull Request

1. 从 `main` 分支创建你的特性分支：`git checkout -b feat/your-feature`
2. 确保代码能正常启动，无明显报错
3. 提交 PR，描述你做了什么改动以及为什么
4. 关联相关的 Issue（如有）

---

## 需要帮助？

- 查看 [系统架构文档](docs/architecture.md) 了解数据流和设计决策
- 查看 [使用手册](docs/user_guide.md) 了解配置参数
- 提交 Issue 描述你遇到的问题

---

## 致谢

感谢所有贡献者让 whisperMe 变得更好！
