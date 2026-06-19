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
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(DB_FILE_PATH, check_same_thread=False)
        self.conn.row_factory = dict_factory
        self._init_db()
        self._migrate_if_needed()

    def _init_db(self):
        with self.lock:
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
                quote TEXT
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
            self.conn.commit()

    def _migrate_if_needed(self):
        """侦测旧版 JSON 文件并无缝迁移至 SQLite"""
        with self.lock:
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

    def _insert_task_internal(self, c, t: dict):
        metadata = json.dumps(t.get("metadata", {}), ensure_ascii=False)
        transcript = json.dumps(t.get("transcript", []), ensure_ascii=False)
        speaker_mappings = json.dumps(t.get("speaker_mappings", {}), ensure_ascii=False)
        speaker_embeddings = json.dumps(t.get("speaker_embeddings", {}), ensure_ascii=False)
        c.execute('''INSERT OR REPLACE INTO tasks 
            (id, url, asr_mode, summary_mode, title, podcast_name, status, progress, 
            error_message, created_at, image_url, obsidian_synced, restoring, restore_progress, 
            metadata, transcript, summary, speaker_mappings, speaker_embeddings, audio_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
            (t.get("id"), t.get("url"), t.get("asr_mode", "local"), t.get("summary_mode", "local"),
             t.get("title"), t.get("podcast_name"), t.get("status"), t.get("progress"),
             t.get("error_message"), t.get("created_at"), t.get("image_url"), 
             bool(t.get("obsidian_synced")), bool(t.get("restoring")), t.get("restore_progress", 0),
             metadata, transcript, t.get("summary", ""), speaker_mappings, speaker_embeddings, t.get("audio_url", "")))

    def _insert_paragraph_internal(self, c, p: dict):
        sentences = json.dumps(p.get("sentences", []), ensure_ascii=False)
        c.execute('''INSERT OR REPLACE INTO paragraphs 
            (id, podcast_id, start_time, end_time, content, sentences, speaker)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (p.get("id"), p.get("podcast_id"), p.get("start_time"), p.get("end_time"),
             p.get("content"), sentences, p.get("speaker", "")))

    def _insert_card_internal(self, c, card: dict):
        c.execute('''INSERT OR REPLACE INTO cards 
            (id, paragraph_id, podcast_id, spark_title, why_it_matters, created_at, status, efactor, interval, next_review_date, quote)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (card.get("id"), card.get("paragraph_id"), card.get("podcast_id"), card.get("spark_title"),
             card.get("why_it_matters"), card.get("created_at"), card.get("status", "active"), 
             card.get("efactor", 2.5), card.get("interval", 1), card.get("next_review_date"), card.get("quote", "")))

    def _insert_link_internal(self, c, link: dict):
        c.execute('''INSERT OR REPLACE INTO links 
            (id, source_card_id, target_card_id, my_synthesis, created_at)
            VALUES (?, ?, ?, ?, ?)''',
            (link.get("id"), link.get("source_card_id"), link.get("target_card_id"), 
             link.get("my_synthesis", ""), link.get("created_at", datetime.now().isoformat())))

    # ==================== TASKS ====================
    def get_all_tasks(self) -> list[dict]:
        with self.lock:
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
                r["metadata"] = {
                    "pub_date": meta.get("pub_date", ""),
                    "source": meta.get("source", "")
                }
                tasks_list.append(r)
            return tasks_list

    def get_task(self, task_id: str) -> dict:
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
            row = c.fetchone()
            if row:
                # SQLite driver returns dict because of row_factory
                # Boolean fields
                row["obsidian_synced"] = bool(row["obsidian_synced"])
                row["restoring"] = bool(row["restoring"])
                return row
            return None

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
            "speaker_embeddings": {}
        }
        with self.lock:
            c = self.conn.cursor()
            self._insert_task_internal(c, new_task)
            self.conn.commit()
        return new_task

    def update_task(self, task_id: str, **kwargs):
        with self.lock:
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
            return updated_row

    def delete_task(self, task_id: str) -> bool:
        with self.lock:
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
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM paragraphs WHERE podcast_id=?", (podcast_id,))
            return c.fetchall()

    def delete_paragraphs_by_podcast(self, podcast_id: str):
        with self.lock:
            c = self.conn.cursor()
            c.execute("DELETE FROM paragraphs WHERE podcast_id=?", (podcast_id,))
            self.conn.commit()

    def add_paragraphs(self, paragraphs: list[dict]):
        if not paragraphs: return
        with self.lock:
            c = self.conn.cursor()
            for p in paragraphs:
                self._insert_paragraph_internal(c, p)
            self.conn.commit()

    # ==================== CARDS ====================
    def get_all_cards(self) -> list[dict]:
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM cards")
            return c.fetchall()

    def get_cards_by_podcast(self, podcast_id: str) -> list[dict]:
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM cards WHERE podcast_id=?", (podcast_id,))
            return c.fetchall()

    def get_card(self, card_id: str) -> dict:
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM cards WHERE id=?", (card_id,))
            return c.fetchone()

    def create_card(self, card: dict) -> dict:
        with self.lock:
            c = self.conn.cursor()
            # 避免同一段落重复沉淀
            pid = card.get("paragraph_id")
            if pid:
                c.execute("DELETE FROM cards WHERE paragraph_id=?", (pid,))
            
            self._insert_card_internal(c, card)
            self.conn.commit()
            return card

    def update_card(self, card_id: str, **kwargs) -> dict:
        with self.lock:
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
        with self.lock:
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
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM links")
            return c.fetchall()

    def create_link(self, link: dict) -> dict:
        with self.lock:
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
        with self.lock:
            c = self.conn.cursor()
            c.execute("DELETE FROM links WHERE id=?", (link_id,))
            if c.rowcount > 0:
                self.conn.commit()
                return True
            return False

# 实例化全局单例数据库对象
db = LocalDatabase()
