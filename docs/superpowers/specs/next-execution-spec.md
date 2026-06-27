# whisperMe 下一轮执行规范 — 施工图纸

**日期**: 2026-06-25  
**前置**: `code_review_report.md`（同日审计报告）  
**状态**: 待用户审批后交付执行 Agent  

---

## 〇、目标主机硬件画像

| 组件 | 规格 | 对本项目的约束含义 |
|------|------|------------------|
| CPU | AMD Ryzen 5 5600 (6C/12T, 3.50 GHz) | 12 逻辑核心 → CTranslate2 `inter_threads=4` 是甜点值；CPU 推理可开 INT8 量化 |
| RAM | 32 GB DDR4 | 充裕，Whisper large-v3 内存峰值 ~4GB，不构成瓶颈 |
| GPU | **RTX 3070 8GB GDDR6** | 8GB 显存须精打细算：pyannote (~1.5GB) + Whisper large-v3 (~3.8GB FP16 / ~2.2GB INT8) ≈ 5.3-6GB，**留 ~2GB 余量给 WDDM + OS**；`int8_float16` 是最优精度 |
| 存储 | 954 GB，已用 283 GB | 671GB 剩余空间充足；3h 音频 WAV ~600MB，无磁盘压力但应清理 `temp_sandbox` 残留 |

> **RTX 3070 8GB 的黄金推理配置**：`compute_type="int8_float16"` + `beam_size=5` + `large-v3-turbo` 模型。  
> `int8_float16` 让权重走 INT8 而 KV-Cache 走 FP16，实测可在 8GB 卡上比纯 FP16 快 30-40% 且显存占用降至 ~2.2GB，与 pyannote 共存无压力。  
> `large-v3-turbo` 对比 `large-v3` 在中文转录准确度几乎无差，但推理速度快 ~3x（CTranslate2 引擎优化 + 蒸馏模型更小）。

---

## 一、工作包索引

| # | 代号 | 标题 | 优先级 | 涉及文件数 | 预估工时 |
|---|------|------|--------|-----------|---------|
| WP-1 | Turbo Engine | RTX 3070 定制 ASR 性能极限优化 | 🔴 P0 | 4 | 2h |
| WP-2 | Pipeline Hardening | 增量流水线并发安全加固 | 🔴 P0 | 2 | 1.5h |
| WP-3 | Voiceprint Shield | 说话人声纹库健壮性加固 | 🟡 P1 | 2 | 1h |
| WP-4 | Prompt Surgeon | Prompt 模板修复与规范化 | 🟡 P1 | 1 | 0.5h |
| WP-5 | Code DRY | 三大冗余抽取（DoH、subprocess、LLM） | 🟡 P1 | 6 | 2h |
| WP-6 | Sandbox Hygiene | 临时文件清理与环境变量劫持收窄 | 🟡 P1 | 1 | 0.5h |
| WP-7 | HF Token UX | 小白友好型 HuggingFace Token 配置 | 🟡 P1 | 5 | 2h |
| WP-8 | Build Modernize | 统一版本号与全自动构建脚本 | 🟢 P2 | 3 | 1.5h |

**执行依赖关系**:
```
WP-5 (Code DRY) ─→ WP-1 (Turbo Engine)
                 ─→ WP-2 (Pipeline Hardening)
WP-6 (Sandbox)  ─→ 独立
WP-3, WP-4      ─→ 独立
WP-7 (HF Token) ─→ 独立
WP-8 (Build)    ─→ 最后执行
```

> **建议执行顺序**：WP-5 → WP-1 → WP-2 → WP-3 → WP-4 → WP-6 → WP-7 → WP-8  
> WP-5（去重）先行，因为 WP-1 和 WP-2 的改动会涉及被去重的模块，先去重可避免冲突。

---

## WP-1: Turbo Engine — RTX 3070 定制 ASR 性能极限优化

### 目标
将 3 小时播客的本地 ASR 处理时间从 **~37 分钟压缩到 ~15-20 分钟**（目标提速 50-60%）。

### 涉及文件

| 文件 | 操作 | 变更摘要 |
|------|------|---------|
| `backend/app/core/transcriber.py` | MODIFY | 精度策略 + VAD 过滤 + Whisper 参数调优 + 模型推荐 |
| `backend/app/config.py` | MODIFY | 新增 `AppConfigModel` 字段 |
| `backend/app/core/pipeline.py` | MODIFY | 跳过 WAV 预处理（Whisper 直读原始音频） |
| `backend/app/core/asr_providers/mimo.py` | MODIFY | 并发分片请求 |

---

### 变更点 1.1: 自适应精度策略（`compute_type` 智能选择）

**位置**: `transcriber.py` L220

**当前代码**:
```python
self.compute_type = "float16" if self.device == "cuda" else "float32"
```

