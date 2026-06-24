# whisperMe 增量处理流水线 + 端口规划 + Agent 接口设计

**日期**: 2026-06-24
**状态**: 草案，待用户审批

---

## 一、问题背景

当前 whisperMe 的处理流水线是完全串行的：下载 → 预处理 → 声纹分割 → Whisper 转录 → 段落聚类 → AI 总结。用户提交一个 2 小时播客后，需要等待 10-25 分钟才能看到任何结果。此外，项目使用的端口（8001/5173）容易与其他开发项目冲突，且缺少面向 AI Agent 的标准化接口。

本设计覆盖三个目标：
1. **增量处理体验** — 音频即时播放 + 转录逐步显示 + AI 总结加载态
2. **端口规划** — 避免与常见开发工具端口冲突
3. **Agent 接口预留** — 为未来 AI Agent 操控 whisperMe 预留标准化 API 入口

---

## 二、端口规划

### 当前端口

| 服务 | 端口 | 冲突风险 |
|------|------|----------|
| 后端 API (FastAPI) | 8001 | 高 — Jupyter/其他 Python 服务常用 |
| 前端 Dev (Vite) | 5173 | 中 — 所有 Vite 项目默认 |
| Ollama (本地 LLM) | 11434 | 低 — Ollama 标准端口，不改 |

### 新端口方案

| 服务 | 旧端口 | 新端口 | 理由 |
|------|--------|--------|------|
| 后端 API | 8001 | **9101** | 远离 8000-8080 拥堵区，好记（9-1-0-1） |
| 前端 Dev | 5173 | **9173** | 保留 173 后缀便于记忆，无常见框架占用 |

### 需要修改的文件

**后端端口变更（8001 → 9101）：**
1. `backend/run.py` — uvicorn `--port` 参数
2. `frontend/src/constants.js` — `API_BASE`
3. `backend/app/main.py` — CORS `allow_origins`
4. `CLAUDE.md` — 端口文档
5. `docs/architecture.md` — 端口文档（当前错误写着 8000）

**前端端口变更（5173 → 9173）：**
1. `frontend/vite.config.js` — 添加 `server: { port: 9173 }`
2. `backend/app/main.py` — CORS `allow_origins`
3. `backend/app/routers/boards.py` — 硬编码的 `localhost:5173` 链接
4. `CLAUDE.md` — 端口文档
5. `docs/architecture.md` — 端口文档

---

## 三、增量处理流水线

### 3.1 体验时间线（以 2 小时播客为例）

```
T+0min    提交任务
T+1~2min  音频下载完成 → 用户可立刻播放收听，转录面板显示"正在分析说话人特征..."
T+3~5min  声纹分割完成，Whisper 开始转录
T+5~8min  首批段落出现 → 此后每 20-30 秒新增段落
T+15~20min 转录完成 → 右侧显示"AI 正在深度分析..."加载动画
T+16~22min AI 总结生成 → 全部完成
```

### 3.2 后端改动

#### 3.2.1 pipeline.py — 提前注册 audio_url

**当前**: `audio_url` 在第 131 行写入（预处理之后）
**改为**: 下载完成并写入元数据后立即注册（第 119 行之后）

```python
# 当前顺序:
# 1. download (L105)
# 2. write metadata (L112)
# 3. status="transcribing" (L123)
# 4. preprocess audio (L125)
# 5. set audio_url (L131)  ← 太晚

# 新顺序:
# 1. download (L105)
# 2. write metadata (L112)
# 3. SET audio_url ← 提前到此处
# 4. status="transcribing" (L123)
# 5. preprocess audio (L125)
# (删除原 L131 的 audio_url 设置)
```

影响范围：仅 `pipeline.py`，移动两行代码。前端无需改动（`App.jsx` 第 561 行的 `<audio>` 已根据 `audio_url` 是否存在自动渲染）。

#### 3.2.2 transcriber.py — 增量段落回调

**改动 1**: `transcribe_and_merge` 新增 `on_segment_batch` 回调参数

```python
def transcribe_and_merge(self, wav_path, diarization_segments,
                         progress_callback=None, asr_mode="local",
                         on_segment_batch=None):  # 新增
```

