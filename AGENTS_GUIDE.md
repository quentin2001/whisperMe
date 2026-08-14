# whisperMe AI Agent Developer & Deployment Guide

This guide is written for AI Agents (Cursor, Antigravity, Claude Desktop, AutoGPT, etc.) to automatically inspect, deploy, configure local AI models, and control whisperMe programmatically.

---

## 1. Quick Start for Agents

### Check Server & Health Status
```bash
# Check server process status
python scripts/whisperme-cli.py server status --json

# Check comprehensive system health (CPU, RAM, GPU, Dependencies)
python scripts/whisperme-cli.py health --json
```

### Start / Stop Server
```bash
# Start background server
python scripts/whisperme-cli.py server start --json

# Stop background server
python scripts/whisperme-cli.py server stop --json

# Check server logs
python scripts/whisperme-cli.py server logs --tail 50
```

*Direct Launchers:*
- **Windows**: `start.bat`
- **macOS / Linux**: `bash start.sh`
- **Foreground Dev**: `python scripts/launcher.py --foreground`

Default server address: `http://127.0.0.1:9101`.

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

### Configure Local Modes via API / CLI
Switch whisperMe to use **local ASR** (FunASR/Whisper) and **local LLM** (Ollama / LM Studio):

```bash
# Via CLI
python scripts/whisperme-cli.py config set asr_mode=local summary_mode=local ollama_model=qwen2.5:7b-instruct --json

# Or via HTTP API
curl -X POST http://127.0.0.1:9101/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "asr_mode": "local",
    "local_whisper_model_path": "models/funasr",
    "summary_mode": "local",
    "ollama_url": "http://localhost:11434",
    "ollama_model": "qwen2.5:7b-instruct"
  }'
```

---

## 3. Programmatic CLI Control

Agents can control tasks without a browser using `scripts/whisperme-cli.py` (all subcommands support `--json`):

```bash
# Create a podcast transcription task
python scripts/whisperme-cli.py task create "https://www.xiaoyuzhoufm.com/episode/xxx" --asr local --json

# List recent tasks
python scripts/whisperme-cli.py task list --json

# Check task status and details
python scripts/whisperme-cli.py task status <task_id> --json

# Export task transcript (formats: markdown, text, srt, vtt, json)
python scripts/whisperme-cli.py task export <task_id> --format markdown

# Ask a question based on a podcast episode
python scripts/whisperme-cli.py ask <task_id> "What are the key points?" --json

# View or update custom AI prompt template
python scripts/whisperme-cli.py prompt show --json
python scripts/whisperme-cli.py prompt set "Your custom summary prompt template..." --json
```

---

## 4. MCP (Model Context Protocol) Integration

whisperMe runs a FastMCP server over SSE/HTTP mounted at `http://127.0.0.1:9101/mcp`.

### Client Configuration (e.g. `claude_desktop_config.json` / Antigravity MCP settings):
```json
{
  "mcpServers": {
    "whisperMe": {
      "url": "http://127.0.0.1:9101/mcp"
    }
  }
}
```

### Exposed MCP Primitives

- **Tools**:
  - `create_task(url, asr_mode)` — Submit a new podcast URL for download, transcription and summary
  - `list_tasks(status, limit)` — List tasks with optional status filter
  - `get_task(task_id)` — Get full task transcript, summary, metadata and speaker data
  - `search_tasks(query, limit)` — Search podcasts by title, author, or transcript keywords
  - `export_transcript(task_id, format)` — Export in markdown, text, srt, vtt, or json
  - `ask_podcast(task_id, question)` — Ask AI questions directly grounded on the episode transcript
  - `get_system_status()` — Retrieve real-time CPU, RAM, GPU, and queue statistics
  - `get_config()` — Get current system configuration (credentials safely masked)
- **Resources**:
  - `whisperme://tasks` — All task list
  - `whisperme://tasks/{task_id}` — Single task details
  - `whisperme://config` — Current sanitized system configuration
- **Prompts**:
  - `summarize_podcast(task_id)` — Generate template prompt for summarizing a specific episode
  - `ask_about_podcast(task_id, question)` — Generate template prompt for grounded Q&A

---

## 5. Architectural & Development Constraints

For core packaging, build downsizing rules (CPU-only PyTorch), startup script preservation, and data exclusion rules, refer directly to [.agents/AGENTS.md](file:///.agents/AGENTS.md).
