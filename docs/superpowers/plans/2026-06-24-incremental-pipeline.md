# Incremental Pipeline + Port Migration + Agent Interface Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the monolithic podcast processing pipeline into three user-visible phases (audio playback → incremental transcript → AI summary), migrate ports to avoid conflicts, and prepare CORS for future AI Agent integration.

**Architecture:** The backend pipeline in `pipeline.py` moves audio URL registration earlier (Phase 1), adds a batch callback to `transcribe_and_merge` that writes paragraphs incrementally to SQLite (Phase 2), and the frontend shows a loading animation during summarization (Phase 3). Ports migrate from 8001/5173 to 9101/9173. CORS is relaxed to allow local Agent calls.

**Tech Stack:** Python (FastAPI, faster-whisper, PyAnnote), React 19, Vite 8, SQLite WAL, Tailwind CSS

**Spec:** `docs/superpowers/specs/2026-06-24-incremental-pipeline-design.md`

**Test URLs:**
- `https://www.xiaoyuzhoufm.com/episode/6a18473eac7bdb080c324b39`
- `https://www.xiaoyuzhoufm.com/episode/693abe4b2a383da167952187`
- `https://www.xiaoyuzhoufm.com/episode/6a2c327643a22a695582d135`

---

### Task 1: Port Migration — Backend 8001 → 9101

**Files:**
- Modify: `backend/run.py:31-32,42`
- Modify: `frontend/src/constants.js:4`
- Modify: `backend/app/main.py:33,36`
- Modify: `CLAUDE.md:50-51`
- Modify: `docs/architecture.md:275-276`

- [ ] **Step 1: Update backend/run.py port**

In `backend/run.py`, change lines 31-32 and 42:

```python
# Line 31-32: change print statements
print("  * 监听地址: http://127.0.0.1:9101")
print("  * 音频下载挂载路径: http://127.0.0.1:9101/audio")

# Line 42: change port argument
"--port", "9101",
```

- [ ] **Step 2: Update frontend/src/constants.js**

```javascript
export const API_BASE = "http://127.0.0.1:9101";
```

- [ ] **Step 3: Update backend/app/main.py CORS and comment**

In `backend/app/main.py`, line 33 and 36:

```python
# 配置 CORS 跨域请求（前端 Vite 运行在 9173，后端运行在 9101）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9173", "http://127.0.0.1:9173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- [ ] **Step 4: Update CLAUDE.md port documentation**

In `CLAUDE.md`, update the port section:

```markdown
## 端口配置
- 后端: 9101
- 前端: 9173（Vite dev server）
```

- [ ] **Step 5: Update docs/architecture.md**

Fix the stale port reference (currently says 8000):

```markdown
| Backend API | 9101 | FastAPI + Uvicorn |
| Frontend Dev | 9173 | Vite dev server |
```

- [ ] **Step 6: Commit**

```bash
git add backend/run.py frontend/src/constants.js backend/app/main.py CLAUDE.md docs/architecture.md
git commit -m "chore: migrate ports — backend 8001→9101, frontend 5173→9173"
```

---

### Task 2: Port Migration — Frontend 5173 → 9173

**Files:**
- Modify: `frontend/vite.config.js`
- Modify: `backend/app/main.py:36` (CORS — already done in Task 1 Step 3)
- Modify: `backend/app/routers/boards.py:338`

- [ ] **Step 1: Update vite.config.js**

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 9173,
  },
})
```

- [ ] **Step 2: Update boards.py hardcoded frontend URL**

In `backend/app/routers/boards.py`, line 338:

```python
source_link = f"http://localhost:9173/?task_id={card['podcast_id']}&paragraph_id={card['paragraph_id']}"
```

- [ ] **Step 3: Commit**

```bash
git add frontend/vite.config.js backend/app/routers/boards.py
git commit -m "chore: migrate frontend port 5173→9173"
```

---

### Task 3: Transcriber — Extract `_find_speaker` Helper

**Files:**
- Modify: `backend/app/core/transcriber.py:386-409`

