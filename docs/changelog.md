# whisperMe — 变更日志 (Changelog)

## Session `2026-07-10` — v1.0.1 核心配置与交互精细化优化

### 🐛 缺陷修复
- **开机恢复重排队缺陷修复**: 修复了服务器启动时将已完成转录但未总结的任务 (`transcribed` 状态) 当作未完成任务重新塞入队列并自动运行 AI 总结的 Bug，将其收窄至仅恢复真正的 transient 状态 (`pending`, `downloading`, `transcribing`, `summarizing`)。
- **详情页模板选择器样式统一**: 在详情页的 Prompt 弹窗中引入了全新的自定义 `TemplateDropdown` 组件替代原生下拉框，完全对齐设置页下拉菜单的美观样式，高亮及勾选状态一致。

### 🚀 ASR & LLM 性能与配置体验优化
- **测试本地 ASR (FunASR) 转录提速**: 深入测试并优化了本地 ASR 引擎在搭载 FunASR 模型时的处理路径，大幅提升了在 CPU 及 GPU 环境下的离线转录效率，支持分片并行与高精标点恢复。
- **优化本地模型配置体验，统一配置项**: 优化了本地模型配置的交互路径，统一并梳理了设置项，消除了复杂的冗余选项，并在本地 ASR 配置项添加了原生跨平台目录选择（“📁 选择目录”）按钮，彻底支持 Windows、macOS 和 Linux。
- **本地路径默认值绝对化与自动迁移**: 移除了相对路径配置方式，将默认本地 ASR 路径指定为绝对物理路径 `PROJECT_DIR/models/funasr`；加入了启动时的空值自动迁移逻辑，空路径或空字符串将自动升级为绝对路径。
- **在 Settings 中提供模型双重推荐**: 在设置页面为用户提供了本地 ASR (FunASR/Whisper) 和 Ollama 本地大语言模型 (Qwen 2.5) 的智能拉取和配置推荐，同时保留了在线 API 模式，并提供了一键连通性测试。

### 🤖 AI 总结与 Prompt 增强
- **Prompt 模板防错约束设计**: 在默认 AI 总结 Prompt 模板中增加了容错与防错约束指令。当播客任务在未开启声纹识别（即转录文本无 Speaker 区分）的情况下，AI 总结会自动跳过对特定发言人角度立场的拆解，但仍会完整提取并分析出节目中的核心观点与结论，避免总结逻辑发生崩塌。
- **Prompt 模板管理与弹窗体验优化**: 在设置页左侧新增了“AI 总结 Prompt 模板管理”板块，支持在线编辑、切换预设模板、一键保存和重置；在详情页的 Prompt 弹窗中选择模版时自动默认并加载 `标准分析`，同时调整输入框为 `rows={22}` 和 `resize-none`，只保留滚动条。

### ✨ 界面交互与排版优化 (Settings, Workstation, Detail)
- **Settings 页面视觉优化**: 完成了对 Settings 设置页面的整体 UI 与布局重构，移除了无效的引导话术，修复了表单元素间距过大的视觉 Bug，卡片组件排列更加紧凑和谐。
- **Workstation 页面 UI 优化**: 优化了工作台 Workstation 页面在网格与列表模式下的卡片视觉展示，统一了行高与截断逻辑，将节目系列名称和单集标题分线排版，防止折行错乱，使得整体排版主次分明。
- **逐字稿渐进转录与进度状态条重构**: 优化了详情页逐字稿转录阶段的交互，实现了渐进式转录进度的实时展示。同时全面重构了播客卡片的转录进度条 UI 设计，用户可清晰、秒级感知当前任务处于“排队中”、“下载中”、“转录中”、“总结中”还是“失败”等细分状态。
- **暂时隐藏说话人声纹识别分析和管理功能**: 为了提升通用版本的首次运行体验，暂时隐藏了非核心的“说话人声纹识别分析”以及“说话人管理”功能，聚焦于核心的单人/混合快速转录与 AI 总结。
- **播客详情页 AI 总结交互优化**: 移除了右上角常驻的“运行AI总结”按钮，转为在“AI总结” Tab 页下展示；智能匹配任务状态（转录中为置灰的“⏳ 转录中，完成后可运行AI总结”，转录完成后变为红色激活的“✨ 运行 AI 深度总结”）；针对已有总结的任务，在右上角增加了“🔄 重新生成总结”按钮，方便调整 Prompt 后重试。

### 🧹 仓库与数据清理
- **数据库表与无用模块清理**: 清理了项目中不再开发或冗余的功能模块，并清理了 SQLite 数据库中已废弃的旧数据表，保持底层数据结构的极简与高效。