**改动 2**: 本地 Whisper 模式从 `list(whisper_segments_raw)` 改为逐段迭代

当前代码（第 363 行）一次性消费整个生成器：
```python
whisper_segments = list(whisper_segments_raw)
```

改为逐段迭代，每 10 段调用一次回调：
```python
batch_buffer = []
for seg in whisper_segments_raw:
    # 去重、说话人匹配、时间戳计算（逻辑不变）
    merged_seg = {...}
    merged_results.append(merged_seg)
    batch_buffer.append(merged_seg)

    if on_segment_batch and len(batch_buffer) >= 10:
        on_segment_batch(batch_buffer)
        batch_buffer = []

if on_segment_batch and batch_buffer:
    on_segment_batch(batch_buffer)
```

**改动 3**: 提取 `_find_speaker` 辅助方法

将第 387-409 行的说话人匹配逻辑提取为独立方法，供批量和非批量路径复用：

```python
def _find_speaker(self, seg, diarization_segments):
    seg_center = (seg.start + seg.end) / 2
    best_match = None
    max_overlap = 0.0
    for d in diarization_segments:
        if d["start"] <= seg_center <= d["end"]:
            return d["speaker"]
        overlap = max(0, min(seg.end, d["end"]) - max(seg.start, d["start"]))
        if overlap > max_overlap:
            max_overlap = overlap
            best_match = d["speaker"]
    return best_match or "UNKNOWN_SPEAKER"
```

**改动 4**: 在线 ASR 模式同样支持回调

在线 ASR 返回全部段落后，在合并阶段分批调用回调（逻辑与本地模式一致）。

#### 3.2.3 pipeline.py — 增量段落写入

在转录步骤中定义回调函数：

```python
accumulated_segments = []

def on_segment_batch(new_segments):
    accumulated_segments.extend(new_segments)
    try:
        paragraphs = transcriber.cluster_segments_to_paragraphs(task_id, accumulated_segments)
        db.add_paragraphs(paragraphs)  # INSERT OR REPLACE，自动更新末段
    except Exception as e:
        print(f"[LOG] Incremental paragraph write failed: {e}")

merged_transcript = transcriber.transcribe_and_merge(
    standardized_wav, diar_data,
    progress_callback=progress_callback,
    asr_mode=asr_mode,
    on_segment_batch=on_segment_batch
)
```

原有的第 164 行 `db.add_paragraphs(paragraphs)` 保留作为最终兜底，确保完整性。

#### 3.2.4 pipeline.py — 断点续传逻辑调整

增量写入后，转录过程中也会有段落存在于数据库。当前的跳过条件需修改：

```python
# 当前（第 59-60 行）:
existing_paragraphs = db.get_paragraphs_by_podcast(task_id)
if existing_paragraphs and len(existing_paragraphs) > 0:
    # 跳过转录 → 直接总结

# 改为:
existing_paragraphs = db.get_paragraphs_by_podcast(task_id)
has_full_transcript = bool(task.get("transcript"))
if existing_paragraphs and len(existing_paragraphs) > 0 and has_full_transcript:
    # 有完整转录 → 跳过转录，直接总结（断点续传）
elif existing_paragraphs and len(existing_paragraphs) > 0 and not has_full_transcript:
    # 有段落但无完整转录 → 上次中断在转录中，清理后重跑
    db.delete_paragraphs_by_podcast(task_id)
    # 继续正常流水线...
```

关键判断：`task.get("transcript")` 只在完整转录完成后才填充（第 156 行），所以有段落但无 transcript 意味着上次中断在转录中途。

#### 3.2.5 tasks.py — 返回所有状态的段落

当前 `get_task_details`（第 137 行）只在 `status == "completed"` 时返回段落。改为所有状态都返回：