**变更为**:  
在 `PodcastTranscriber.__init__` 中，将硬编码的 `float16` 改为 **基于 GPU 显存的自适应策略**。规则如下：

| GPU 显存 | `compute_type` | 理由 |
|----------|---------------|------|
| >= 10 GB | `float16` | 显存充裕，用 FP16 保最高精度 |
| 4-10 GB（**含 RTX 3070 8GB**） | `int8_float16` | **权重 INT8 + KV-Cache FP16，速度提升 30-40%，精度损失 <1%** |
| < 4 GB | `int8` | 显存极紧，纯 INT8 保证不 OOM |
| CPU | `int8` | CPU 上 INT8 通过 VNNI/AVX-512 加速，比 float32 快 ~3x |

**关键约束**:
- 用 `torch.cuda.mem_get_info()` 获取 **total** 显存（不是 free，因为 free 受其他进程影响）
- 在 `nvidia-smi` 检测成功后（L216-218），立即调 `torch.cuda.mem_get_info()` 一次，缓存 `total_vram_gb`
- `torch` 的 import 必须仍在此处延迟执行，**禁止提升到模块顶层**（遵守 CLAUDE.md 约束）

---

### 变更点 1.2: 默认模型推荐升级为 `large-v3-turbo`

**位置**: `transcriber.py` L409-L414

**当前 MODEL_SIZE_MAPPING**:
```python
MODEL_SIZE_MAPPING = {
    "large-v3": "Systran/faster-whisper-large-v3",
    "large-v3-turbo": "Systran/faster-whisper-large-v3-turbo",
    "medium": "Systran/faster-whisper-medium",
    "small": "Systran/faster-whisper-small",
}
```

**变更**:
- `MODEL_SIZE_MAPPING` 不变（已支持 turbo）
- `config.py` L57 的 `AppConfigModel` 中，将 `local_whisper_model_size` 的默认值从 `"large-v3"` 改为 `"large-v3-turbo"`

**理由**: `large-v3-turbo` 是 Whisper large-v3 的蒸馏版本，在 CTranslate2 引擎上推理速度约为 large-v3 的 3 倍，中文转录 WER 差距 <1%。对 RTX 3070 8GB 而言，turbo 模型显存占用约 1.5GB（INT8），留出充足空间给 pyannote。

> **已有用户若 config.json 里已写了 `"large-v3"`，Pydantic 校验不会覆盖**——这是正确的行为。仅影响全新安装的默认值。

---

### 变更点 1.3: Whisper 推理参数调优

**位置**: `transcriber.py` L427-L431

**当前代码**:
```python
whisper_segments_raw, info = model.transcribe(
    short_wav_path,
    beam_size=5,
    language="zh"
)
```

**变更为**:  
增加以下参数以提速并改善质量：

| 参数 | 当前值 | 新值 | 效果 |
|------|-------|------|------|
| `beam_size` | `5` | `5` | 不变，5 是精度-速度平衡点 |
| `vad_filter` | 未设 | `True` | **启用内置 Silero VAD，跳过静音区间推理**，预计节省 15-25% 时间 |
| `vad_parameters` | 未设 | `{"min_silence_duration_ms": 500}` | 500ms 以上静音才算间隔，避免过度切碎 |
| `language` | `"zh"` | `"zh"` | 不变 |
| `condition_on_previous_text` | 未设（默认 True） | `True` | 保持上下文连贯 |
| `no_speech_threshold` | 未设 | `0.6` | 默认值，无变化 |

**关键约束**:
- `vad_filter=True` 会让 `faster-whisper` 使用 Silero VAD 模型（~2MB，首次自动下载）。这个 VAD 在**推理内部**运行，与 pyannote 的外部 VAD 不冲突——两者作用域不同：pyannote VAD 决定"谁在说话"（说话人分割），Whisper 内置 VAD 决定"哪些帧值得解码"（静音跳过）
- Silero VAD 不需要 GPU，运行在 CPU 上，不占显存

---

### 变更点 1.4: 跳过冗余 WAV 预处理（Whisper 直读原始音频）

**位置**: `pipeline.py` L127-L138

**当前流程**:
```
下载 MP3 → FFmpeg 转 16kHz WAV (~600MB) → pyannote 读 WAV → Whisper 读 WAV
```

**新流程**:
```
下载 MP3 → FFmpeg 转 16kHz WAV → pyannote 读 WAV → Whisper 直读原始 MP3
                                                     ↑ 不再需要 WAV
```

**变更细节**:
1. `pipeline.py` 中，将 `transcriber.transcribe_and_merge()` 的第一个参数从 `standardized_wav` 改为 `local_mp3`（原始下载的 MP3/M4A 文件路径）
2. `transcriber.py` 的 `transcribe_and_merge` 方法内部，`short_wav_path = get_short_path_name(os.path.abspath(wav_path))` 这行逻辑不变——只是传入的路径从 WAV 变成了 MP3
3. `faster-whisper` 的 `model.transcribe()` 内部使用 FFmpeg 解码器，**原生支持 MP3/M4A/FLAC/OGG 等压缩格式**，无需预转 WAV