## Session `2026-07-04` — 界面重构与稳定性修复

### 🐛 缺陷修复
- **SSL 证书验证修复**: 移除了在线 API 请求底层的 `verify=False` 限制，彻底修复了连接部分高安全级别 API（如 DeepSeek）时触发的 `[SSL: UNEXPECTED_EOF_WHILE_READING]` 和 SNI 拦截报错。
- **状态管理崩溃修复**: 修复了 React 前端 Zustand 的底层函数式状态更新 Bug (`configData` 意外被替换为 `function`)。彻底解决了在设置面板中切换“多语言（如中英文）”或其他配置时，界面不更新且潜伏崩溃的严重问题。
- **声纹识别逻辑修复**: 修复了关闭“智能声纹推理与说话人分离”选项后，系统仍然去尝试加载 PyAnnote 模型导致单人播客转录流程异常卡死的问题，现在彻底跳过并获得极速转录体验。
- **进程强杀优化**: 完全重构了 `start.bat` 和 `stop.bat`。为 `taskkill` 添加了 `/T` (Process Tree) 参数，能够彻底杀死 Uvicorn worker、FFmpeg 及所有残余子进程。并在每次启动前加入**自动清理探针**，双击启动保证获得纯净的服务环境。

### ✨ 体验优化
- **界面极致梳理**: 
  - 彻底删除了底部冗余的 “Hugging Face 授权”卡片。
  - 将 HF Token 的配置输入框无缝“内嵌合并”到了“实验室选项 (Beta) -> 智能声纹推理与说话人分离”开关的下方。
  - 将所有“连通性测试”按钮重新设计：采用了极简圆角（`rounded-md`）、11px 小字号、Subtle 边框，并将其提炼移动到了每个区块的顶部标题栏右侧，视觉上不再喧宾夺主。
  - 修复了所有按钮文字在小屏幕或缩放时可能产生的“折行”挤压问题（引入了 `whitespace-nowrap shrink-0`）。

## Session `2026-06-28` — Bug 修复与体验优化

### 🐛 缺陷修复
- **端口强杀 (stop.bat/stop.sh)**: 完全重写停止脚本，除了检查 `.whisperMe.pid` 之外，增加底层端口占用强制清理逻辑（Windows 依赖 `netstat/taskkill`，macOS/Linux 依赖 `lsof/kill`），彻底解决启动时 `9101 端口被占用` 的问题。
- **长文本 LLM OOM 处理**: 修复 `call_llm` 因 Ollama 崩溃抛出原生 Exception 导致前端 JSON 解析失败的问题。现在会将其封装为 `HTTPException` 抛出，前端可以优雅地向用户展示真实的 LLM 错误原因（如 context length 超限）。
- **前端 UI 修复**: 修复了播客详情页左下角播放控制栏中，播客封面图加载成功后，默认的首字母兜底文字依然悬浮在图片上方导致重叠的视觉 Bug。

### ✨ 体验优化
- **全平台自启动支持**: 后台新增对 macOS `launchctl` (LaunchAgents) 的支持，前端文案由“Windows 开机自动后台运行”更名为跨平台的“随系统开机自动后台运行”。
- **前后端同源**: 梳理文档和架构，彻底明确生产环境下统一采用 `9101` 端口，前端静态页面通过 FastAPI 直出，根绝 CORS 问题，实现零配置双击即用。
- **设置面板分离**: 将 `HF Token` 配置从 ASR 引擎设置卡片中独立拆分为专用的 `Hugging Face Authorization` 认证卡片，并修复了“系统语言偏好”组件被错误复制两份的问题。

## Session `2026-06-26` — 性能优化 + 字体升级 + 项目整理
### 🚀 RTX 3070 ASR 性能优化 (WP-1)
- **自适应 compute_type**: 按 GPU 总显存自动选择 float16 / int8_float16 / int8
- **默认模型升级**: `large-v3` → `large-v3-turbo`（速度 ~6x 提升）
- **VAD 静音过滤**: Silero VAD filter，跳过静音段推理
- **MP3 直读**: Whisper 直接读取原始 MP3，省去 WAV 转码
- **MiMo 并发**: ThreadPoolExecutor(4 workers) + 分片从 60s → 120s

