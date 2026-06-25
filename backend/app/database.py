import os
import json
import threading
import sqlite3
from datetime import datetime
import shutil
from app.config import PROJECT_DIR, STORAGE_BASE

DB_FILE_PATH = os.path.join(STORAGE_BASE, "whisperMe.db")
OLD_JSON_FILE_PATH = os.path.join(PROJECT_DIR, "tasks_db.json")

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        val = row[idx]
        if isinstance(val, str):
            # Try to parse JSON fields automatically if they look like JSON
            if (val.startswith('{') and val.endswith('}')) or (val.startswith('[') and val.endswith(']')):
                try:
                    val = json.loads(val)
                except Exception:
                    pass
        d[col[0]] = val
    return d

class LocalDatabase:
    def __init__(self):
        self._local = threading.local()
        self.write_lock = threading.Lock()
        self._init_db()
        self._migrate_if_needed()

    @property
    def conn(self):
        if not hasattr(self._local, "conn"):
            conn = sqlite3.connect(DB_FILE_PATH, check_same_thread=False)
            conn.row_factory = dict_factory
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.execute("PRAGMA busy_timeout=30000;")
            self._local.conn = conn
        return self._local.conn

    def _init_db(self):
        with self.write_lock:
            c = self.conn.cursor()
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
            
            # insights table
            c.execute('''CREATE TABLE IF NOT EXISTS insights (
                id TEXT PRIMARY KEY,
                podcast_id TEXT,
                original_text TEXT,
                refined_content TEXT NOT NULL,
                review_count INTEGER DEFAULT 0,
                next_review_date TEXT,
                status TEXT DEFAULT 'ACTIVE',
                created_at TEXT,
                FOREIGN KEY(podcast_id) REFERENCES tasks(id) ON DELETE CASCADE
            )''')
            c.execute('CREATE INDEX IF NOT EXISTS idx_insights_podcast_id ON insights(podcast_id)')
            
            # cards table
            c.execute('''CREATE TABLE IF NOT EXISTS cards (
                id TEXT PRIMARY KEY,
                paragraph_id TEXT,
                podcast_id TEXT,
                spark_title TEXT,
                why_it_matters TEXT,
                created_at TEXT,
                status TEXT,
                efactor REAL,
                interval INTEGER,
                next_review_date TEXT,
                quote TEXT,
                pos_x REAL,
                pos_y REAL
            )''')
            c.execute('CREATE INDEX IF NOT EXISTS idx_cards_podcast_id ON cards(podcast_id)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_cards_paragraph_id ON cards(paragraph_id)')
            
            # links table
            c.execute('''CREATE TABLE IF NOT EXISTS links (
                id TEXT PRIMARY KEY,
                source_card_id TEXT,
                target_card_id TEXT,
                my_synthesis TEXT,
                created_at TEXT
            )''')
            
            # boards table
            c.execute('''CREATE TABLE IF NOT EXISTS boards (
                id TEXT PRIMARY KEY,
                name TEXT,
                created_at TEXT
            )''')
            
            # board_cards table
            c.execute('''CREATE TABLE IF NOT EXISTS board_cards (
                board_id TEXT,
                card_id TEXT,
                pos_x REAL,
                pos_y REAL,
                PRIMARY KEY (board_id, card_id),
                FOREIGN KEY(board_id) REFERENCES boards(id) ON DELETE CASCADE,
                FOREIGN KEY(card_id) REFERENCES cards(id) ON DELETE CASCADE
            )''')

            # speakers table (global voiceprint library)
            c.execute('''CREATE TABLE IF NOT EXISTS speakers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                embedding TEXT NOT NULL,
                sample_count INTEGER DEFAULT 1,
                last_seen_at TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )''')
            self.conn.commit()

    def _migrate_if_needed(self):
        """侦测旧版 JSON 文件并无缝迁移至 SQLite"""
        with self.write_lock:
            c = self.conn.cursor()
            c.execute("SELECT COUNT(*) as count FROM tasks")
            count = c.fetchone()["count"]
            if count == 0 and os.path.exists(OLD_JSON_FILE_PATH):
                print("🔄 [MIGRATION] 检测到老旧 JSON 数据库，正在无缝迁移至 SQLite...")
                try:
                    with open(OLD_JSON_FILE_PATH, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    # Migrate tasks
                    for t in data.get("tasks", []):
                        self._insert_task_internal(c, t)
                        
                    # Migrate paragraphs
                    for p in data.get("paragraphs", []):
                        self._insert_paragraph_internal(c, p)
                        
                    # Migrate cards
                    for card in data.get("cards", []):
                        self._insert_card_internal(c, card)
                        
                    # Migrate links
                    for link in data.get("links", []):
                        self._insert_link_internal(c, link)
                        
                    self.conn.commit()
                    print("✅ [MIGRATION] 迁移成功！重命名旧文件为 tasks_db.json.bak")
                    os.rename(OLD_JSON_FILE_PATH, OLD_JSON_FILE_PATH + ".bak")
                except Exception as e:
                    print(f"❌ [MIGRATION] 迁移失败: {e}")
                    self.conn.rollback()
            
            # 增量升级：检查是否缺失 audio_url 列
            c.execute("PRAGMA table_info(tasks)")
            columns = [col["name"] for col in c.fetchall()]
            if "audio_url" not in columns:
                try:
                    c.execute("ALTER TABLE tasks ADD COLUMN audio_url TEXT")
                    self.conn.commit()
                    print("✅ [MIGRATION] 成功为 tasks 表增加 audio_url 列")
                except Exception as e:
                    print(f"❌ [MIGRATION] 增加 audio_url 列失败: {e}")
                    self.conn.rollback()

            # 增量升级：为 cards 表增加 pos_x 和 pos_y 用于白板画布
            c.execute("PRAGMA table_info(cards)")
            card_columns = [col["name"] for col in c.fetchall()]
            if "pos_x" not in card_columns:
                try:
                    c.execute("ALTER TABLE cards ADD COLUMN pos_x REAL")
                    c.execute("ALTER TABLE cards ADD COLUMN pos_y REAL")
                    self.conn.commit()
                    print("✅ [MIGRATION] 成功为 cards 表增加 pos_x 和 pos_y 列")
                except Exception as e:
                    print(f"❌ [MIGRATION] 增加 cards 表坐标列失败: {e}")
                    self.conn.rollback()

            # 增量升级：初始化默认画板，并将所有现有卡片加入默认画板
            c.execute("SELECT COUNT(*) as count FROM boards")
            b_count = c.fetchone()["count"]
            if b_count == 0:
                try:
                    default_board_id = "board_default"
                    c.execute("INSERT INTO boards (id, name, created_at) VALUES (?, ?, ?)", 
                              (default_board_id, "全局总览 (All)", datetime.now().isoformat()))
                    
                    c.execute("SELECT id, pos_x, pos_y FROM cards")
                    all_cards = c.fetchall()
                    for crd in all_cards:
                        c.execute("INSERT OR IGNORE INTO board_cards (board_id, card_id, pos_x, pos_y) VALUES (?, ?, ?, ?)",
                                  (default_board_id, crd["id"], crd.get("pos_x") or 0.0, crd.get("pos_y") or 0.0))
                    self.conn.commit()
                    print("✅ [MIGRATION] 成功初始化默认画板并迁移现有卡片")
                except Exception as e:
                    print(f"❌ [MIGRATION] 初始化默认画板失败: {e}")
                    self.conn.rollback()

            # 增量升级：为历史完成任务自动回填音频总时长
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
                                    print(f"⚠️ [LOG] 迁移回填任务 {task_row['id']} 音频时长失败: {e_dur}")
                                
                                if duration_str != "00:00":
                                    meta["duration"] = duration_str
                                    c.execute("UPDATE tasks SET metadata=? WHERE id=?", 
                                              (json.dumps(meta, ensure_ascii=False), task_row["id"]))
                                    updated_count += 1
                if updated_count > 0:
                    self.conn.commit()
                    print(f"✅ [MIGRATION] 成功为 {updated_count} 个历史播客任务回填音频总时长")
            except Exception as e_backfill:
                print(f"⚠️ [MIGRATION] 历史任务音频时长回填失败: {e_backfill}")

            # 增量升级：为 tasks 表增加 speaker_confidence 列
            c.execute("PRAGMA table_info(tasks)")
            task_columns = [col["name"] for col in c.fetchall()]
            if "speaker_confidence" not in task_columns:
                try:
                    c.execute("ALTER TABLE tasks ADD COLUMN speaker_confidence TEXT")
                    self.conn.commit()
                    print("✅ [MIGRATION] 成功为 tasks 表增加 speaker_confidence 列")
                except Exception as e:
                    print(f"❌ [MIGRATION] 增加 speaker_confidence 列失败: {e}")
                    self.conn.rollback()

            # 增量升级：为 tasks 表增加 qa_history 列
            c.execute("PRAGMA table_info(tasks)")
            task_columns = [col["name"] for col in c.fetchall()]
            if "qa_history" not in task_columns:
                try:
                    c.execute("ALTER TABLE tasks ADD COLUMN qa_history TEXT")
                    self.conn.commit()
                    print("✅ [MIGRATION] 成功为 tasks 表增加 qa_history 列")
                except Exception as e:
                    print(f"❌ [MIGRATION] 增加 qa_history 列失败: {e}")
                    self.conn.rollback()

            # 增量升级：将 speaker_fingerprints.json 迁移到 speakers 表
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
                        self.conn.commit()
                        os.rename(fingerprints_json, fingerprints_json + ".bak")
                        print(f"✅ [MIGRATION] 成功将 {len(fingerprints)} 条声纹从 JSON 迁移到 SQLite speakers 表")
                    except Exception as e:
                        print(f"❌ [MIGRATION] 声纹 JSON 迁移失败: {e}")
                        self.conn.rollback()


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

    def _insert_paragraph_internal(self, c, p: dict):
        sentences = json.dumps(p.get("sentences", []), ensure_ascii=False)
        c.execute('''INSERT OR REPLACE INTO paragraphs 
            (id, podcast_id, start_time, end_time, content, sentences, speaker)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (p.get("id"), p.get("podcast_id"), p.get("start_time"), p.get("end_time"),
             p.get("content"), sentences, p.get("speaker", "")))

    def _insert_card_internal(self, c, card: dict):
        c.execute('''INSERT OR REPLACE INTO cards 
            (id, paragraph_id, podcast_id, spark_title, why_it_matters, created_at, status, efactor, interval, next_review_date, quote, pos_x, pos_y)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (card.get("id"), card.get("paragraph_id"), card.get("podcast_id"), card.get("spark_title"),
             card.get("why_it_matters"), card.get("created_at"), card.get("status", "active"), 
             card.get("efactor", 2.5), card.get("interval", 1), card.get("next_review_date"), card.get("quote", ""),
             card.get("pos_x", 0.0), card.get("pos_y", 0.0)))

    def _insert_link_internal(self, c, link: dict):
        c.execute('''INSERT OR REPLACE INTO links 
            (id, source_card_id, target_card_id, my_synthesis, created_at)
            VALUES (?, ?, ?, ?, ?)''',
            (link.get("id"), link.get("source_card_id"), link.get("target_card_id"), 
             link.get("my_synthesis", ""), link.get("created_at", datetime.now().isoformat())))

    # ==================== TASKS ====================
    def get_all_tasks(self) -> list[dict]:
        c = self.conn.cursor()
        # 不取 transcript、speaker_embeddings 等大字段以保证列表渲染极速
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
            # 重组为前端期望的格式
            r["like_count"] = meta.get("like_count", 0)
            r["comment_count"] = meta.get("comment_count", 0)
            # Ensure boolean conversion
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
        c = self.conn.cursor()
        c.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
        row = c.fetchone()
        if row:
            # SQLite driver returns dict because of row_factory
            # Boolean fields
            row["obsidian_synced"] = bool(row["obsidian_synced"])
            row["restoring"] = bool(row["restoring"])
            # Inject duration at root
            meta = row.get("metadata") or {}
            if isinstance(meta, str):
                try: meta = json.loads(meta)
                except: meta = {}
            row["duration"] = meta.get("duration", "00:00")
            return row
        return None

    def get_next_pending_task(self) -> dict:
        c = self.conn.cursor()
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
            
        c = self.conn.cursor()
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
        with self.write_lock:
            c = self.conn.cursor()
            self._insert_task_internal(c, new_task)
            self.conn.commit()
        return new_task

    def update_task_field(self, task_id: str, **kwargs) -> None:
        """轻量级字段更新（不 SELECT 全行，仅 UPDATE SET）。
        适用于 progress、status 等高频更新字段。"""
        if not kwargs:
            return
        from datetime import datetime
        kwargs["updated_at"] = datetime.now().isoformat()
        set_clauses = []
        values = []
        for key, val in kwargs.items():
            set_clauses.append(f"{key}=?")
            if isinstance(val, (dict, list)):
                values.append(json.dumps(val, ensure_ascii=False))
            else:
                values.append(val)
        values.append(task_id)
        sql = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id=?"
        with self.write_lock:
            self.conn.execute(sql, values)
            self.conn.commit()

    def update_task(self, task_id: str, **kwargs):
        with self.write_lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
            row = c.fetchone()
            if not row:
                return None
            
            for k, v in kwargs.items():
                row[k] = v
            self._insert_task_internal(c, row)
            self.conn.commit()
            
            # Re-fetch to return formatted data
            c.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
            updated_row = c.fetchone()
            if updated_row:
                updated_row["obsidian_synced"] = bool(updated_row["obsidian_synced"])
                updated_row["restoring"] = bool(updated_row["restoring"])
                # Inject duration at root
                meta = updated_row.get("metadata") or {}
                if isinstance(meta, str):
                    try: meta = json.loads(meta)
                    except: meta = {}
                updated_row["duration"] = meta.get("duration", "00:00")
            return updated_row

    def delete_task(self, task_id: str) -> bool:
        with self.write_lock:
            c = self.conn.cursor()
            c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            if c.rowcount > 0:
                # SQLite FOREIGN KEY CASCADE needs PRAGMA foreign_keys = ON, but we manually delete just in case
                c.execute("DELETE FROM paragraphs WHERE podcast_id=?", (task_id,))
                c.execute("DELETE FROM cards WHERE podcast_id=?", (task_id,))
                
                # Cleanup orphaned links
                c.execute('''DELETE FROM links 
                             WHERE source_card_id NOT IN (SELECT id FROM cards) 
                             OR target_card_id NOT IN (SELECT id FROM cards)''')
                self.conn.commit()
                return True
            return False

    # ==================== PARAGRAPHS ====================
    def get_paragraphs_by_podcast(self, podcast_id: str) -> list[dict]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM paragraphs WHERE podcast_id=?", (podcast_id,))
        return c.fetchall()

    def delete_paragraphs_by_podcast(self, podcast_id: str):
        with self.write_lock:
            c = self.conn.cursor()
            c.execute("DELETE FROM paragraphs WHERE podcast_id=?", (podcast_id,))
            self.conn.commit()

    def add_paragraphs(self, paragraphs: list[dict]):
        if not paragraphs: return
        with self.write_lock:
            c = self.conn.cursor()
            for p in paragraphs:
                self._insert_paragraph_internal(c, p)
            self.conn.commit()

    # ==================== INSIGHTS ====================
    def _insert_insight_internal(self, c, insight: dict):
        c.execute('''INSERT OR REPLACE INTO insights 
            (id, podcast_id, original_text, refined_content, review_count, next_review_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (insight.get("id"), insight.get("podcast_id"), insight.get("original_text", ""),
             insight.get("refined_content", ""), insight.get("review_count", 0),
             insight.get("next_review_date", ""), insight.get("status", "ACTIVE"),
             insight.get("created_at", datetime.now().isoformat())))

    def get_all_insights(self) -> list[dict]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM insights WHERE status != 'DELETED' ORDER BY created_at DESC")
        return c.fetchall()

    def get_insights_for_review(self) -> list[dict]:
        c = self.conn.cursor()
        now = datetime.now().isoformat()
        # 简化逻辑，获取 active 的 insight 并按需要复习的时间排，或者随机取3-5个
        c.execute("SELECT * FROM insights WHERE status = 'ACTIVE' ORDER BY RANDOM() LIMIT 5")
        return c.fetchall()

    def create_insight(self, insight: dict) -> dict:
        import uuid
        if "id" not in insight or not insight["id"]:
            insight["id"] = str(uuid.uuid4())
        if "created_at" not in insight:
            insight["created_at"] = datetime.now().isoformat()
        with self.write_lock:
            c = self.conn.cursor()
            self._insert_insight_internal(c, insight)
            self.conn.commit()
            return insight

    def update_insight(self, insight_id: str, **kwargs) -> dict:
        with self.write_lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM insights WHERE id=?", (insight_id,))
            row = c.fetchone()
            if not row:
                return None
            for k, v in kwargs.items():
                row[k] = v
            self._insert_insight_internal(c, row)
            self.conn.commit()
            
            c.execute("SELECT * FROM insights WHERE id=?", (insight_id,))
            return c.fetchone()

    def delete_insight(self, insight_id: str) -> bool:
        with self.write_lock:
            c = self.conn.cursor()
            c.execute("UPDATE insights SET status = 'DELETED' WHERE id=?", (insight_id,))
            if c.rowcount > 0:
                self.conn.commit()
                return True
            return False

    # ==================== CARDS ====================
    def get_all_cards(self) -> list[dict]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM cards")
        return c.fetchall()

    def get_cards_by_podcast(self, podcast_id: str) -> list[dict]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM cards WHERE podcast_id=?", (podcast_id,))
        return c.fetchall()

    def get_card(self, card_id: str) -> dict:
        c = self.conn.cursor()
        c.execute("SELECT * FROM cards WHERE id=?", (card_id,))
        return c.fetchone()

    def create_card(self, card: dict) -> dict:
        with self.write_lock:
            c = self.conn.cursor()
            # 避免同一段落重复沉淀
            pid = card.get("paragraph_id")
            if pid:
                c.execute("DELETE FROM cards WHERE paragraph_id=?", (pid,))
            
            self._insert_card_internal(c, card)
            self.conn.commit()
            return card

    def update_card(self, card_id: str, **kwargs) -> dict:
        with self.write_lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM cards WHERE id=?", (card_id,))
            row = c.fetchone()
            if not row:
                return None
            for k, v in kwargs.items():
                row[k] = v
            self._insert_card_internal(c, row)
            self.conn.commit()
            
            c.execute("SELECT * FROM cards WHERE id=?", (card_id,))
            return c.fetchone()

    def delete_card(self, card_id: str) -> bool:
        with self.write_lock:
            c = self.conn.cursor()
            c.execute("DELETE FROM cards WHERE id=?", (card_id,))
            if c.rowcount > 0:
                c.execute('''DELETE FROM links 
                             WHERE source_card_id=? OR target_card_id=?''', 
                          (card_id, card_id))
                self.conn.commit()
                return True
            return False

    # ==================== LINKS ====================
    def get_all_links(self) -> list[dict]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM links")
        return c.fetchall()

    def create_link(self, link: dict) -> dict:
        with self.write_lock:
            c = self.conn.cursor()
            # 检查双向连接是否已存在
            c.execute('''SELECT * FROM links 
                         WHERE (source_card_id=? AND target_card_id=?) 
                         OR (source_card_id=? AND target_card_id=?)''',
                      (link["source_card_id"], link["target_card_id"],
                       link["target_card_id"], link["source_card_id"]))
            row = c.fetchone()
            if row:
                row["my_synthesis"] = link.get("my_synthesis", "")
                self._insert_link_internal(c, row)
                self.conn.commit()
                return row
            else:
                import uuid
                if "id" not in link:
                    link["id"] = str(uuid.uuid4())
                self._insert_link_internal(c, link)
                self.conn.commit()
                return link

    def delete_link(self, link_id: str) -> bool:
        with self.write_lock:
            c = self.conn.cursor()
            c.execute("DELETE FROM links WHERE id=?", (link_id,))
            if c.rowcount > 0:
                self.conn.commit()
                return True
            return False

    # ==================== BOARDS ====================
    def get_all_boards(self) -> list[dict]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM boards ORDER BY created_at ASC")
        return c.fetchall()

    def create_board(self, board_id: str, name: str) -> dict:
        with self.write_lock:
            c = self.conn.cursor()
            board = {
                "id": board_id,
                "name": name,
                "created_at": datetime.now().isoformat()
            }
            c.execute("INSERT INTO boards (id, name, created_at) VALUES (?, ?, ?)", 
                      (board["id"], board["name"], board["created_at"]))
            self.conn.commit()
            return board

    def get_cards_by_board(self, board_id: str) -> list[dict]:
        c = self.conn.cursor()
        c.execute('''
            SELECT c.*, bc.pos_x as bc_pos_x, bc.pos_y as bc_pos_y
            FROM cards c
            JOIN board_cards bc ON c.id = bc.card_id
            WHERE bc.board_id = ?
        ''', (board_id,))
        rows = c.fetchall()
        for r in rows:
            r["pos_x"] = r.pop("bc_pos_x")
            r["pos_y"] = r.pop("bc_pos_y")
        return rows

    def add_card_to_board(self, board_id: str, card_id: str, pos_x: float = 0.0, pos_y: float = 0.0):
        with self.write_lock:
            c = self.conn.cursor()
            c.execute("INSERT OR IGNORE INTO board_cards (board_id, card_id, pos_x, pos_y) VALUES (?, ?, ?, ?)",
                      (board_id, card_id, pos_x, pos_y))
            self.conn.commit()

    def update_board_card_position(self, board_id: str, card_id: str, pos_x: float, pos_y: float):
        with self.write_lock:
            c = self.conn.cursor()
            c.execute("UPDATE board_cards SET pos_x=?, pos_y=? WHERE board_id=? AND card_id=?",
                      (pos_x, pos_y, board_id, card_id))
            self.conn.commit()

    # ==================== SPEAKERS (Global Voiceprint Library) ====================
    def get_all_speakers(self) -> list[dict]:
        """获取全局声纹库列表（不返回 embedding 向量）"""
        c = self.conn.cursor()
        c.execute("SELECT id, name, sample_count, last_seen_at, created_at, updated_at FROM speakers ORDER BY sample_count DESC, name ASC")
        return c.fetchall()

    def get_speaker(self, name: str) -> dict:
        """按名字查询单个声纹（含 embedding）"""
        c = self.conn.cursor()
        c.execute("SELECT * FROM speakers WHERE name=?", (name,))
        return c.fetchone()

    def get_all_speakers_with_embeddings(self) -> dict:
        """获取全局声纹库 {name: embedding_list}，供匹配使用"""
        c = self.conn.cursor()
        c.execute("SELECT name, embedding, sample_count FROM speakers")
        rows = c.fetchall()
        result = {}
        for r in rows:
            emb = r["embedding"]
            if isinstance(emb, str):
                try: emb = json.loads(emb)
                except: continue
            result[r["name"]] = {"embedding": emb, "sample_count": r.get("sample_count", 1)}
        return result

    def upsert_speaker(self, name: str, embedding: list, sample_count: int = None):
        """插入或更新声纹（name 为 UNIQUE 键）"""
        with self.write_lock:
            c = self.conn.cursor()
            now_iso = datetime.now().isoformat()
            emb_json = json.dumps(embedding, ensure_ascii=False)
            c.execute("SELECT id, sample_count FROM speakers WHERE name=?", (name,))
            existing = c.fetchone()
            if existing:
                new_count = sample_count if sample_count is not None else (existing["sample_count"] or 0) + 1
                c.execute("UPDATE speakers SET embedding=?, sample_count=?, last_seen_at=?, updated_at=? WHERE name=?",
                          (emb_json, new_count, now_iso, now_iso, name))
            else:
                c.execute("INSERT INTO speakers (name, embedding, sample_count, last_seen_at) VALUES (?, ?, ?, ?)",
                          (name, emb_json, sample_count or 1, now_iso))
            self.conn.commit()

    def delete_speaker(self, name: str) -> bool:
        """从全局声纹库中删除指定说话人"""
        with self.write_lock:
            c = self.conn.cursor()
            c.execute("DELETE FROM speakers WHERE name=?", (name,))
            if c.rowcount > 0:
                self.conn.commit()
                return True
            return False

    def merge_speakers(self, source_name: str, target_name: str) -> bool:
        """合并声纹：将 source 的 embedding 加权合并到 target，然后删除 source"""
        with self.write_lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM speakers WHERE name=?", (source_name,))
            source = c.fetchone()
            c.execute("SELECT * FROM speakers WHERE name=?", (target_name,))
            target = c.fetchone()
            if not source or not target:
                return False

            src_emb = source["embedding"]
            tgt_emb = target["embedding"]
            if isinstance(src_emb, str): src_emb = json.loads(src_emb)
            if isinstance(tgt_emb, str): tgt_emb = json.loads(tgt_emb)

            src_count = source.get("sample_count", 1)
            tgt_count = target.get("sample_count", 1)
            total = src_count + tgt_count

            # 加权平均合并 embedding
            merged_emb = [(s * src_count + t * tgt_count) / total for s, t in zip(src_emb, tgt_emb)]

            now_iso = datetime.now().isoformat()
            c.execute("UPDATE speakers SET embedding=?, sample_count=?, last_seen_at=?, updated_at=? WHERE name=?",
                      (json.dumps(merged_emb, ensure_ascii=False), total, now_iso, now_iso, target_name))
            c.execute("DELETE FROM speakers WHERE name=?", (source_name,))
            self.conn.commit()
            return True

# 实例化全局单例数据库对象
db = LocalDatabase()