**收益**:
- 省去 10-30s 的 FFmpeg WAV 转换时间
- 省去 ~600MB 的磁盘临时文件（`temp_sandbox` 不再产生超大 WAV）
- 总体提速 ~10-15%

**关键约束**:
- pyannote 的 `run_diarization()` 和 `extract_speaker_embeddings()` **仍然需要 WAV 输入**（pyannote 依赖 `torchaudio` 加载，对压缩格式支持不稳定）。所以 WAV 预处理步骤**保留**，但只给 pyannote 用
- `standardized_wav` 的清理时间可以**提前**到声纹分割和声纹提取完成后、Whisper 转录之前，即 pipeline.py L186 之后（当前在 L248）

**提前清理 WAV 的新位置**:
在 Step 4.5（声纹提取）完成之后、Step 5（AI 总结）之前，将 WAV 清理逻辑从 L247-L253 **上移**到 L186 之后：
```
Step 3: pyannote 分割 ← 用 WAV
Step 4: Whisper 转录  ← 改为用原始 MP3
Step 4.5: 声纹提取    ← 用 WAV
→ 立即清理 WAV ← 新位置（提前释放 ~600MB）
Step 5: AI 总结       ← 不用音频
```

---

### 变更点 1.5: MiMo 在线 ASR 并发分片

**位置**: `mimo.py` L36-L113

**当前**: 60s 分片，串行 HTTP 请求。3 小时 = 180 次串行。

**变更**:
1. `chunk_length` 从 `60.0` 改为 `120.0`（MiMo API 支持更长音频，减少请求次数一半）
2. 引入 `concurrent.futures.ThreadPoolExecutor` 并发请求，**最大并发数 = 4**（防止 API 限流）
3. 回调 `progress_callback` 在线程安全方式下更新进度

**并发策略**:
```
分片编号:  [1] [2] [3] [4] [5] [6] [7] [8] ...
Worker-0:  [1]         [5]         [9]
Worker-1:      [2]         [6]          [10]
Worker-2:          [3]         [7]
Worker-3:              [4]         [8]
```

**关键约束**:
- 各 Worker 的返回结果必须按分片编号**排序后再合并**（`sorted(results, key=lambda x: x[0])`），否则时间轴会错乱
- 需要用 `threading.Lock` 保护 `all_segments` 列表和 `progress` 更新
- 如果某个分片失败，允许重试 1 次后 raise（不静默吞错）
- `_send_request` 方法不变（每个线程独享 `httpx.Client` 实例）

---

### 变更点 1.6: CTranslate2 CPU 多线程参数（仅 CPU fallback 时生效）

**位置**: `transcriber.py` L177-L191（ModelCacheManager.get_model）

**当前**: `WhisperModel(model_path_or_size, device=device, compute_type=compute_type)`

**变更**: 当 `device == "cpu"` 时，增加 CTranslate2 的线程参数：

| 参数 | 值 | 含义 |
|------|---|------|
| `cpu_threads` | `6` | R5 5600 的物理核心数，每个推理实例用 6 线程 |
| `num_workers` | `1` | 保持单 worker（因为只有一个推理任务） |

当 `device == "cuda"` 时，不添加这些参数（GPU 推理由 CUDA 自行管理线程）。

---

### 本工作包验证标准

- [ ] `nvidia-smi` + RTX 3070 → `compute_type` 自动选为 `int8_float16`
- [ ] 提交 1 小时测试播客 URL，对比优化前后的 `timing_stats['语音识别转录']` 耗时
- [ ] 目标：**本地 Whisper 阶段耗时下降 >= 40%**
- [ ] MiMo 在线模式提交 2 小时播客，对比串行 vs 并发耗时
- [ ] 目标：**在线 ASR 阶段耗时下降 >= 60%**
- [ ] `temp_sandbox/` 不再产生超大 standardized WAV 残留（WAV 在 pyannote 用完后立即清理）

---

## WP-2: Pipeline Hardening — 增量流水线并发安全加固

### 目标
修复 Code Review 中发现的 3 个并发安全与逻辑漏洞。

### 涉及文件

| 文件 | 操作 | 变更摘要 |
|------|------|---------|
| `backend/app/core/pipeline.py` | MODIFY | on_segment_batch 纯增量化 + t_rename_start 修复 |
| `backend/app/database.py` | MODIFY | 新增 update_task_field 轻量更新方法 |

---

### 变更点 2.1: `on_segment_batch` 改为纯增量写入

**位置**: `pipeline.py` L154-L164