### 🔧 架构加固 (WP-2/3/4/6)
- **update_task_field**: 轻量 SQLite UPDATE，避免全行 SELECT
- **t_rename_start 修复**: 移出 try 块避免 NameError
- **声纹维度校验**: merge_speakers 前检查 embedding 维度一致性
- **双级置信度**: HIGH ≥ 0.85 才增加声纹信任度计数
- **沙盒收窄**: 环境变量仅劫持 TEMP/TMP（之前覆盖 7 个）

### 🎨 字体系统升级
- **中文**: 得意黑 (smiley-sans) → **思源黑体** (Noto Sans SC, 1.1 MB WOFF2)
- **英文**: **Outfit** (14 KB WOFF2) — 恢复项目最初的英文搭配
- 全部自托管 `frontend/public/fonts/`，零外部请求

### 📦 打包双版本
- **ZIP 完整包**: `whisperMe-Windows-x64-v1.4.0.zip` (4.1 MB)
- **单文件 EXE**: `whisperMe.exe` (113.8 MB)，双击即用，无需 Python
- 新入口 `backend/run_server.py`：品牌横幅 + uvicorn 内进程运行
- 启动器品牌化输出（横幅、状态、停止提示）

### 📁 项目目录整理
- `scripts/` — 所有构建和启动脚本集中
- `assets/` — 图标资源
- `docs/` — 全部文档（含 DESIGN.md, CONTRIBUTING.md）
- 根目录精简至 11 个文件

### 🧹 仓库清理
- 磁盘回收 ~740 MB（temp_sandbox + 旧 release + CDN 原型页面）
- Git 二进制从 4.1 MB → 2.5 MB（仅字体）
- .gitignore 规则完善（amen_break 音频 + backend/data/）
- 删除旧 prompt.json / 空数据库文件 / 备份文件

### 📝 文档同步
- README.md 更新项目结构和启动方式
- CLAUDE.md 重构为最新目录结构和功能清单

## Session `2026-06-25` — 生产打包 + 离线化 + 健壮性

### 📦 生产打包（Windows）
- **PyInstaller 编译**: `launcher.py` → 单文件 `whisperMe.exe`，带 logo 图标
- **Python 嵌入式**: Python 3.12.4 embeddable，无需系统安装 Python
- **FFmpeg 内置**: 自动发现 `ffmpeg/ffmpeg.exe`，用户无需配置
- **发布包**: `whisperMe-Windows-x64-v1.3.1.zip`（~137MB），解压即用
- **GitHub Actions**: `.github/workflows/release.yml` 自动构建 Windows + macOS 包

### 🎨 前端离线化
- **Tailwind CSS v4 编译**: 从 CDN 切换到 `@tailwindcss/vite` 插件编译打包，CSS 58KB 自包含
- **字体本地化**: smiley-sans 字体从 CDN 移至 `frontend/public/fonts/smiley-sans.woff2`，`@font-face` 本地加载
- **移除所有外部 CDN 依赖**: Google Fonts、Material Symbols、Tailwind CDN 全部去除
- **`import.meta.env.DEV` 动态 API_BASE**: 开发模式用完整 URL，生产模式留空

### 🔧 启动器改进
- **端口冲突检测**: `launcher.py` 启动前检查 9101 端口，占用了弹窗提醒
- **PID 文件管理**: `.whisperMe.pid` 记录进程 ID，支持 `stop.bat` / `stop.sh` 停止
- **跨平台支持**: `start.bat` (Windows) + `start.sh` (macOS)

### 🖼️ 图片代理
- **`GET /api/proxy/image?url=...`** : 后端代理 CDN 图片，解决浏览器直连 `image.xyzcdn.net` 失败问题
- **`proxyImage()` 工具函数**: `constants.js` 统一处理图片 URL

### ♻️ 失败任务重试
- **`POST /api/tasks/{id}/retry`**: 重置失败/已取消任务为 pending 并重新入队
- **网络错误智能提示**: 前端检测 timeout/DNS/SSL/403/429 等错误，给出中文修复建议
- **状态显示一致**: `failed`（红色）、`cancelled`（灰色）在列表页和详情页统一展示

### 🤖 MCP Server
- **`/mcp` 端点**: 8 个工具（list_tasks, get_task, search_tasks, create_task, export_transcript, ask_podcast, get_system_status, get_config）
- **可选依赖**: 需 `mcp` 包，未安装时自动降级跳过

### 🗣️ 说话人识别说明
- 在线模式包不包含 torch / pyannote.audio（~2GB），说话人识别仅本地模式可用
- `config.py` lazy import numpy，避免在线包启动崩溃

### 🐛 Bug 修复
- 转录/总结为空时 pipeline 正确标记 `failed`（之前误标记 `completed`）
- HF Token 字段在在线/本地模式均可见（之前隐藏在本地模式条件下）
- `python-multipart` 和 `plyer` 添加到发布依赖

