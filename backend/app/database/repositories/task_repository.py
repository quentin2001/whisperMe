import json
from datetime import datetime

class TaskRepository:
    def __init__(self, core):
        self.core = core

    def _insert_task_internal(self, c, t: dict):
        metadata = json.dumps(t.get("metadata", {}), ensure_ascii=False)
        transcript = json.dumps(t.get("transcript", []), ensure_ascii=False)
        speaker_mappings = json.dumps(t.get("speaker_mappings", {}), ensure_ascii=False)
        speaker_embeddings = json.dumps(t.get("speaker_embeddings", {}), ensure_ascii=False)
        speaker_confidence = json.dumps(t.get("speaker_confidence", {}), ensure_ascii=False)
        qa_history = json.dumps(t.get("qa_history") or [], ensure_ascii=False)
        c.execute('''INSERT OR REPLACE INTO tasks
            (id, url, asr_mode, summary_mode, title, podcast_name, status, progress,
            error_message, created_at, image_url, obsidian_synced, restoring, restore_progress,
            metadata, transcript, summary, speaker_mappings, speaker_embeddings, audio_url, speaker_confidence, qa_history)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (t.get("id"), t.get("url"), t.get("asr_mode", "local"), t.get("summary_mode", "local"),
             t.get("title"), t.get("podcast_name"), t.get("status"), t.get("progress"),
             t.get("error_message"), t.get("created_at"), t.get("image_url"),
             bool(t.get("obsidian_synced")), bool(t.get("restoring")), t.get("restore_progress", 0),
             metadata, transcript, t.get("summary", ""), speaker_mappings, speaker_embeddings, t.get("audio_url", ""),
             speaker_confidence, qa_history))

    def get_all_tasks(self) -> list[dict]:
        c = self.core.conn.cursor()
        c.execute('''SELECT id, url, asr_mode, summary_mode, title, podcast_name, status, 
                     progress, created_at, error_message, obsidian_synced, image_url, 
                     restoring, restore_progress, audio_url, metadata 
                     FROM tasks ORDER BY created_at DESC''')
        rows = c.fetchall()
        tasks_list = []
        for r in rows:
            meta = r.get("metadata", {})
            if isinstance(meta, str):
                try: meta = json.loads(meta)
                except: meta = {}
            r["like_count"] = meta.get("like_count", 0)
            r["comment_count"] = meta.get("comment_count", 0)
            r["obsidian_synced"] = bool(r["obsidian_synced"])
            r["restoring"] = bool(r["restoring"])
            r["duration"] = meta.get("duration", "00:00")
            r["metadata"] = {
                "pub_date": meta.get("pub_date", ""),
                "source": meta.get("source", ""),
                "duration": meta.get("duration", "00:00")
            }
            tasks_list.append(r)
        return tasks_list

    def get_task(self, task_id: str) -> dict:
        c = self.core.conn.cursor()
        c.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
        row = c.fetchone()
        if row:
            row["obsidian_synced"] = bool(row["obsidian_synced"])
            row["restoring"] = bool(row["restoring"])
            meta = row.get("metadata") or {}
            if isinstance(meta, str):
                try: meta = json.loads(meta)
                except: meta = {}
            row["duration"] = meta.get("duration", "00:00")
            return row
        return None

    def get_next_pending_task(self) -> dict:
        c = self.core.conn.cursor()
        c.execute("SELECT * FROM tasks WHERE status='pending' ORDER BY created_at ASC LIMIT 1")
        row = c.fetchone()
        if row:
            row["obsidian_synced"] = bool(row["obsidian_synced"])
            row["restoring"] = bool(row["restoring"])
            meta = row.get("metadata") or {}
            if isinstance(meta, str):
                try: meta = json.loads(meta)
                except: meta = {}
            row["duration"] = meta.get("duration", "00:00")
            return row
        return None

    def get_task_queue_position(self, task_id: str, current_task_id: str = None) -> int:
        if current_task_id == task_id:
            return 0
        c = self.core.conn.cursor()
        c.execute("SELECT created_at, status FROM tasks WHERE id=?", (task_id,))
        target = c.fetchone()
        if not target:
            return -1
        if target["status"] != "pending":
            return -1
        c.execute("SELECT COUNT(*) as cnt FROM tasks WHERE status='pending' AND created_at < ?", (target["created_at"],))
        row = c.fetchone()
        return row["cnt"] + 1 if row else -1

    def add_task(self, task_id: str, url: str, asr_mode: str = "local", summary_mode: str = "local") -> dict:
        new_task = {
            "id": task_id,
            "url": url,
            "asr_mode": asr_mode,
            "summary_mode": summary_mode,
            "title": "等待解析中...",
            "podcast_name": "等待解析...",
            "status": "pending",
            "progress": 0.0,
            "error_message": None,
            "created_at": datetime.now().isoformat(),
            "image_url": "",
            "obsidian_synced": False,
            "restoring": False,
            "restore_progress": 0,
            "metadata": {
                "title": "等待解析...",
                "podcast_name": "等待解析...",
                "shownotes": "",
                "like_count": 0,
                "comment_count": 0,
                "comments": [],
                "image_url": "",
                "source": "unknown"
            },
            "transcript": [],
            "summary": "",
            "speaker_mappings": {},
            "speaker_embeddings": {},
            "speaker_confidence": {}
        }
        with self.core.write_lock:
            c = self.core.conn.cursor()
            self._insert_task_internal(c, new_task)
            self.core.conn.commit()
        return new_task

    def update_task_field(self, task_id: str, **kwargs) -> dict:
        """Atomic update logic. Returns the updated task dictionary."""
        if not kwargs:
            return self.get_task(task_id)
            
        # Optional: auto update "updated_at" if you have it in schema, but we don't for tasks.
        set_clauses = []
        values = []
        for key, val in kwargs.items():
            set_clauses.append(f"{key}=?")
            if isinstance(val, (dict, list)):
                values.append(json.dumps(val, ensure_ascii=False))
            elif isinstance(val, bool):
                values.append(int(val))
            else:
                values.append(val)
        values.append(task_id)
        sql = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id=?"
        with self.core.write_lock:
            self.core.conn.execute(sql, values)
            self.core.conn.commit()
            
        return self.get_task(task_id)

    def delete_task(self, task_id: str) -> bool:
        with self.core.write_lock:
            c = self.core.conn.cursor()
            c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            if c.rowcount > 0:
                c.execute("DELETE FROM paragraphs WHERE podcast_id=?", (task_id,))
                c.execute("DELETE FROM cards WHERE podcast_id=?", (task_id,))
                c.execute('''DELETE FROM links 
                             WHERE source_card_id NOT IN (SELECT id FROM cards) 
                             OR target_card_id NOT IN (SELECT id FROM cards)''')
                self.core.conn.commit()
                return True
            return False
