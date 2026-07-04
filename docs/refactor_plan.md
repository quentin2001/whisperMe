# whisperMe 重构与优化路线图 (Refactor Plan)

> 基于 2026-07-03 全代码库扫描诊断报告

## 🩺 第一部分：诊断报告总结 (Top 5 技术债)

经过对项目代码库（近 10,000 行核心逻辑）的深度审计，目前存在以下五个极其严重的技术债，已对系统的可维护性、性能和安全性产生威胁：

### 1. 前端 Mega-Components 与性能坍塌
- **现状**：`PodcastDetailView.jsx` 高达 1,658 行，包含 5 个内联组件、30+ 个 useState，集成了从播放器控制到问答、字幕渲染的所有逻辑。`App.jsx` 也是 God Component。
- **痛点**：极其严重的 Prop Drilling（15+ props 透传）；毫无 `useMemo` 或 `React.memo`，当播放器进度更新时（每秒 4 次），触发全量重新渲染；`scrollIntoView` 挂载在主循环中导致滚动性能暴跌。

### 2. 后端 Fat Controllers 与严重耦合
- **现状**：`routers` 层（如 `tasks.py` 和 `boards.py`）不仅处理 HTTP 请求，还直接混杂了：100 多行的 LLM 调用、复杂的 SRT/VTT 文本格式化、物理文件读写、艾宾浩斯记忆算法等。
- **痛点**：缺乏 Service 层抽象；Controller 代码过于庞大，且没有使用 Pydantic 的 `response_model`，接口契约形同虚设。

### 3. God Classes (上帝类) 的失控
- **现状**：`database.py` (931 行，50+ 个方法) 处理所有 7 张表的 CRUD 和数据库版本迁移；`downloader.py` (1219 行) 把 4 种播客平台的解析、下载、重试逻辑全部揉在了一起；`pipeline.py` 中 `run_podcast_pipeline` 函数单体长达 330 行。
- **痛点**：代码修改的“痛苦面”极大。新增一个平台下载支持或增加一个数据库表，都必须修改这些巨型文件，极易引发回归 Bug。

### 4. 关键级别的安全与并发漏洞
- **现状 (SSRF)**：`/api/proxy/image` 接口接收任意 URL 并服务端代为请求，没有任何白名单限制，存在高危内网探测 (SSRF) 风险。
- **现状 (线程安全)**：`network.py` 中的 `doh_dns_bypass` 对 `socket.getaddrinfo` 进行全局猴子补丁（Monkey Patch），若多线程同时并发下载，将互相污染 DNS 解析。

### 5. LLM 调用逻辑大量复制粘贴
- **现状**：系统中存在 4 处几乎一模一样的底层 LLM HTTP 调用封装（分别在 `llm_utils.py`, `speaker.py`, `transcriber.py`, `summarizer.py`）。
- **痛点**：若未来需要升级大模型接口规范或支持 Streaming 流式输出，需要修改 4 处截然不同的代码。

---

## 🗺️ 第二部分：重构路线图 (分阶段规划)

### Phase 1：低挂的果实 (Low-hanging fruits)
*目标：本周内可完成，代码改动局限在特定文件内，修复安全隐患，立刻提升稳定性和开发体验。*

- [ ] **修复 SSRF 漏洞**：在 `/api/proxy/image` 中引入目标域名白名单（仅允许 `xiaoyuzhoufm.com`, `bilibili.com` 等平台域名）。
- [ ] **收敛 LLM 网络调用**：彻底删除 `speaker.py`、`transcriber.py`、`summarizer.py` 中的私有 `_call_llm`，统一强制使用 `llm_utils.py`。
- [ ] **修复前端的 ReferenceError 炸弹**：修复 `SettingsView.jsx` 第 79 行由于变量提升导致的潜在报错。
- [ ] **清理重复魔术变量**：将代码中散落的 `0x08000000` 统一替换为 `subprocess.CREATE_NO_WINDOW`；统一 `interjection_chars` 等硬编码数组。
- [ ] **补全 Response Model**：为至少核心的 GET `/api/tasks` 和 `/api/config` 引入 Pydantic Response 返回模型，明确数据结构。

### Phase 2：核心逻辑解耦 (Core Logic Decoupling)
*目标：大面积动刀，将胖控制器和上帝类拆分为现代分层架构（Controller -> Service -> Repository）。*

- [ ] **重构路由层 (Fat Controllers)**：
  - 提取 `tasks.py` 中的格式化逻辑到 `app/utils/formatters.py`。
  - 提取 `boards.py` 中的记忆算法与卡片碰撞逻辑到 `app/services/board_service.py`。
- [ ] **拆解 `database.py` (God Class)**：
  - 建立 Repository 模式，拆分为 `TaskRepository`, `SpeakerRepository`, `BoardRepository` 等。
  - 剥离那段 170 行的 `_migrate_if_needed()` 数据库迁移脚本为独立的初始化流程。
- [ ] **拆解 `downloader.py`**：
  - 应用策略模式（Strategy Pattern），拆分出独立的 `XiaoyuzhouStrategy`, `BilibiliStrategy`, `GenericStrategy`。
- [ ] **重写前端状态管理**：
  - 引入 Zustand 替换 `App.jsx` 中失控的 30 多个 `useState`。
  - 将全局配置、主题、系统性能监控全部移入各自独立的 Zustand Store，消除 Prop Drilling。

### Phase 3：性能与健壮性提升 (Performance & Robustness)
*目标：解决运行时瓶颈，优化渲染效率和后端防线。*

- [ ] **重构前端 `PodcastDetailView.jsx`**：
  - 必须进行组件拆分：`AudioPlayerControl`, `TranscriptList`, `SpeakerManagerModal`, `QAChatPanel`。
  - 引入 `useMemo` 和 `React.memo` 避免每秒 4 次的全量刷新瀑布。
  - 对播放进度自动滚动的 `scrollIntoView` 添加防抖（Debounce），并仅在段落边界跨越时触发。
- [ ] **彻底改造前端 i18n 系统**：
  - 废弃全局传递的简陋 `t(zh, en)` 函数。
  - 引入 `i18next` 或基于 Context 封装标准 hook（`useTranslation`），消除国际化对组件 Props 的污染。
- [ ] **后端网络并发安全性加固**：
  - 移除 `network.py` 中的全局 `socket` 猴子补丁，改为通过 `httpx` 的 `Transport` 层面自定义 DNS 解析，实现线程安全的穿透。
  - 解决 `database.py` 中 `update_task()` 方法的 N+1 Read-Modify-Write 性能损耗，全部替换为 `update_task_field`。
- [ ] **前端引入 Error Boundary**：在关键组件外部包裹 Error Boundary，防止因为某条特殊格式的渲染错误导致整个应用白屏。

---

> **Chief Architect's Note**: 
> 目前的首要任务（Highest Priority）是 **Phase 1 的安全漏洞与重复代码修复**，随后立即展开 **Phase 2 的 Zustand 前端状态库引入**，这是拆解 `PodcastDetailView.jsx` 的基础前提。