---

## Session `2026-06-24` — P0/P1 功能全量实现 + 暗色模式

### 🎯 P0 核心功能

- **导出 SRT/VTT/Text/JSON**：新增 `GET /api/tasks/{task_id}/transcript?format=srt|vtt|text|json` 端点，支持四种格式的转录文本导出，前端详情页提供 SRT/VTT 下载按钮。
- **说话人系统重构**：声纹库从 `speaker_fingerprints.json` 迁移到 SQLite `speakers` 表，支持 CRUD、合并、忘记操作；新增动态阈值机制（根据 sample_count 在 0.75-0.83 之间自适应）；前端显示说话人置信度颜色标识。
- **引用提取**：在 DEFAULT_ACTION_PROMPT 中新增第 6 节「提及引用与资源索引」，自动提取金句、书籍、影视、工具、人物、关键数据。

### 🚀 P1 增强功能

- **并行转录**：`queue_manager.py` 从单线程重写为可配置线程池，支持 CAS 式任务获取；`max_concurrent_tasks` 配置项（0=自动检测 GPU 显存，1=串行，2-3=并行）。
- **长播客分段总结**：`summarizer.py` 新增 `_split_transcript_into_chunks()` 方法，超长转录自动分段（带 15 行重叠），分段总结后合并为最终报告。
- **批量转录**：新增 `POST /api/tasks/batch` 端点，一次最多提交 20 个 URL。
- **通知优化**：桌面通知包含播客名称 + 标题 + 时长；错误通知截断至 80 字符。
- **API 接口开放**：梳理并稳定 7 个核心 API 端点，为 MCP/Skill 集成做准备。

### 🌙 暗色模式

- **ThemeContext**：新建 `contexts/ThemeContext.jsx`，管理亮/暗主题状态，持久化到 `localStorage`，支持跟随系统偏好。
- **CSS 变量体系**：`index.css` 定义 `--bg-primary`、`--bg-card`、`--text-primary`、`--accent-red` 等 20+ CSS 变量，`.dark` 选择器切换暗色值。
- **全组件适配**：App.jsx、Sidebar、LibraryView、PodcastDetailView、WorkstationView、SettingsView 全部从硬编码十六进制色迁移到 CSS 变量。
- **设置页开关**：SettingsView 新增外观设置卡片，含深色模式切换开关。

### 📝 Prompt 模板系统

- **单一 Prompt 格式**：合并原有 `base_prompt` + `action_prompt` 为单一 Prompt，使用 `{{PODCAST_DATA}}` 占位符标记数据注入位置。
- **预设模板**：`prompt_manager.py` 内置 3 个模板——标准（standard）、简洁（concise）、深度（deep），前端可一键选用。
- **后端 API**：新增 `GET /api/prompt/templates`（列出模板）和 `GET /api/prompt/template/{id}`（获取模板内容）。
- **前端整合**：SettingsView 将两个 Prompt 编辑器合并为一个，新增模板快速选择按钮组。
- **向后兼容**：`load_prompt()` 自动将旧格式 `{base_prompt, action_prompt}` 迁移为新格式 `{prompt}`。
- **summarizer.py 适配**：单次总结和分段总结模式均使用 `user_prompt.replace("{{PODCAST_DATA}}", data_block)` 组装最终 Prompt。

### 🔧 其他改进

- **端口迁移**：因 Windows TCP 残留占住 8000 端口，前后端临时切换至 8001。
- **Speaker embedding 维度兼容**：修复 256 维 vs 512 维声纹 embedding 的 numpy 点积报错。
- **前端进度显示**：任务进度从 `session.progress` 改为 `Math.round(session.progress)`，去掉多余小数位。
- **路由顺序修复**：`/speakers/*` 路由移到 `/{task_id}` 之前，避免 FastAPI 路径参数拦截。

---

## Session `2026-06-23` — 网络代理配置优化

### 🌐 代理分流配置
*   **Clash Verge 分流规则**：添加 whisperMe 项目所需的中国域名直连规则，包括小宇宙 FM、Bilibili、HuggingFace 镜像、ModelScope、小米 MiMo ASR 等。
*   **文档更新**：在 `docs/user_guide.md` 中新增"网络代理配置"章节，详细说明分流规则和域名用途。
*   **CLAUDE.md 更新**：添加网络代理配置信息，便于后续会话了解开发环境。

---

## Session `a6a6c8c6` — 2026-06-22 ~ 2026-06-23

