import os
import json
from datetime import datetime
from app.config import PROJECT_DIR, STORAGE_BASE


def init_schema(core):
    with core.write_lock:
        c = core.conn.cursor()
        # tasks table
        c.execute('''CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            url TEXT,
            asr_mode TEXT,
            summary_mode TEXT,
            title TEXT,
            podcast_name TEXT,
            status TEXT,
            progress REAL,
            error_message TEXT,
            created_at TEXT,
            image_url TEXT,
            obsidian_synced BOOLEAN,
            restoring BOOLEAN,
            restore_progress REAL,
            metadata TEXT,
            transcript TEXT,
            summary TEXT,
            speaker_mappings TEXT,
            speaker_embeddings TEXT,
            audio_url TEXT
        )''')
        # paragraphs table
        c.execute('''CREATE TABLE IF NOT EXISTS paragraphs (
            id TEXT PRIMARY KEY,
            podcast_id TEXT,
            start_time REAL,
            end_time REAL,
            content TEXT,
            sentences TEXT,
            speaker TEXT,
            FOREIGN KEY(podcast_id) REFERENCES tasks(id) ON DELETE CASCADE
        )''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_paragraphs_podcast_id ON paragraphs(podcast_id)')
        
        # speakers table
        c.execute('''CREATE TABLE IF NOT EXISTS speakers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            embedding TEXT NOT NULL,
            sample_count INTEGER DEFAULT 1,
            last_seen_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )''')
        core.conn.commit()


def run_migrations(core, facade):
    """Run incremental migrations and JSON sync"""
    OLD_JSON_FILE_PATH = os.path.join(PROJECT_DIR, "tasks_db.json")
    with core.write_lock:
        c = core.conn.cursor()
        c.execute("SELECT COUNT(*) as count FROM tasks")
        count = c.fetchone()["count"]
        if count == 0 and os.path.exists(OLD_JSON_FILE_PATH):
            print("🔄 [MIGRATION] 检测到老旧 JSON 数据库，正在无缝迁移至 SQLite...")
            try:
                with open(OLD_JSON_FILE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for t in data.get("tasks", []):
                    facade.task_repo._insert_task_internal(c, t)
                for p in data.get("paragraphs", []):
                    facade.paragraph_repo._insert_paragraph_internal(c, p)
                core.conn.commit()
                print("✅ [MIGRATION] 迁移成功！重命名旧文件为 tasks_db.json.bak")
                os.rename(OLD_JSON_FILE_PATH, OLD_JSON_FILE_PATH + ".bak")
            except Exception as e:
                print(f"❌ [MIGRATION] 迁移失败: {e}")
                core.conn.rollback()
        
        # Incremental columns checks
        def add_column_if_missing(table, col, col_type):
            c.execute(f"PRAGMA table_info({table})")
            columns = [info["name"] for info in c.fetchall()]
            if col not in columns:
                try:
                    c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
                    core.conn.commit()
                    print(f"✅ [MIGRATION] Added column {col} to {table}")
                except Exception as e:
                    print(f"❌ [MIGRATION] Add column {col} failed: {e}")
                    core.conn.rollback()

        add_column_if_missing("tasks", "audio_url", "TEXT")
        add_column_if_missing("tasks", "speaker_confidence", "TEXT")
        add_column_if_missing("tasks", "qa_history", "TEXT")
        add_column_if_missing("tasks", "hf_token_missing", "BOOLEAN")
        # Audio duration backfill
        try:
            c.execute("SELECT id, audio_url, metadata FROM tasks WHERE status='completed'")
            completed_tasks = c.fetchall()
            updated_count = 0
            for task_row in completed_tasks:
                meta = task_row.get("metadata") or {}
                if isinstance(meta, str):
                    try: meta = json.loads(meta)
                    except: meta = {}
                
                if "duration" not in meta or meta["duration"] == "00:00":
                    audio_url = task_row.get("audio_url")
                    if audio_url:
                        filename = os.path.basename(audio_url)
                        from app.config import SHORT_DOWNLOADS_DIR, FFMPEG_PATH
                        physical_path = os.path.join(SHORT_DOWNLOADS_DIR, filename)
                        if os.path.exists(physical_path):
                            duration_str = "00:00"
                            try:
                                import subprocess
                                import re
                                cmd = [FFMPEG_PATH, "-i", physical_path]
                                res = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
                                if res.returncode != 0:
                                    cmd = ["ffmpeg", "-i", physical_path]
                                    res = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
                                output = res.stderr or ""
                                match = re.search(r"Duration:\s*(\d{2}:\d{2}:\d{2})", output)
                                if match:
                                    raw_d = match.group(1)
                                    parts = raw_d.split(":")
                                    if parts[0] == "00":
                                        duration_str = f"{parts[1]}:{parts[2]}"
                                    else:
                                        duration_str = raw_d
                            except Exception as e_dur:
                                pass
                            
                            if duration_str != "00:00":
                                meta["duration"] = duration_str
                                c.execute("UPDATE tasks SET metadata=? WHERE id=?", 
                                          (json.dumps(meta, ensure_ascii=False), task_row["id"]))
                                updated_count += 1
            if updated_count > 0:
                core.conn.commit()
        except Exception as e_backfill:
            pass

        # Speaker JSON migration
        fingerprints_json = os.path.join(PROJECT_DIR, "speaker_fingerprints.json")
        if os.path.exists(fingerprints_json):
            c.execute("SELECT COUNT(*) as cnt FROM speakers")
            sp_count = c.fetchone()["cnt"]
            if sp_count == 0:
                try:
                    with open(fingerprints_json, "r", encoding="utf-8") as f:
                        fingerprints = json.load(f)
                    now_iso = datetime.now().isoformat()
                    for name, emb in fingerprints.items():
                        c.execute(
                            "INSERT OR IGNORE INTO speakers (name, embedding, sample_count, last_seen_at) VALUES (?, ?, 1, ?)",
                            (name, json.dumps(emb, ensure_ascii=False), now_iso)
                        )
                    core.conn.commit()
                    os.rename(fingerprints_json, fingerprints_json + ".bak")
                except Exception as e:
                    core.conn.rollback()