```python
# 当前:
if task.get("status") == "completed":
    paragraphs = db.get_paragraphs_by_podcast(task_id)
    # ... sedimented 检查 ...
    task["paragraphs"] = paragraphs
else:
    task["paragraphs"] = []

# 改为:
paragraphs = db.get_paragraphs_by_podcast(task_id) or []
# 仅对已完成任务做 sedimented 检查（避免转录中频繁查询 cards 表）
if task.get("status") == "completed" and paragraphs:
    podcast_cards = db.get_cards_by_podcast(task_id)
    sedimented_ids = {c["paragraph_id"] for c in podcast_cards}
    for p in paragraphs:
        p["sedimented"] = p["id"] in sedimented_ids

    # 旧格式兼容检查（仅已完成任务需要）
    is_old_format = paragraphs and ("sentences" not in paragraphs[0] or
                     not isinstance(paragraphs[0].get("sentences"), list))
    if is_old_format and task.get("transcript"):
        paragraphs = transcriber.cluster_segments_to_paragraphs(task_id, task["transcript"])
        db.delete_paragraphs_by_podcast(task_id)
        db.add_paragraphs(paragraphs)

task["paragraphs"] = paragraphs
```

### 3.3 前端改动

#### 3.3.1 PodcastDetailView.jsx — AI 总结加载动画

第 969 行的 summary 区域增加条件渲染：

```jsx
{detailSubTab === "summary" && (
  <div className="...">
    <div className="flex items-center gap-2 pb-4 border-b ...">
      <Sparkles size={18} />
      <h3>AI VALUE ANALYSIS REPORT</h3>
    </div>

    {activeTask.status === "summarizing" ? (
      // 加载动画
      <div className="flex flex-col items-center justify-center py-12 gap-4">
        <div className="w-10 h-10 border-3 border-[var(--accent-red)]
                        border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-[var(--text-muted)] font-semibold">
          {t("AI 正在深度分析转录文本...", "AI is analyzing the transcript...")}
        </p>
      </div>
    ) : activeTask.summary ? (
      <MarkdownRenderer text={activeTask.summary} t={t} />
    ) : (
      <p className="text-[var(--text-muted)] text-xs">
        {t("暂无总结内容", "No summary content available")}
      </p>
    )}
  </div>
)}
```

#### 3.3.2 PodcastDetailView.jsx — 转录进度指示器

在转录面板（左侧）顶部添加状态提示：

```jsx
{(activeTask.status === "downloading" || activeTask.status === "transcribing") && (
  <div className="flex items-center gap-2 mb-4 px-3 py-2
                  bg-[var(--accent-red-light)] border border-[var(--border-primary)] rounded-lg">
    <div className="w-3 h-3 border-2 border-[var(--accent-red)]
                    border-t-transparent rounded-full animate-spin" />
    <span className="text-xs text-[var(--accent-red)] font-semibold">
      {activeTask.status === "downloading"
        ? t("正在下载音频...", "Downloading audio...")
        : t("转录进行中...", "Transcribing...") + ` (${paragraphs.length} ${t("段", "paragraphs")})`
      }
    </span>
  </div>
)}
```

#### 3.3.3 PodcastDetailView.jsx — statusMap 更新

第 778 行添加 `summarizing` 状态：

```javascript
const statusMap = {
  completed: "Completed", failed: "Failed", cancelled: "Cancelled",
  pending: "Queued", downloading: "Downloading",
  transcribing: "Transcribing", summarizing: "Summarizing"  // 新增
};
```

#### 3.3.4 App.jsx — 无需结构性改动

- 音频播放器已根据 `audio_url` 自动渲染
- 3 秒轮询已在 "transcribing" 状态时触发
- `fetchTaskDetail` 已自动更新 `activeTask` 包含 paragraphs

### 3.4 数据库

**无 schema 变更。** `paragraphs` 表的 `INSERT OR REPLACE` 语义天然支持增量写入。`tasks` 表已有所有需要的字段。

### 3.5 额外开销分析

| 环节 | 开销 | 说明 |
|------|------|------|
| 段落聚类重算 | ~100ms | 每 10 段重聚类一次，纯 Python 分组逻辑 |
| 数据库增量写入 | ~100ms | 100 次 × 1ms/次，WAL 模式下不阻塞读 |
| Whisper 迭代方式 | 0 | 逐段迭代 vs list()，处理量相同，内存更低 |
| **总计** | **~200ms** | 对比 10-25min 总时长，< 0.1% |