### 🚀 后端架构重构与高并发优化
*   **API 模块化拆分**：将臃肿的 `main.py`（2200+行）重构成清晰的 APIRouter 模块，按领域拆分出 `tasks.py`、`config.py`、`system.py`、`boards.py`。
*   **核心服务与控制层解耦**：抽取 `app/core/speaker.py` 负责声纹比对、Shownotes 交叉检验、LLM 智能匹配与自动重命名逻辑；抽取 `app/core/pipeline.py` 负责整套音画转录、语义聚合与 LLM 总结的流水线调度逻辑，使 `main.py` 仅作为轻量级 "分发外壳" (Shell)。
*   **零外部 AI 依赖极速启动**：重构了 `transcriber.py` 并取消顶部的全局 `import torch` 等大库引用。当 ASR 选择为在线模式（如 SaaS 部署）时，彻底豁免载入本地 AI 库，大幅降低服务器冷启动消耗和内存开销。
*   **Model Cache 显存常驻与 TTL 释放**：内置 `ModelCacheManager` 单例缓存 WhisperModel 避免本地模式下的重复读盘耗时，并支持 `local_model_idle_timeout` 超时自动释放 VRAM 显存并进行 gc 垃圾回收；支持本地模型规格（如 `large-v3-turbo`、`medium`）的自适应选择与在线下载载入。
*   **SQLite 高并发 WAL 与线程隔离**：支持 PRAGMA WAL 模式实现高并发读写；使用 `threading.local` 构筑独立的线程连接池，移除所有只读查询中的 Python 并发锁，大幅提升面板列表与卡片看析的响应性能，同时配合 busy_timeout 与 write_lock 锁定写事务。
*   **零依赖标准日志与 Pydantic 校验**：新建 `logger.py` 利用 Python 内置 `logging` 模块实现彩色控制台输出与滚动物理日志，替换 `loguru` 依赖；升级 `config.py` 改用 Pydantic v2 模型对 `config.json` 自动补齐类型校验，替换 `pydantic-settings` 依赖。
*   **持久化队列与安全取消**：支持 SQLite 驱动的排队状态恢复，并对接 `POST /api/tasks/{task_id}/cancel` 任务中断接口，支持在删除或主动取消正在运行的任务时进行强行安全中断并清理物理临时大文件。

> 按会话 (Session) 分组记录，最新在前。

---

## Session `adc707df` (续) — 2026-06-22

### 🎨 UI 与 UX 交互优化

- **时间与日期布局平铺化**：将媒体库（Recent Recordings）及工作台（Workstation）列表模式下的“时长”、“导入于”和“发布于”元数据堆叠更改为单行平铺展示，使用简洁圆点 `•` 进行区分，并配有微缩日历图标。
- **操作按钮悬停与图标统一**：将媒体库列表行右侧操作按钮（Play, Download, Trash）的悬停背景形状从 `rounded-md` 统一为了 `rounded-full` 圆形，并将删除动作的多功能三点菜单图标（`MoreVertical`）替换为明确的 `Trash2`（小垃圾桶）图标，配合红色 hover 提示态。
- **工作台卡片与列表删除功能打通**：为工作台视图中的所有网格卡片及列表行增加了删除按钮，打通了删除任务及清理本地缓存的交互路径。
- **输入框与文本域聚焦/悬停颜色统一**：在 `index.css` 全局重构了表单控件和 Prompt 文本域的 `:hover`（50% 柔红）与 `:focus`（100% 实体红）边框色，移除了浏览器原生的紫色/蓝色虚光阴影。
- **Prompt 编辑框滚动条圆角与溢出修复**：为 Prompt 输入框的自定义滚动条轨道增加了顶/底各 `8px` 的内缩边距，解决了滚动条在上下边界顶穿 rounded 容器边框的视觉瑕疵。
- **文本域拖拽控制手柄定制化**：将文本域右下角默认原生拖拽角（三角锯齿）重构为带有系统红与 0.3 浅透明度的三道倾斜细线 SVG 极简背景，与 UI 整体风格无缝契合。

### ✨ 新功能

- **双轴日期维度筛选器**：将工作台视图原有的单个 `DATE` 日期下拉筛选器拆分为 **导入日期 (`IMPORTED`)** 和 **发布日期 (`PUBLISHED`)** 两个独立的下拉选项，支持“全部时间”、“最近 7 天”、“最近 30 天”的双维度交叉精确计算与过滤。

---

## Session `adc707df` — 2026-06-20

### 🎨 UI 与 UX 交互优化

