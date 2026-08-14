# Local Compute Capability Detection Guide (本地算力探测与模型匹配指南)

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

# AMD GPU check (ROCm)
rocm-smi

# PCI Bus Display Controller check (PCI 显卡信息识别)
lspci | grep -i 'vga\|3d\|display'
```

### macOS
```bash
# Display and GPU info for Apple Silicon / Intel Mac
system_profiler SPDisplaysDataType
```

---

## 2. VRAM Thresholds for ASR Models (显存阈值与模型推荐表)

| VRAM / Hardware | Recommended Model (推荐模型) | Speed Estimate (预测速度) | Notes / Recommendations |
|---|---|---|---|
| No GPU / < 2 GB | Cloud ASR only (MiMo / OpenAI API) | Depends on network | Local inference too slow; use cloud API |
| 2 – 4 GB | `faster-whisper` tiny / base | ~5x real-time | Suitable for basic local transcription |
| 4 – 6 GB | `faster-whisper` small / medium | ~10x real-time | Balanced accuracy and performance |
| 6 – 8 GB | `faster-whisper` large-v2 | ~8x real-time | High accuracy for multi-language ASR |
| ≥ 8 GB | `faster-whisper` large-v3 | ~12x real-time | Best accuracy & speed on modern GPUs |
| Apple Silicon (M1/M2/M3/M4) | `faster-whisper` medium (CPU/CoreML) | ~3x real-time | Unified memory acceleration |

---

## 3. Local ASR Service Endpoint Probing (本地服务端点探查)

AI agents should probe common local service endpoints to detect pre-existing LLM or ASR runtimes:

| Service (服务) | Default Endpoint (默认地址) | Probe Method (探测方式) | Expected Response |
|---|---|---|---|
| **Ollama** | `http://localhost:11434/api/tags` | GET, check status 200 | JSON list of installed models |
| **LM Studio** | `http://localhost:1234/v1/models` | GET, check status 200 | OpenAI-compatible models response |
| **FunASR WebSocket** | `ws://localhost:10095` | WebSocket handshake | Connection accepted |
| **vLLM** | `http://localhost:8000/v1/models` | GET, check status 200 | Model list JSON |
| **whisperMe (self)** | `http://localhost:9101/api/health` | GET, check status 200 | Status OK JSON |

---

## 4. Decision Flowchart (决策逻辑树)

```text
Does nvidia-smi return valid output?
├── YES → Parse VRAM → Select appropriate local model
│         ├── VRAM ≥ 4GB? → Recommend local faster-whisper (small / medium / large)
│         └── VRAM < 4GB? → Recommend cloud ASR (OpenAI / MiMo)
└── NO  → Is Apple Silicon (M1+)?
          ├── YES → Recommend CPU/CoreML-based faster-whisper (medium)
          └── NO  → Recommend Cloud ASR (CPU-only local inference is not recommended for batch processing)
```

---

## 5. Example Agent Probe Script (Agent 探测脚本示例)

Agents can run the following Python snippet to programmatically inspect the host GPU and probe active local AI service endpoints:

```python
import subprocess
import json
import urllib.request

def check_nvidia_gpu():
    """Detect NVIDIA GPU name and total/free VRAM."""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total,memory.free', '--format=csv,noheader'], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            print(f"[GPU] NVIDIA detected: {result.stdout.strip()}")
            return True
        else:
            print("[GPU] nvidia-smi ran but returned empty output.")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("[GPU] No NVIDIA GPU detected via nvidia-smi.")
    return False

def probe_local_services():
    """Probe common local LLM and ASR service endpoints."""
    endpoints = [
        ("Ollama", "http://localhost:11434/api/tags"),
        ("LM Studio", "http://localhost:1234/v1/models"),
        ("vLLM", "http://localhost:8000/v1/models"),
        ("whisperMe", "http://localhost:9101/api/health")
    ]
    
    print("\n[Endpoints] Probing local AI services:")
    for name, url in endpoints:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'whisperMe-Agent/1.0'})
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status == 200:
                    print(f"  - {name:12s}: ONLINE (port active, status 200)")
                else:
                    print(f"  - {name:12s}: HTTP {response.status}")
        except Exception:
            print(f"  - {name:12s}: offline")

if __name__ == "__main__":
    check_nvidia_gpu()
    probe_local_services()
```