**当前行为**:  
每次回调都 `accumulated_segments.extend(new_segments)`，然后对**全量** `accumulated_segments` 调用 `cluster_segments_to_paragraphs` 并 `INSERT OR REPLACE`。当段落达到 1500 条时，每次回调写 1500 行 SQL。

**新行为**:
回调只处理 `new_segments` 的增量段落。引入一个 `paragraph_offset` 计数器跟踪已持久化的段落数，作为新段落 ID 的起始偏移量传给 `cluster_segments_to_paragraphs`：

```
回调第 1 次: new_segments=[seg_1..seg_10]  → 生成 paragraph p0..p2, 写入 3 条 SQL
回调第 2 次: new_segments=[seg_11..seg_20] → 生成 paragraph p3..p5, 写入 3 条 SQL（ID 从 p3 开始）
...
最终兜底:   对全量 merged_transcript 做一次完整聚类，覆盖/修正所有段落
```

**关键变更细节**:
1. `cluster_segments_to_paragraphs` 需要新增一个**可选参数** `id_offset: int = 0`，用于生成段落 ID 时跳过已有的段落。当前段落 ID 格式是 `f"{podcast_id}-p{idx}"`，新增 offset 后变为 `f"{podcast_id}-p{id_offset + idx}"`
2. `on_segment_batch` 闭包中用 `paragraph_count` 变量追踪已写入的段落数
3. 最终兜底写入（L178-L185）保持不变——它用全量数据做一次完整聚类，`INSERT OR REPLACE` 会自动覆盖增量写入的中间结果

---

### 变更点 2.2: `update_task_field` 轻量级字段更新

**位置**: `database.py` 新增方法

在 `LocalDatabase` 类中新增方法 `update_task_field`：

**用途**: 替代 `update_task` 中对 `progress`、`status` 等高频轻量字段的更新。避免每次 progress 更新都要 SELECT 整行（含 MB 级 transcript JSON）再 INSERT OR REPLACE。

**方法签名**: `def update_task_field(self, task_id: str, **kwargs) -> None`

**内部逻辑**:
1. `with self.write_lock:`
2. 构建 `UPDATE tasks SET field1=?, field2=?, updated_at=? WHERE id=?`
3. 对 dict/list 类型的 value 做 `json.dumps`，标量类型直接传入
4. `self.conn.execute(sql, values)` + `self.conn.commit()`

**调用方迁移**: `pipeline.py` 中的 `progress_callback` 函数：
```python
def progress_callback(current_progress):
    check_cancelled(task_id)
    db.update_task_field(task_id, progress=current_progress)  # 轻量级
```

其他需要更新完整任务数据的场景（如写入 `transcript`、`speaker_mappings`）仍使用 `update_task`。

**关键约束**:
- `update_task_field` 只做 `UPDATE ... SET`，**不做 SELECT**
- 必须在 `write_lock` 内执行
- `updated_at` 自动设为 `datetime.now().isoformat()`

---

### 变更点 2.3: `t_rename_start` 初始化位置修复

**位置**: `pipeline.py` L232-L238

**Bug**: 如果 `extract_speaker_embeddings`（L191）抛异常跳入 `except`（L234），`t_rename_start`（L232）尚未赋值，导致 `NameError`。

**修复**: 将 `t_rename_start = time.time()` 上移到 `try` 块的**第一行**（L189 之后），与 `t_diarization_start` 等计时器初始化方式保持一致。

同时将 `except` 块中的 `timing_stats['发言人智能推断'] = time.time() - t_rename_start` 也包在 `try` 内防止二次异常：
```python
except Exception as emb_ex:
    if 't_rename_start' in dir():  # 防御性检查
        timing_stats['发言人智能推断'] = time.time() - t_rename_start
```

更优做法：直接在 `try` 块首行初始化，保证变量一定存在。

---

### 本工作包验证标准

- [ ] 提交 3 小时播客，在 `on_segment_batch` 回调中打印每次写入的 SQL 条数，确认为 3-5 条（非全量 1500 条）
- [ ] `progress_callback` 调用 `update_task_field` 后，SQLite WAL 日志大小不再随 progress 更新而膨胀
- [ ] 在 `extract_speaker_embeddings` 中人为制造异常（如无 HF_TOKEN），确认不会触发 `NameError`

---

## WP-3: Voiceprint Shield — 说话人声纹库健壮性加固

### 涉及文件

| 文件 | 操作 | 变更摘要 |
|------|------|---------|
| `backend/app/database.py` L828-L830 | MODIFY | merge_speakers 维度校验 |
| `backend/app/core/speaker.py` L66-L72 | MODIFY | 动态阈值双级门控 |

---

### 变更点 3.1: `merge_speakers` 向量维度校验

**位置**: `database.py` L828-L830

在 `zip(src_emb, tgt_emb)` 之前添加维度检查：
- 若 `len(src_emb) != len(tgt_emb)`，不执行合并，返回 `False` 并 print 警告
- 防止 `zip` 静默截断较长向量产生错误的合并结果