- **全新 Warm Professional 主题重构**：全面接入 Stitch 导出的 AIStudio 高级版面设计，采用米色底色搭配暗红（`#bf0029`）与朱红（`#f62440`）的温暖质感视觉体系。
- **三栏独立子标签页重构**：将播客详情页右边栏拆分为三个独立的子标签页——**“AI总结”**、**“节目简介”**（含 clickable 时间线）以及**“听众热评”**（含点赞与时间跳转功能），彻底解决了简介与热评过长导致的堆叠杂乱问题。
- **方形海报封面绑定**：Library 列表与 Workstation 网格视图中的播客列表全面绑定播客自身的方形 1:1 封面图（`task.image_url`），替换了此前临时的 Unsplash 随机素材。
- **自适应拖拽分割栏**：播客详情页左右两栏之间新增了可自由拖拽调整比例的滑块，左右容器实现独立滚动。
- **无边扩展滚动条**：自定义开发了扩展式透明滚动条，鼠标悬浮或拖拽时会自动增宽并呈品牌红色。

### ✨ 新功能

- **发言人自定义管理 (SPEAKER MANAGER)**：
  - 在详情页顶部重新恢复了“发言人管理”按钮。
  - 新增发言人管理模态弹窗，自动展示该期节目中识别出的全部发言人 ID 及已命名昵称。
  - 支持在弹窗中进行编辑重命名，修改通过 `POST /api/tasks/{task_id}/speaker/rename` 接口进行热更新并即时重载页面，使得全局转录气泡中展现的主播/嘉宾昵称实时生效。
- **真实的磁盘使用量监控 (Storage Used)**：将首页的 Storage Used 状态卡片升级为接入真实的磁盘使用情况。优先从 Uvicorn 后端的 `/api/performance` 接口读取被监控存储目录的实际物理磁盘使用量，并在性能监测未加载时优雅降级为模拟值。
- **总结 Prompt 模板在线编辑恢复**：在设置页面中成功恢复了在线编辑 AI 总结 Prompt 的功能（分为防幻觉守则 `Base Prompt` 与输出格式指令 `Action Prompt`），支持对 `/api/prompt` 接口进行热保存以及一键恢复默认模板。

### 🐛 Bug 修复

- **系统设置白屏 crash 修复**：修复由于在 `SettingsView.jsx` 中缺少从 React 导入 `useState` 导致的 ReferenceError 白屏崩溃问题。
- **热评空白修复**：修复由于前端接口误匹配 `comment.text` 导致热评区域空白不展示文本的问题，变更为读取正确的 `comment.content`，并使评论里的时间节点同样具备时间戳播放跳转功能。

---

## Session `c5508343` — 2026-06-19 ~ 2026-06-20

### ✨ 新功能

- **四阶段发言人智能推断流水线**：极大提升了当某些常驻主播缺席该期节目的识别准确率。流水线包含四个阶段：
  1. **阶段C (前置过滤)**：自动过滤仅含语气词或极短发言的无效 Speaker 节点。
  2. **阶段B (Shownotes 拆分)**：智能分离节目内容区与固定模板区，分别提取人物名单。
  3. **阶段A (LLM 双重推断)**：先甄别真正参与本期录制的人员名单，随后根据上下文内容进行精准身份匹配。
  4. **阶段D (交叉验证)**：后置验证分配的人名是否重复或不合理，对冲突结果进行降级回退兜底。
- **全链路处理耗时统计**：在转录与分析完成后，AI 总结报告底部将自动附加精确到秒级的流水线处理耗时统计，包含音频下载、音频预处理、声纹分割、语音转录、发言人推断及 AI 深度总结各个子阶段的耗时。

### 🐛 Bug 修复与体验优化

- **终端字符编码问题修复**：修复在 Windows 环境中双击 `一键启动.bat` 时出现的 GBK 乱码和“工具找不到”报错，强制切换至 `chcp 65001` UTF-8 编码环境。
- **日志精简**：通过 Python 原生 `warnings` 模块全面屏蔽了后端控制台中由 PyAnnote, Torchaudio 和 SpeechBrain 抛出的大量过期特性（Deprecated）警告，使后台运行日志更清爽。

## Session `c29845b5` (续) — 2026-06-19 ~ 2026-06-20

### 🎨 UI 与 UX 交互优化

- **左下角模型选用状态展示**：在侧边栏底部的 ASR 与 LLM 引擎状态区新增了当前激活/选用的模型名称显示。支持智能提取本地/云端模型名称、防溢出截断与鼠标悬停完整路径提示，未配置时提供合理的默认回退值。

