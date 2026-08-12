# whisperMe AI Agent Developer & Deployment Guide

This guide is written for AI Agents (Cursor, Antigravity, Claude Desktop, AutoGPT, etc.) to automatically inspect, deploy, configure local AI models, and control whisperMe.

---

## 1. Quick Start for Agents

### Check System Status
```bash
python scripts/whisperme-cli.py status --json
```

### Start Server
```bash
# Windows
start.bat
# macOS / Linux
bash start.sh
# or directly via python
python scripts/launcher.py --foreground
```
The server will run on `http://127.0.0.1:9101`.

---

## 2. Local Models Auto-Discovery & Configuration

whisperMe provides a dedicated auto-discovery API endpoint for local LLMs and local Speech-to-Text (ASR) models.

### Auto-Detect Installed Local Models
```bash
curl -s http://127.0.0.1:9101/api/system/detect-models
```
**Sample Response**:
```json
{
  "llm": {
    "service_running": true,
    "detected_models": ["qwen2.5:7b-instruct", "llama3:8b"],
    "ollama_url": "http://localhost:11434",
    "current_model": "qwen2.5:7b-instruct"
  },
  "asr": {
    "detected_paths": ["E:/Projects/whisperMe/models/funasr"],
    "current_path": "E:/Projects/whisperMe/models/funasr"
  }
}
```

### Configure Local Modes via API
To switch whisperMe to use **local ASR** (Whisper/FunASR) and **local LLM** (Ollama / LM Studio):

```bash
curl -X POST http://127.0.0.1:9101/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "asr_mode": "local",
    "local_whisper_model_path": "E:/Projects/whisperMe/models/funasr",
    "summary_mode": "local",
    "ollama_url": "http://localhost:11434",
    "ollama_model": "qwen2.5:7b-instruct"
  }'
```

---

## 3. Programmatic CLI Control

Agent can control tasks without a browser using `scripts/whisperme-cli.py`:

```bash
# Transcribe a Podcast URL or local audio file
python scripts/whisperme-cli.py transcribe "https://www.xiaoyuzhoufm.com/episode/xxx" --json

# List recent tasks
python scripts/whisperme-cli.py list --json

# Query Q&A for a transcribed podcast
python scripts/whisperme-cli.py ask <task_id> "What are the key points?" --json

# Retry a failed task
python scripts/whisperme-cli.py retry <task_id>
```

---

## 4. MCP (Model Context Protocol) Mounting Guide

whisperMe mounts a native MCP server at `http://127.0.0.1:9101/mcp`.

Add the following snippet to your AI Agent's MCP config file (e.g., `mcp_config.json` or `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "whisperMe": {
      "url": "http://127.0.0.1:9101/mcp"
    }
  }
}
```

Available MCP Tools exposed:
- `transcribe_podcast(url_or_path)`
- `get_task_status(task_id)`
- `ask_podcast(task_id, question)`
- `list_tasks()`

---

## 5. Architectural & Preservation Constraints
- **Preserved Files**: When modifying or auto-updating, NEVER delete `data/config.json`, `data/prompt.json`, `data/whisperMe.db`, or `downloads/`.
- **Launchers**: `start.bat` and `start.sh` must remain in root.