---

### 变更点 3.2: 动态阈值双级门控

**位置**: `speaker.py` L66-L72

**当前行为**: 只要 `max_sim >= threshold` 就匹配成功并 `sample_count += 1`。

**新行为**: 引入"高置信度门槛"和"普通匹配门槛"两级策略：

| 相似度范围 | 行为 |
|-----------|------|
| `max_sim >= 0.85` | 高置信匹配 → `sample_count += 1`（增信任） |
| `threshold <= max_sim < 0.85` | 普通匹配 → `sample_count` 不变（匹配但不增加信任） |
| `max_sim < threshold` | 不匹配 |

这样只有高置信度的匹配才会降低未来阈值（通过 `sample_count` 增长），避免低质量匹配导致阈值"正反馈退化环"。

**关键约束**: `0.85` 不应硬编码，定义为模块级常量 `HIGH_CONFIDENCE_THRESHOLD = 0.85`，便于后续调参。

---

### 本工作包验证标准

- [ ] 单元测试：构造 256 维和 512 维 embedding，调用 `merge_speakers`，应返回 `False`
- [ ] 单元测试：构造 sim=0.82 的匹配（高于 threshold 0.80 但低于 0.85），验证 sample_count 不递增

---

## WP-4: Prompt Surgeon — Prompt 模板修复与规范化

### 涉及文件

| 文件 | 操作 | 变更摘要 |
|------|------|---------|
| `backend/app/core/summarizer.py` | MODIFY | 3 处修复 |

---

### 变更点 4.1: `overlap_lines` 默认值统一为 15

**位置**: `summarizer.py` L98

将方法签名从 `overlap_lines: int = 20` 改为 `overlap_lines: int = 15`，与 CLAUDE.md 文档和实际调用处保持一致。

---

### 变更点 4.2: 删除 `{{PODCAST_DATA}}` 残留检查死代码

**位置**: summarizer.py 中的 `if "{{PODCAST_DATA}}" in chunk_prompt: pass` 块

这段代码是空操作（`pass`），既不检测替换失败也不抛警告。直接删除。

---

### 变更点 4.3: 合并阶段 Prompt 可定制化（可选/低优先级）

当前合并阶段的 `merge_prompt` 是硬编码中文字符串。如需支持用户自定义，在 `prompt.json` 中新增一个 `merge_system_prompt` 字段。但鉴于合并逻辑较固定，此变更**标记为可选**，不阻塞其他工作包。

---

### 本工作包验证标准

- [ ] 不传 `overlap_lines` 参数直接调用 `_split_transcript_into_chunks`，确认使用 15 行重叠
- [ ] grep 确认无残留 `{{PODCAST_DATA}}` 空检查代码

---

## WP-5: Code DRY — 三大冗余抽取

### 目标
提取 3 套重复代码为共享模块，减少维护成本。

### 涉及文件

| 文件 | 操作 | 变更摘要 |
|------|------|---------|
| `backend/app/core/network.py` | **[NEW]** | 统一 DoH/DNS 绕过模块 |
| `backend/app/core/compat.py` | **[NEW]** | subprocess 猴子补丁 + 平台兼容层 |
| `backend/app/core/transcriber.py` | MODIFY | 删除内联 DoH 代码和 subprocess 补丁，改为 import |
| `backend/app/core/summarizer.py` | MODIFY | 同上 |
| `backend/app/core/downloader.py` | MODIFY | 同上 |
| `backend/app/core/transcriber.py` L4 | MODIFY | 删除重复的 `import sys` |

---

### 变更点 5.1: `network.py` — 统一 DoH DNS 绕过

**新文件路径**: `backend/app/core/network.py`

**提取来源**: 
- `transcriber.py` L34-L116（`resolve_host_via_doh` + `doh_dns_bypass` context manager）
- `summarizer.py` L9-L91（同样的 DoH 逻辑）
- `downloader.py` 中的独立 DoH 实现

**导出内容**:
```
resolve_host_via_doh(hostname: str) -> str | None
doh_dns_bypass(url: str)  # context manager
```

**迁移规则**: 原文件删除内联实现，改为 `from app.core.network import doh_dns_bypass`

---

### 变更点 5.2: `compat.py` — subprocess 猴子补丁统一

**新文件路径**: `backend/app/core/compat.py`

**提取来源**:
- `transcriber.py` L6-L18
- `downloader.py` L13-L18

**导出内容**: 
```
patch_subprocess_no_window()  # 一次性调用，全局生效
```

**调用位置**: 在 `backend/app/main.py` 的顶层 import 后调用一次。各子模块不再重复打补丁。

---

### 变更点 5.3: `import sys` 去重

**位置**: `transcriber.py` L2-L4

删除 L4 的重复 `import sys`。

---

### 本工作包验证标准