### 3.6 错误处理

- **转录中途崩溃**: 重启后检测到有段落但无 transcript → 清理段落 → 从头重跑
- **任务删除**: `check_cancelled()` 在每步检查，`db.delete_task()` 级联删除段落
- **并发读写**: SQLite WAL 模式允许写入时读取，3 秒轮询无阻塞
- **段落 ID 稳定性**: `{podcast_id}-p{idx}` 格式，`INSERT OR REPLACE` 自动更新末段内容

### 3.7 实施顺序

1. `backend/app/core/transcriber.py` — 提取 `_find_speaker`，添加 `on_segment_batch`
2. `backend/app/core/pipeline.py` — 提前 audio_url，添加增量回调，修复断点续传
3. `backend/app/routers/tasks.py` — `get_task_details` 返回所有状态段落
4. `frontend/src/views/PodcastDetailView.jsx` — 加载动画 + 进度指示器 + statusMap
5. 端口变更（见第二节）
6. Agent 接口预留（见第四节）

---

## 四、AI Agent 接口预留

### 4.1 现状

当前 API 已经能覆盖 Agent 的大部分基本需求：提交任务、查询状态、获取转录、导出。但存在以下缺口：

| 缺口 | 影响 |
|------|------|
| 无搜索/过滤 API | Agent 无法按关键词、播客名、日期筛选任务 |
| 无分页 | 任务量大时一次返回全部，效率低 |
| 无任务完成回调 | Agent 只能轮询，无法被动接收通知 |
| 响应格式不统一 | `{success}` vs `{status}` vs 原始 dict，Agent 解析困难 |
| 无 API 版本 | 未来改动可能破坏 Agent 集成 |

### 4.2 设计原则

**本次不实现 Agent 接口**，但需要在架构改动中预留空间：

1. **API 路径预留**: 新增端点统一使用 `/api/v1/` 前缀，旧端点保持 `/api/` 不变（双轨兼容）
2. **CORS 配置**: 允许来自非 5173/9173 端口的本地请求（Agent 可能从任意端口调用）
3. **响应格式**: 增量流水线新增的端点（如有）采用统一格式 `{"ok": true, "data": {...}}`
4. **OpenAPI 文档**: FastAPI 自动生成 `/docs`，确保所有端点有清晰的请求/响应 schema

### 4.3 未来 Agent 接口路线图（本次不实现）

以下端点作为未来规划记录，不在本次实施范围内：

```
# 搜索与过滤
GET  /api/v1/tasks/search?q=&podcast=&status=&from=&to=&page=&limit=

# 任务完成回调
POST /api/v1/tasks  (body 新增可选字段 callback_url)

# 队列状态
GET  /api/v1/queue

# 批量转录获取
POST /api/v1/tasks/batch-transcript  (body: {task_ids: []})

# 统一导出
GET  /api/v1/tasks/{id}/export?format=markdown  (summary + transcript + metadata 合并)
```

### 4.4 本次需要做的预留动作

1. **CORS 放宽**: `allow_origins` 从固定端口列表改为 `["http://localhost:*", "http://127.0.0.1:*"]` 或使用正则匹配
2. **FastAPI metadata**: 在 `FastAPI()` 构造函数中补充 `description`、`contact` 等元数据，让 `/docs` 页面更专业
3. **确保所有新端点有类型注解**: FastAPI 自动从类型注解生成 OpenAPI schema

---

## 五、验收标准

### 增量流水线
- [ ] 提交播客 URL 后，音频下载完成即可播放
- [ ] 转录过程中，段落每 20-30 秒增量出现在转录面板
- [ ] 声纹分割阶段显示"正在分析说话人特征..."提示
- [ ] AI 总结阶段右侧显示加载动画
- [ ] 已完成任务的功能不受影响
- [ ] 任务中途取消/删除能正确清理

### 端口
- [ ] 后端运行在 9101
- [ ] 前端运行在 9173
- [ ] 所有配置文件、文档、CORS 同步更新

### Agent 预留
- [ ] CORS 允许本地任意端口调用
- [ ] FastAPI `/docs` 页面可用且信息完整