- [ ] **Step 1: Add `_find_speaker` method to PodcastTranscriber**

Insert this method before `transcribe_and_merge` (before line 281):

```python
def _find_speaker(self, seg, diarization_segments: list[dict]) -> str:
    """Match a transcript segment to the closest diarization speaker."""
    if not diarization_segments:
        return "UNKNOWN_SPEAKER"

    seg_center = (seg.start + seg.end) / 2
    best_match = None
    max_overlap = 0.0

    for d in diarization_segments:
        # Exact center containment
        if d["start"] <= seg_center <= d["end"]:
            return d["speaker"]
        # Fallback: highest overlap
        overlap_start = max(seg.start, d["start"])
        overlap_end = min(seg.end, d["end"])
        overlap_len = overlap_end - overlap_start
        if overlap_len > max_overlap:
            max_overlap = overlap_len
            best_match = d["speaker"]

    return best_match or "UNKNOWN_SPEAKER"
```

- [ ] **Step 2: Replace inline speaker matching with helper call**

In `transcribe_and_merge`, replace lines 386-409 (the `for seg in whisper_segments:` loop's speaker matching block) with:

```python
for seg in whisper_segments:
    current_speaker = self._find_speaker(seg, diarization_segments)
```

The rest of the loop body (timestamp calculation, merged_results append, progress callback) stays unchanged.

- [ ] **Step 3: Verify no behavioral change**

The `_find_speaker` method is a direct extraction of the inline logic. The `for/else` pattern in the original code (lines 394-409) is equivalent to the `best_match` fallback in the helper. Run the backend to verify no import errors:

```bash
cd backend && python -c "from app.core.transcriber import PodcastTranscriber; print('OK')"
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/core/transcriber.py
git commit -m "refactor: extract _find_speaker helper from transcribe_and_merge"
```

---

### Task 4: Transcriber — Add `on_segment_batch` Callback

**Files:**
- Modify: `backend/app/core/transcriber.py:281` (signature)
- Modify: `backend/app/core/transcriber.py:357-442` (local Whisper path)
- Modify: `backend/app/core/transcriber.py:288-316` (online ASR path)

- [ ] **Step 1: Update `transcribe_and_merge` signature**

At line 281, add the `on_segment_batch` parameter:

```python
def transcribe_and_merge(self, wav_path: str, diarization_segments: list[dict],
                         progress_callback=None, asr_mode: str = "local",
                         on_segment_batch=None) -> list[dict]:
```

- [ ] **Step 2: Refactor local Whisper path to iterate incrementally**

Replace lines 357-442 (from `whisper_segments_raw, info = model.transcribe(...)` to the end of the for loop) with:

```python
            print("✨ [LOG] Whisper 模型已就绪！开始高效转汉字...")
            whisper_segments_raw, info = model.transcribe(
                short_wav_path,
                beam_size=5,
                language="zh"
            )

            # 过滤相邻重复句，防止本地 Whisper 幻觉循环
            def clean_txt(text):
                return re.sub(r'[^\w\s]', '', text).strip()

            dedup_prev_text = ""
            duration = 1.0
            batch_buffer = []

            for seg in whisper_segments_raw:
                # Adjacent deduplication
                cleaned = clean_txt(seg.text)
                if cleaned == dedup_prev_text:
                    if merged_results:
                        merged_results[-1]["end"] = seg.end
                    continue
                dedup_prev_text = cleaned

                # Speaker matching
                current_speaker = self._find_speaker(seg, diarization_segments)

                # Timestamp
                start_min, start_sec = divmod(int(seg.start), 60)
                start_hour, start_min = divmod(start_min, 60)
                timestamp = f"[{start_hour:02d}:{start_min:02d}:{start_sec:02d}]"

                merged_seg = {
                    "start": seg.start,
                    "end": seg.end,
                    "timestamp_str": timestamp,
                    "speaker": current_speaker,
                    "text": seg.text
                }
                merged_results.append(merged_seg)
                batch_buffer.append(merged_seg)

                # Incremental batch callback every 10 segments
                if on_segment_batch and len(batch_buffer) >= 10:
                    try:
                        on_segment_batch(list(batch_buffer))
                    except Exception as batch_ex:
                        print(f"⚠️ [LOG] Incremental paragraph batch failed: {batch_ex}")
                    batch_buffer = []

                # Progress update
                if info and info.duration:
                    duration = info.duration
                current_progress = 60.0 + (seg.end / max(duration, 1.0)) * 15.0
                current_progress = min(current_progress, 75.0)
                current_progress_int = int(current_progress)
                if current_progress_int > last_progress_int:
                    last_progress_int = current_progress_int
                    if progress_callback:
                        try:
                            progress_callback(float(current_progress_int))
                        except Exception as pe:
                            print(f"⚠️ [LOG] 进度回调触发异常: {pe}")

            # Flush remaining segments
            if on_segment_batch and batch_buffer:
                try:
                    on_segment_batch(list(batch_buffer))
                except Exception as batch_ex:
                    print(f"⚠️ [LOG] Final paragraph batch failed: {batch_ex}")

            print("="*50 + f"\n🎉 [LOG] 转录与声纹角色合并工作顺利完成！共识别出 {len(merged_results)} 段对话。")
            return merged_results
```

Note: the `whisper_segments = list(whisper_segments_raw)` line is removed. The dedup, speaker matching, timestamp, and merge logic are all folded into the single `for seg in whisper_segments_raw:` loop. The variable `has_diarization` is no longer needed since `_find_speaker` handles empty diarization internally.

- [ ] **Step 3: Refactor online ASR path for batch callback**

Replace lines 318-342 (the `else:` local mode block that builds whisper_segments) and the merge loop. After the online ASR provider returns segments (line 316), the existing code builds `whisper_segments` list and then falls through to the shared merge loop at line 386. The merge loop is now handled differently for online mode.

After line 316 (`print(f"[LOG] Online ASR completed: ...")`), add the online ASR merge + batch callback logic:

```python
            # Online ASR: merge with diarization and batch callback
            batch_buffer = []
            for seg in whisper_segments:
                current_speaker = self._find_speaker(seg, diarization_segments)

                start_min, start_sec = divmod(int(seg.start), 60)
                start_hour, start_min = divmod(start_min, 60)
                timestamp = f"[{start_hour:02d}:{start_min:02d}:{start_sec:02d}]"

                merged_seg = {
                    "start": seg.start,
                    "end": seg.end,
                    "timestamp_str": timestamp,
                    "speaker": current_speaker,
                    "text": seg.text
                }
                merged_results.append(merged_seg)
                batch_buffer.append(merged_seg)

                if on_segment_batch and len(batch_buffer) >= 10:
                    try:
                        on_segment_batch(list(batch_buffer))
                    except Exception as batch_ex:
                        print(f"⚠️ [LOG] Incremental paragraph batch failed: {batch_ex}")
                    batch_buffer = []

            if on_segment_batch and batch_buffer:
                try:
                    on_segment_batch(list(batch_buffer))
                except Exception as batch_ex:
                    print(f"⚠️ [LOG] Final paragraph batch failed: {batch_ex}")

            # Progress callback for online mode
            if progress_callback:
                try:
                    progress_callback(75.0)
                except Exception:
                    pass

            print("="*50 + f"\n🎉 [LOG] 转录与声纹角色合并工作顺利完成！共识别出 {len(merged_results)} 段对话。")
            return merged_results
```

Then the local mode `else:` block should also end with its own `return merged_results` (already included in Step 2). The shared merge loop at lines 380-442 is no longer needed — remove it since both paths now handle merging internally.

- [ ] **Step 4: Verify the refactored transcriber**

```bash
cd backend && python -c "from app.core.transcriber import PodcastTranscriber; print('OK')"
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/transcriber.py
git commit -m "feat: add on_segment_batch callback for incremental transcription"
```

---

### Task 5: Pipeline — Early audio_url + Incremental Paragraphs + Resume Fix

**Files:**
- Modify: `backend/app/core/pipeline.py:58-92` (resume logic)
- Modify: `backend/app/core/pipeline.py:105-131` (audio_url registration)
- Modify: `backend/app/core/pipeline.py:140-167` (transcription + paragraph writing)

- [ ] **Step 1: Fix resume logic for incremental writes**

Replace lines 58-60:

```python
        # Step 0.8: ASR 断点续传/跳过检查
        existing_paragraphs = db.get_paragraphs_by_podcast(task_id)
        if existing_paragraphs and len(existing_paragraphs) > 0:
```

With:

```python
        # Step 0.8: ASR 断点续传/跳过检查
        # 增量写入后，转录中也会有段落。只有段落+完整transcript同时存在才跳过
        existing_paragraphs = db.get_paragraphs_by_podcast(task_id)
        has_full_transcript = bool(task.get("transcript"))
        if existing_paragraphs and len(existing_paragraphs) > 0 and has_full_transcript:
```

Add cleanup for partial paragraphs after the `else` of this block. After line 92 (the `return` statement), the normal pipeline continues. Insert a cleanup block before Step 1:

```python
        # 清理不完整的增量段落（上次转录中途崩溃留下的）
        if existing_paragraphs and len(existing_paragraphs) > 0 and not has_full_transcript:
            print(f"🧹 [LOG] 检测到 {len(existing_paragraphs)} 条残留段落（无完整转录），清理后重新开始。")
            db.delete_paragraphs_by_podcast(task_id)
```

- [ ] **Step 2: Move audio_url registration earlier**

Move lines 128-131 (audio_url registration) to right after line 119 (metadata write). The new order after the metadata write at line 119:

```python
        # 立即注册音频播放路径，让用户可以边听边等
        check_cancelled(task_id)
        audio_filename = os.path.basename(local_mp3)
        db.update_task(task_id, audio_url=f"/audio/{audio_filename}", progress=32.0)

        # Step 2: 音频格式预处理（16kHz Mono WAV）
        check_cancelled(task_id)
        db.update_task(task_id, status="transcribing", progress=40.0)
        t_preprocess_start = time.time()
        standardized_wav = downloader.preprocess_audio(local_mp3)
        timing_stats['音频预处理'] = time.time() - t_preprocess_start

        # audio_url 已在下载后立即注册，此处无需重复设置
```

Delete the old audio_url lines at 128-131 (they're now moved up).

- [ ] **Step 3: Add incremental paragraph callback to transcription step**

Replace lines 140-167 (from `# Step 4: Whisper` to the paragraph writing block) with:

```python
        # Step 4: Whisper 语音识别与时间轴交叉合并
        check_cancelled(task_id)

        def progress_callback(current_progress):
            check_cancelled(task_id)
            db.update_task(task_id, progress=current_progress)

        # 增量段落写入回调
        accumulated_segments = []

        def on_segment_batch(new_segments):
            """每 10 个段落触发一次，增量写入数据库"""
            accumulated_segments.extend(new_segments)
            try:
                paragraphs = transcriber.cluster_segments_to_paragraphs(task_id, accumulated_segments)
                db.add_paragraphs(paragraphs)
            except Exception as batch_ex:
                print(f"⚠️ [LOG] 增量段落写入失败: {batch_ex}")

        asr_mode = task.get("asr_mode", "local")
        t_transcribe_start = time.time()
        merged_transcript = transcriber.transcribe_and_merge(
            standardized_wav,
            diar_data,
            progress_callback=progress_callback,
            asr_mode=asr_mode,
            on_segment_batch=on_segment_batch
        )
        timing_stats['语音识别转录 (Whisper)'] = time.time() - t_transcribe_start
        db.update_task(task_id, transcript=merged_transcript, progress=75.0)

        # Step 4.2: 最终段落聚合（兜底，确保完整性）
        try:
            print("⏳ [LOG] 正在运行最终语义分块聚合...")
            t_chunk_start = time.time()
            paragraphs = transcriber.cluster_segments_to_paragraphs(task_id, merged_transcript)
            timing_stats['语义段落聚合'] = time.time() - t_chunk_start
            db.add_paragraphs(paragraphs)
            print(f"✅ [LOG] 成功为任务 {task_id} 聚合出 {len(paragraphs)} 个语义段落。")
        except Exception as chunk_ex:
            print(f"⚠️ [LOG 警告] 语义分块聚合失败: {chunk_ex}")
```

- [ ] **Step 4: Verify pipeline.py syntax**

```bash
cd backend && python -c "from app.core.pipeline import run_podcast_pipeline; print('OK')"
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/pipeline.py
git commit -m "feat: early audio_url + incremental paragraph writes + resume fix"
```

---

### Task 6: API — Return Paragraphs for All Task Statuses

**Files:**
- Modify: `backend/app/routers/tasks.py:136-157`

- [ ] **Step 1: Rewrite paragraph injection in get_task_details**

Replace lines 136-157:

```python
    # 注入段落（所有状态都返回，支持增量转录显示）
    try:
        paragraphs = db.get_paragraphs_by_podcast(task_id) or []

        if task.get("status") == "completed" and paragraphs:
            # 仅对已完成任务做 sedimented 检查
            podcast_cards = db.get_cards_by_podcast(task_id)
            sedimented_paragraph_ids = {c["paragraph_id"] for c in podcast_cards}
            for p in paragraphs:
                p["sedimented"] = p["id"] in sedimented_paragraph_ids

            # 旧格式兼容检查
            is_old_format = paragraphs and len(paragraphs) > 0 and (
                "sentences" not in paragraphs[0] or
                not isinstance(paragraphs[0].get("sentences"), list)
            )
            if (not paragraphs or is_old_format) and task.get("transcript"):
                paragraphs = transcriber.cluster_segments_to_paragraphs(task_id, task.get("transcript"))
                db.delete_paragraphs_by_podcast(task_id)
                db.add_paragraphs(paragraphs)

        task["paragraphs"] = paragraphs
    except Exception as e:
        print(f"⚠️ [LOG ERROR] Failed to inject paragraphs: {e}")
        task["paragraphs"] = []
```

- [ ] **Step 2: Verify tasks.py syntax**

```bash
cd backend && python -c "from app.routers.tasks import router; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/tasks.py
git commit -m "feat: return paragraphs for all task statuses (incremental display)"
```

---

### Task 7: Frontend — AI Summary Loading + Transcription Progress + Status Badge

**Files:**
- Modify: `frontend/src/views/PodcastDetailView.jsx:778` (statusMap)
- Modify: `frontend/src/views/PodcastDetailView.jsx:888-919` (transcript panel)
- Modify: `frontend/src/views/PodcastDetailView.jsx:969-978` (summary panel)

- [ ] **Step 1: Update statusMap**

At line 778, add `summarizing`:

```javascript
  const statusMap = { completed: "Completed", failed: "Failed", cancelled: "Cancelled", pending: "Queued", downloading: "Downloading", transcribing: "Transcribing", summarizing: "Summarizing" };
```

- [ ] **Step 2: Add transcription progress indicator to transcript panel**

Before the paragraphs rendering `<div className="flex flex-col gap-6">` at line 888, add:

```jsx
          {/* Transcription progress indicator */}
          {(activeTask.status === "downloading" || activeTask.status === "transcribing") && (
            <div className="flex items-center gap-2 mb-4 px-3 py-2 bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-lg">
              <div className="w-3 h-3 border-2 border-[var(--accent-red)] border-t-transparent rounded-full animate-spin" />
              <span className="text-xs text-[var(--accent-red)] font-semibold">
                {activeTask.status === "downloading"
                  ? t("正在下载音频...", "Downloading audio...")
                  : t("转录进行中...", "Transcribing...") + (paragraphs.length > 0 ? ` (${paragraphs.length} ${t("段", "paragraphs")})` : "")
                }
              </span>
            </div>
          )}
```

- [ ] **Step 3: Add AI summary loading animation**

Replace lines 969-978 (the summary sub-tab content):

```jsx
            {detailSubTab === "summary" && (
              <div className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-xl p-6 shadow-xs select-text animate-fade-in">
                <div className="flex items-center gap-2 pb-4 border-b border-[var(--border-primary)]/30 mb-5 text-[var(--accent-red)] select-none">
                  <Sparkles size={18} className="text-[var(--accent-red)]" />
                  <h3 className="text-[13px] font-extrabold uppercase tracking-widest text-[var(--text-primary)] font-display">{t("AI 价值分析报告", "AI VALUE ANALYSIS REPORT")}</h3>
                </div>

                {activeTask.status === "summarizing" ? (
                  <div className="flex flex-col items-center justify-center py-12 gap-4">
                    <div className="w-10 h-10 border-3 border-[var(--accent-red)] border-t-transparent rounded-full animate-spin" />
                    <p className="text-sm text-[var(--text-muted)] font-semibold">
                      {t("AI 正在深度分析转录文本...", "AI is analyzing the transcript...")}
                    </p>
                  </div>
                ) : activeTask.summary ? (
                  <MarkdownRenderer text={activeTask.summary} t={t} />
                ) : (
                  <div className="border-2 border-dashed border-[var(--border-primary)]/40 p-8 text-center rounded-xl select-none">
                    <span className="text-xs text-[var(--text-muted)] font-bold uppercase tracking-wider">{t("暂无总结内容", "No summary available")}</span>
                  </div>
                )}
              </div>
            )}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/PodcastDetailView.jsx
git commit -m "feat: AI summary loading animation + transcription progress indicator"
```

---

### Task 8: CORS — Relax for Agent Integration

**Files:**
- Modify: `backend/app/main.py:31-40`

- [ ] **Step 1: Update FastAPI metadata and CORS**

Replace lines 31-40:

```python
app = FastAPI(
    title="whisperMe Local Podcast Processor",
    version=CURRENT_VERSION,
    description="本地优先的播客转录与知识提炼工具。支持小宇宙、Bilibili 等平台的播客音频下载、ASR 转录、说话人识别和 AI 总结。",
)

# 配置 CORS 跨域请求
# 允许本地任意端口（前端 9173 + 未来 AI Agent 调用）
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: relax CORS for local Agent integration + add API description"
```

---

### Task 9: Functional Verification

- [ ] **Step 1: Start backend and frontend**

```bash
# Terminal 1: Backend
cd backend && python run.py

# Terminal 2: Frontend
cd frontend && npm run dev
```

Verify: backend starts on 9101, frontend on 9173.

- [ ] **Step 2: Test with first podcast URL**

Submit `https://www.xiaoyuzhoufm.com/episode/6a18473eac7bdb080c324b39` via the New Transcription modal.

Verify:
1. Audio downloads → `audio_url` set → player appears in detail view before transcription starts
2. Transcription progress indicator shows "Transcribing... (N paragraphs)"
3. Paragraphs appear incrementally in the transcript panel (check every 10-20 seconds)
4. After transcription completes, AI summary tab shows loading animation
5. Summary appears after LLM finishes

- [ ] **Step 3: Test completed tasks still work**

Open an existing completed task. Verify paragraphs, summary, audio, export all work normally.

- [ ] **Step 4: Test task deletion mid-transcription**

Start a second podcast (`https://www.xiaoyuzhoufm.com/episode/693abe4b2a383da167952187`), then delete it while transcribing. Verify cleanup succeeds.

- [ ] **Step 5: Test batch URL**

Submit the third URL (`https://www.xiaoyuzhoufm.com/episode/6a2c327643a22a695582d135`) to verify batch processing works with incremental pipeline.

- [ ] **Step 6: Verify /docs endpoint**

Open `http://127.0.0.1:9101/docs` in browser. Verify Swagger UI loads with API description.