- [ ] `grep -rn "resolve_host_via_doh\|doh_dns_bypass" backend/app/core/` 只命中 `network.py` 和各文件的 `from app.core.network import`
- [ ] `grep -rn "_patched_run\|_original_run" backend/app/core/` 只命中 `compat.py`
- [ ] 所有模块 import 成功：`python -c "from app.core.transcriber import PodcastTranscriber; from app.core.summarizer import PodcastSummarizer; print('OK')"`

---

## WP-6: Sandbox Hygiene — 临时文件清理与环境变量劫持收窄

### 涉及文件

| 文件 | 操作 | 变更摘要 |
|------|------|---------|
| `backend/app/config.py` L196-L200 | MODIFY | 缩小环境变量覆盖范围 |

---

### 变更点 6.1: 环境变量劫持范围收窄

**位置**: `config.py` L196-L200

**当前代码**（Windows 分支）:
```python
for env_key in ["TEMP", "TMP", "USERPROFILE", "HOMEPATH", "APPDATA", "LOCALAPPDATA"]:
    os.environ[env_key] = SHORT_TEMP_DIR
os.environ["HOME"] = SHORT_TEMP_DIR
```

**变更为**:  
只覆盖 `TEMP` 和 `TMP`，不再劫持 `USERPROFILE` / `HOMEPATH` / `APPDATA` / `LOCALAPPDATA` / `HOME`：

```python
# 只重定向临时目录，不劫持系统用户目录
for env_key in ["TEMP", "TMP"]:
    os.environ[env_key] = SHORT_TEMP_DIR
```

**理由**:
- 劫持 `USERPROFILE` 导致 `.matplotlib`、`.cache`、`NVIDIA`、`torch` 等缓存全部写入 `temp_sandbox/`（Review 已确认 177MB 残留的来源）
- 劫持 `APPDATA` 会影响 pip、git、浏览器等所有工具的配置目录
- Hugging Face 的缓存目录已通过 `HF_HOME`、`HF_HUB_CACHE` 独立控制，不需要劫持 `HOME`
- pyannote 和 faster-whisper 的中文路径问题仅影响 **模型加载路径**，已通过 `get_short_path_name` 转换解决

**关键约束**:
- 修改后需测试 pyannote 模型加载（确认它不依赖 `USERPROFILE` 查找缓存）
- 如果发现某个库确实依赖 `HOME` 或 `APPDATA` 做模型缓存，可以**只对那个特定环境变量**单独设置，而非全部劫持

---

### 变更点 6.2: 临时文件手动清理脚本

在项目根目录新增 `clean_temp.bat`（Windows）：

```batch
@echo off
echo Cleaning temp_sandbox...
del /q temp_sandbox\*.wav 2>nul
del /q temp_sandbox\*.m4a 2>nul
del /q temp_sandbox\*.mp3 2>nul
rd /s /q temp_sandbox\.cache 2>nul
rd /s /q temp_sandbox\.matplotlib 2>nul
rd /s /q temp_sandbox\NVIDIA 2>nul
rd /s /q temp_sandbox\torch 2>nul
echo Done!
```

---

### 本工作包验证标准

- [ ] 启动后端，`temp_sandbox/` 下**不再**出现 `.matplotlib`、`.cache`、`NVIDIA`、`torch` 目录
- [ ] pyannote 模型加载正常（`run_diarization` 不报错）
- [ ] Whisper 模型加载正常

---

## WP-7: HF Token UX — 小白友好型 HuggingFace Token 配置

### 目标
让完全不懂 Python 和环境变量的用户也能在 **30 秒内** 完成 Hugging Face Token 配置，全程在 Web 界面操作，零命令行。

### 当前痛点分析

1. **Token 在 `config.json` 的 `hf_token` 字段**——用户必须知道打开 JSON 文件手动编辑
2. **前端设置页面无 HF Token 输入框**——用户看不到这个配置项
3. **Token 无效时报错不友好**——只在后端日志打印"检测到未配置或无效的 Hugging Face Token"，前端无提示
4. **用户不知道去哪申请 Token**——没有引导链接

### 设计方案

#### 7.1 前端：设置页面新增 "HuggingFace Token" 区块

**位置**: 前端设置页面（Settings View），在"本地 Whisper 模型"区块下方新增一个独立 Section。

**UI 布局**:

```
+--------------------------------------------------+
| HuggingFace 声纹模型令牌                            |
+--------------------------------------------------+
|                                                  |
|  Token     [••••••••••••••••••••]  [eye] [保存]    |
|                                                  |
|  状态：  ✅ Token 有效（已验证）                     |
|          或                                       |
|          ❌ Token 无效 — 将跳过声纹识别功能            |
|          或                                       |
|          ⚠️ 未配置 — 声纹识别功能不可用               |
|                                                  |
|  该 Token 用于下载 pyannote 声纹分析模型。           |
|  无 Token 不影响基础转录功能，仅跳过说话人识别。       |
|                                                  |
|  如何获取 Token？                                  |
|     1. 访问 huggingface.co/settings/tokens        |
|     2. 创建一个新 Token（Read 权限即可）              |
|     3. 访问以下模型页面并接受使用协议：               |
|        - pyannote/speaker-diarization-3.1          |
|        - pyannote/segmentation-3.0                 |
|     4. 将 Token 粘贴到上方输入框                    |
|                                                  |
+--------------------------------------------------+
```

