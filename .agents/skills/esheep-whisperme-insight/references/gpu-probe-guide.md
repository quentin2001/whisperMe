# Local Compute Capability Detection & ASR Model Matching Guide (本地算力探测与模型匹配指南)

This guide provides practical detection commands, VRAM thresholds, endpoint probing methods, and decision logic for AI agents to assess local GPU and compute capabilities for running Automatic Speech Recognition (ASR) models.

---

## 1. GPU Detection Commands (GPU 探测命令)

### Windows
```bash
# NVIDIA GPU check (Primary)
nvidia-smi

# Fallback 1: WMI query (Cmd / PowerShell)
wmic path win32_VideoController get Name,AdapterRAM,DriverVersion

# Fallback 2: PowerShell CIM instance query
Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion
```

### Linux
```bash
# NVIDIA GPU check
nvidia-smi

# AMD GPU check
rocm-smi

# PCI Bus Display Controller check
lspci | grep -i 'vga\|3d\|display'
```

### macOS
```bash
# Display and GPU info for Apple Silicon / Intel Mac
system_profiler SPDisplaysDataType
```

---

## 2. VRAM Thresholds & Local ASR Model Recommendations (显存阈值与模型推荐表)

| VRAM / Hardware | Recommended Local Model (推荐本地方案) | Speed Estimate (预测速度) | Notes / Recommendations |
|---|---|---|---|
| No GPU / < 2 GB | FunASR (CPU mode) or Cloud ASR | Depends on network/CPU | CPU inference acceptable for short audio; Cloud ASR recommended for long audio |
| 2 – 4 GB | **FunASR** (SenseVoice-Small / Paraformer) | ~8x real-time | Excellent Chinese accuracy with low VRAM footprint |
| 4 – 6 GB | **FunASR** (Paraformer-large) / `faster-whisper` small | ~12x real-time | Balanced accuracy & speed for Chinese/English ASR |
| 6 – 8 GB | **FunASR** / `faster-whisper` large-v2 | ~15x real-time | High accuracy for multi-speaker / multi-language ASR |
| ≥ 8 GB | **FunASR** (SenseVoice / Paraformer) / `faster-whisper` large-v3 | ~20x real-time | Top accuracy & fastest local throughput |
| Apple Silicon (M1/M2/M3/M4) | **FunASR** / `faster-whisper` (CoreML / MPS) | ~6x real-time | Unified memory acceleration |

---

## 3. Local ASR Service Endpoint Probing (本地服务端点探查)

AI agents should probe common local service endpoints to detect pre-existing runtimes:

| Service (服务) | Default Endpoint (默认地址) | Probe Method (探测方式) | Expected Response |
|---|---|---|---|
| **FunASR WebSocket/HTTP** | `ws://localhost:10095` or `http://localhost:10095` | HTTP/WS check | Connection accepted |
| **whisperMe (self)** | `http://localhost:9101/api/health` | GET, check status 200 | Status OK JSON |
| **Ollama** | `http://localhost:11434/api/tags` | GET, check status 200 | JSON list of installed models |
| **LM Studio** | `http://localhost:1234/v1/models` | GET, check status 200 | OpenAI-compatible models response |

---

## 4. Decision Flowchart (决策逻辑树)

```text
Does nvidia-smi / GPU detection return valid GPU info?
├── YES → Parse VRAM → Recommend optimal local ASR engine
│         ├── VRAM ≥ 4GB? → Recommend local FunASR (SenseVoice / Paraformer) or faster-whisper
│         └── VRAM < 4GB? → Recommend FunASR (small mode) or Cloud ASR
└── NO  → Is Apple Silicon (M1+)?
          ├── YES → Recommend MPS/CoreML-accelerated FunASR or faster-whisper
          └── NO  → Present Choice: FunASR (CPU mode) vs Cloud API ASR
```