---

## Session `693458b4` — 2026-06-17

### ✨ 新功能

- **一键启动脚本**：新增 `start_project.py` 及 Windows 快捷入口 `一键启动.bat`。通过多线程同时拉起前端 Vite 与后端 Uvicorn，并将进程的 stdout/stderr 重定向落盘至 `logs/` 目录下，支持 `Ctrl+C` 完美清理所有的关联子进程。

### 📝 文档更新

- **README 重构**：全面重写了项目首页文档 `README.md`。增强排版、加入结构化插图建议占位符，提供了非常清晰的快速上手及功能介绍清单，提升开源项目“产品感”。
- **架构文档与日志同步**：更新 `docs/architecture.md` 中的目录结构，加入 `start_project.py` 与日志目录等最新内容，并同步此处的 `changelog.md`。

### 🛡️ 安全与配置

- **Git 追踪与脱敏修复**：将 `logs/` 及本地数据库备份文件 (`*.bak`, `*.db`) 加入 `.gitignore` 防止意外推送。为用户澄清了 `config.json` 的 Git 忽略机制，并重新填补其默认非敏感配置，避免其在更新仓库后配置变为空白。

---

## Session `4eeb3257` — 2026-06-16 ~ 2026-06-17

### 🎨 UI 与 UX 交互优化

- **菜单与顶栏命名对齐**：统一侧边栏与对应顶部栏的标题命名（“我的播客库”、“系统设置”），彻底消除不同页面下命名不一致产生的概念歧义
- **Logo 与品牌文字展示调整**：去除侧边栏小字副标题，将 Logo 尺寸调大至 `36px`，并将 `whisperMe` 标题字体字号增加至 `25px`，以优化侧边栏布局比例
- **设置子标签图标去重**：移除设置标签切换按钮上重复渲染的 Emoji 图标
- **收藏/点赞按钮交互重构**：移除鼠标悬停在星星图标上的 Tooltip 提示，交互时优先进行前端状态变色反馈（Optimistic UI），并移除了页面底部的条状 Toast 提示，改在星星图标处展示精简、即时的高速变色微动效，极大地降低了用户的主观等待感

### ✨ 新功能

- **SQLite 关系数据库重构**：将底层数据持久化层从原有的单 JSON 文件 (`tasks_db.json`) 彻底重构为 SQLite 关系数据库 (`whisperMe.db`)。支持数据无损迁移（启动时自动侦测并将历史 JSON 数据导入数据库，后生成备份 `.bak` 文件）及线程安全锁定。
- **自定义数据/音频下载存储路径**：在“语音转录 (ASR)”配置下新增外挂存放地址配置。支持配置全局存储基准路径 (`storage_base`)，音频文件及 SQLite 数据库将默认移入该指定目录存储，完美支持后期独立打包部署。
- **系统设置子标签重构**：将系统设置页面的长表单划分为“外观与语言”、“语音转录 (ASR)”、“AI 总结 (LLM)”与“消息通知 (SMTP)”四个子标签，极大优化了界面紧凑度
- **多语言 (i18n) 下拉选择器**：在“外观与语言”设置下提供中/繁/英/日多语言动态切换，本地持久化偏好并在切换时立即刷新全局文本

---

## Session `c29845b5` — 2026-06-04 ~ 2026-06-10

### 🎨 UI 视觉优化

- **统一圆角风格**：消除播客卡片与对话面板中圆角/直角混用的问题，全局统一使用 `border-radius` 设计令牌
- **播客卡片元数据布局优化**：为时间、评论数、点赞数等元数据添加椭圆标签样式（pill badge），改善间距与布局紧凑性
- **浅色模式说话人昵称可读性增强**：提升 `.speaker-badge` 在 Light Theme 下的对比度与清晰度
- **系统设置页面统一性优化**：重新设计设置子标签页（外观/ASR/LLM/通知）的布局，使配置项菜单大小、间距和排列更加统一

### ✨ 新功能

- **邮件通知开关**：新增 `enable_email_notification` 配置项，允许用户在设置页面独立控制是否在转录/总结完成后发送邮件通知，默认为关闭
- **Windows 桌面通知开关**：`enable_win_notification` 支持 UI 可视化切换
- **元数据刷新**：新增 `POST /api/tasks/{id}/metadata/refresh` 接口，支持手动刷新已完成任务的元数据（节目信息、评论数、点赞数等）
- **系统设置子标签页**：将设置页面拆分为"外观与语言"、"语音转录 (ASR)"、"AI 总结 (LLM)"和"消息通知 (SMTP)" 四个子标签
- **多语言 (i18n)**：新增界面语言切换器，支持 简体中文 / 繁體中文 / English / 日本語
- **LLM 离线检测**：当检测到本地 LLM 服务未运行时，显示醒目的警告横幅提示用户