**交互行为**:
- 输入框默认 `type="password"`，点击眼睛图标切换明文显示
- 点击"保存"时发起 `PUT /api/settings` 请求更新 `config.json`（复用已有的设置保存 API）
- 保存成功后立即调用新 API `GET /api/settings/hf-token-status` 验证 Token 有效性
- Token 验证结果以状态徽章形式显示（绿/红/黄）

#### 7.2 后端：新增 Token 验证 API

**新增端点**: `GET /api/settings/hf-token-status`

**位置**: 新增到 `backend/app/routers/settings.py` 中

**逻辑**:
1. 从 `config.json` 读取 `hf_token`
2. 如果为空或长度 < 30 → 返回 `{"status": "missing", "message": "未配置"}`
3. 否则，尝试向 HuggingFace API 发一个轻量级验证请求：
   ```
   GET https://hf-mirror.com/api/whoami-v2
   Authorization: Bearer {token}
   ```
4. 如果返回 200 → `{"status": "valid", "username": "xxx"}`
5. 如果返回 401 → `{"status": "invalid", "message": "Token 无效或已过期"}`
6. 如果网络异常 → `{"status": "unknown", "message": "无法验证（网络异常），但 Token 格式正确"}`

**关键约束**:
- 使用 `hf-mirror.com`（中国镜像）而非 `huggingface.co`（被墙）
- 超时设为 10s
- 该 API **不缓存**结果，每次调用实时验证
- 验证请求使用 `trust_env=True`（走系统代理）

#### 7.3 前端：首次启动引导（可选增强）

如果检测到 `hf_token` 为空且用户从未配置过：
- 在首页任务列表顶部显示一个**可关闭的黄色提示横幅**：
  ```
  ⚠️ 尚未配置声纹识别 Token。前往设置页面配置 HuggingFace Token 以启用说话人自动识别功能。 [前往设置] [暂不配置]
  ```
- 点击"暂不配置"后，横幅不再显示（通过 `localStorage.setItem("hf_token_dismissed", "true")` 持久化）
- 点击"前往设置"跳转到设置页面并自动滚动到 HF Token 区块

#### 7.4 后端：pyannote 降级提示增强

**位置**: `transcriber.py` L231-L233

当前降级日志：
```python
print("⚠️ [LOG 严重警告] 检测到未配置或无效的 Hugging Face Token...")
```

**变更**: 在降级时，**将降级信息写入 task 的 metadata**，让前端能展示给用户：
```python
db.update_task_field(task_id, hf_token_missing=True)
```

前端在任务详情页检测到 `hf_token_missing=True` 时，在转录面板顶部显示：
```
ℹ️ 本次转录未启用说话人识别（HuggingFace Token 未配置）。前往设置页面配置以获得更好体验。
```

---

### 涉及文件汇总

| 文件 | 操作 | 变更摘要 |
|------|------|---------|
| 前端设置页面组件 | MODIFY | 新增 HF Token 输入区块 + 验证状态展示 |
| 前端首页组件 | MODIFY | 首次启动引导横幅（可选） |
| 前端任务详情页 | MODIFY | hf_token_missing 提示（可选） |
| `backend/app/routers/settings.py` | MODIFY | 新增 `GET /api/settings/hf-token-status` |
| `backend/app/core/transcriber.py` | MODIFY | 降级时写入 task metadata |

### 本工作包验证标准

- [ ] 设置页面能看到 HF Token 输入框
- [ ] 输入正确 Token → 保存 → 绿色 "✅ 有效" 徽章
- [ ] 输入错误 Token → 保存 → 红色 "❌ 无效" 徽章
- [ ] Token 为空 → 黄色 "⚠️ 未配置" 徽章
- [ ] 无 Token 时提交任务 → 转录正常完成（跳过声纹）→ 任务详情页显示提示信息

---

## WP-8: Build Modernize — 统一版本号与全自动构建脚本

### 涉及文件

| 文件 | 操作 | 变更摘要 |
|------|------|---------|
| `VERSION` | **[NEW]** | 单一版本源文件 |
| `backend/app/config.py` L261 | MODIFY | `CURRENT_VERSION` 改为读取 `VERSION` 文件 |
| `build.py` | MODIFY | 读取 `VERSION`、自动打 zip |

---

### 变更点 8.1: 统一版本号

在项目根目录创建 `VERSION` 纯文本文件，内容为当前版本号（如 `1.4.0`）。

`config.py` 中:
```python
CURRENT_VERSION = (PROJECT_DIR / "VERSION").read_text(encoding="utf-8").strip()
```

`build.py` 中也读同一个文件生成 zip 文件名。

---

### 变更点 8.2: 构建脚本自动化增强

在 `build.py` 的 `main()` 中增加两个自动化步骤：
1. **`create_zip(version)`**: 自动将 `release/whisperMe` 目录打包为 `release/whisperMe-Windows-x64-v{version}.zip`
2. **`print_summary()`**: 构建完成后打印清单（文件数、总大小、版本号）

---

### 本工作包验证标准

- [ ] `python build.py` 一键执行完毕，`release/` 下自动生成带版本号的 zip
- [ ] `config.py` 中 `CURRENT_VERSION` 与 `VERSION` 文件内容一致
- [ ] 前端设置页面的版本号显示正确

---

## 附录 A：RTX 3070 8GB 显存时序图

```
阶段              GPU 显存占用         备注
----------------------------------------------------
启动              0 MB                 模型懒加载
|
+- pyannote 加载   ~1.5 GB              speaker-diarization-3.1
+- 声纹分割执行    ~1.5 GB (峰值 ~2GB)   处理中
+- pyannote 保留   ~1.5 GB              等待声纹提取
|
+- Whisper 加载    +2.2 GB (INT8_FP16)  large-v3-turbo
|                  --------
|                  ~3.7 GB 总计
|                  剩余 ~4.3 GB ✅
|
+- Whisper 推理    ~3.7-4.5 GB (峰值)    beam_size=5
|                  剩余 ~3.5 GB ✅
|
+- 声纹提取       ~1.5 GB               pyannote/embedding
|                  (Whisper 已缓存)
|                  --------
|                  ~3.7 GB 总计 ✅
|
+- 模型闲置超时    → 0 MB               ModelCacheManager 自动释放
```

> RTX 3070 8GB 下 pyannote + Whisper(INT8_FP16) 共存峰值约 4.5GB，**远低于 8GB 上限**。即使 WDDM 预留 ~500MB，仍有 3GB 余量，不会触发 GPU 分页交换。

---

## 附录 B：各工作包预期性能收益

| 工作包 | 优化措施 | 预期加速 | 影响范围 |
|--------|---------|---------|---------|
| WP-1.1 | `int8_float16` 精度 | **30-40%** | 本地 Whisper |
| WP-1.2 | `large-v3-turbo` 模型（新安装） | **200-300%** | 本地 Whisper |
| WP-1.3 | `vad_filter=True` | **15-25%** | 本地 Whisper |
| WP-1.4 | 跳过 WAV 预处理 | **10-15%** | 全流程 |
| WP-1.5 | MiMo 并发 4 路 | **200-300%** | 在线 ASR |
| WP-2.1 | 增量段落纯增量写 | DB 写入量 **减少 95%** | SQLite I/O |
| WP-2.2 | `update_task_field` | 单次 update **减少 90%** | SQLite I/O |

**综合估算**（本地模式，RTX 3070，3h 播客）:
- 优化前：~37 分钟
- 仅 WP-1.1（int8_float16）：~24 分钟
- WP-1.1 + WP-1.3（VAD）：~19 分钟
- WP-1.1 + WP-1.3 + WP-1.4（跳过 WAV）：~16-17 分钟
- 若切换到 large-v3-turbo：**~8-12 分钟**（最激进估算）

---

## 附录 C：RTX 3070 最适配模型搭配方案

### 推荐配置（黄金搭档）

| 组件 | 推荐模型 | 显存占用 | 替代选项 |
|------|---------|---------|---------|
| **ASR 引擎** | `Systran/faster-whisper-large-v3-turbo` | ~2.2GB (INT8_FP16) | `large-v3`（更准但 3x 慢） |
| **声纹分割** | `pyannote/speaker-diarization-3.1` | ~1.5GB | 无替代 |
| **声纹提取** | `pyannote/wespeaker-voxceleb-resnet34-LM` | ~0.3GB | 已是最优 |
| **推理精度** | `int8_float16` | — | `float16`（更准但显存多 60%） |

### 不推荐的配置

| 配置 | 原因 |
|------|------|
| `large-v3` + `float16` | 3.8GB + 1.5GB = 5.3GB，虽能跑但余量仅 2.7GB，长音频峰值可能触发 WDDM 分页 |
| `beam_size > 5` | 显存线性增长，8GB 卡上 beam_size=8 可能 OOM |
| 多 Worker 并行推理 | 单 GPU 无法并行推理，且 pyannote 和 Whisper 共享显存 |

---

> **本文档仅作技术架构指导，不包含实现代码。请交由执行 Agent 按工作包顺序逐一实施。**