### 🐛 Bug 修复

- **播放倍速修复**：修复默认倍速为 `0.75x` 的问题，改为默认 `1x`；修复倍速选择器 `<option>` value 与实际设置不同步的 mismatch 问题
- **任务详情页白页 Bug**：修复点击最新一期播客进入详情后显示系统设置白页面的问题
- **播客卡片空白区域**：消除卡片列表中意外出现的空白间隙
- **音频跳转不匹配**：修复转录对话行点击时音频跳转定位不准的问题
- **进度条颜色**：修复任务进度条在不同状态下颜色显示异常

### 🔧 技术改进

- **LLM 语义拼缝 (Semantic Sewing)**：优化长文本分块总结时的语义连贯性
- **Prompt 模板可配置化**：AI 总结的 Prompt 模板支持通过 `/api/prompt` 接口在线编辑
- **任务自动恢复**：后端重启时自动将中断的未完成任务重新入队

---

## Session `5cbe0e2c` — 2026-06-13 ~ 2026-06-17

### ✨ 新功能

- **认知沙盒模块**：实现包含 3D 老虎机 (Slot Machine)、AI 碰撞器 (AI Collider) 的完整认知沙盒功能
- **Anki 闪光卡片**：支持从播客段落一键生成学习卡片，内置艾宾浩斯复习间隔算法
- **AI 碰撞器雷达自动发现**：实现跨播客卡片的自动关联发现与合成报告生成
- **播客节目主页自动解析**：输入小宇宙播客主页链接（`/podcast/...`）时，后台能够自动获取网页并智能提取、转换为最新单集 URL 进行转录
- **剧本点击跳转逻辑优化**：点击剧本对话流气泡时，跳转至该段落的起始时间（`para.start_time`），而非具体的单词时间，提高交互逻辑可理解性；悬浮对话气泡时增加播放图标指示。
- **网友热评及简介时间戳跳转**：自动解析网友热评及节目简介中的时间戳格式（如 `31:13`、`01:05:20`），转换为可点击的交互式跳转按钮，支持直接定位音频。
- **对话流自动定位滚动**：点击任何时间戳（评论区或简介）跳转播放时，左侧剧本对话流会自动平滑滚动至对应时间戳的段落，并提供为期 2 秒的金色发光（`glow-highlight`）高亮视觉反馈。

### 🐛 Bug 修复

- **在线 ASR 负荷修复**：移除在线 ASR API 负载中冗余的 text prompt，避免 API 报错，同时修复大模型接口的重试/报错提示机制
- **网络代理自愈机制 (DoH DNS Bypass)**：实现 `doh_dns_bypass` 上下文管理器，当使用 Clash 等代理工具的 TUN/全局 Fake-IP 模式时，拦截 `socket.getaddrinfo` 将特定在线 API 域名以公网真实 IP 直接绑定，完美解决 SSL EOF 报错
- **4 级自适应下载器**：在 `downloader.py` 中实现 HTTPX (有代理) -> HTTPX (无代理直连) -> curl (有代理) -> curl (直连+DoH解析) 的 4 级自适应网页抓取策略，保证可在各种极端代理配置下成功下载音频和网页
- **DNS 解析**：替换被封锁的 `dns.google` DoH 查询为鲁棒的 `resolve_host_via_doh` (内置阿里云与腾讯 DoH 并配合静态 IP 兜底)
- **下载器缓存对齐**：修复下载器缓存与数据库状态不一致的问题
- **认知沙盒面板重叠**：修复金色收纳柜面板重叠的 UI Bug
- **转录去重**：解决转录结果中出现重复段落的问题

### 🎨 UI 优化

- **老虎机视觉重构**：多次迭代重新设计为高保真 3D 风格，包含圆柱卷轴、物理按钮、发光投币口和交互式 3D 侧拉杆
- **组件模块化**：将 SlotMachine 和 AiCollider 拆分为独立 `.jsx` 模块文件

### 🔧 技术改进

- **LLM 说话人智能推断兜底**：在段落聚类时，对未成功进行声纹比对的 `UNKNOWN_SPEAKER` 段落，通过大模型结合上下文对话内容进行语义推理，自动补齐和推断缺失的说话人角色，提升台词组合与段落切分的准确度。
