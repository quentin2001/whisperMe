import os
import json
import threading
from datetime import datetime
from app.config import PROJECT_DIR

DB_FILE_PATH = os.path.join(PROJECT_DIR, "tasks_db.json")

class LocalDatabase:
    def __init__(self):
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self.lock:
            if not os.path.exists(DB_FILE_PATH):
                with open(DB_FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump({"tasks": [], "paragraphs": [], "cards": [], "links": []}, f, ensure_ascii=False, indent=2)
            else:
                try:
                    with open(DB_FILE_PATH, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    modified = False
                    for key in ["paragraphs", "cards", "links"]:
                        if key not in data:
                            data[key] = []
                            modified = True
                    if modified:
                        with open(DB_FILE_PATH, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    print(f"⚠️ [DB INIT ERROR] Migration failed: {e}")

    def _read_data(self) -> dict:
        try:
            with open(DB_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"tasks": []}

    def _write_data(self, data: dict):
        with open(DB_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_all_tasks(self) -> list[dict]:
        with self.lock:
            data = self._read_data()
            # 过滤掉体积过大的转录全文，仅返回核心字段用于列表展示（优化性能）
            tasks_list = []
            for t in data.get("tasks", []):
                tasks_list.append({
                    "id": t.get("id"),
                    "url": t.get("url"),
                    "asr_mode": t.get("asr_mode", "local"),
                    "summary_mode": t.get("summary_mode", "local"),
                    "title": t.get("title", "未命名任务"),
                    "podcast_name": t.get("podcast_name", "未知播客"),
                    "status": t.get("status", "pending"),
                    "progress": t.get("progress", 0),
                    "created_at": t.get("created_at"),
                    "error_message": t.get("error_message"),
                    "like_count": t.get("metadata", {}).get("like_count", 0),
                    "comment_count": t.get("metadata", {}).get("comment_count", 0),
                    "obsidian_synced": t.get("obsidian_synced", False),
                    "image_url": t.get("image_url", ""),
                    "restoring": t.get("restoring", False),
                    "restore_progress": t.get("restore_progress", 0),
                    "metadata": {
                        "pub_date": t.get("metadata", {}).get("pub_date", ""),
                        "source": t.get("metadata", {}).get("source", "")
                    }
                })
            # 按时间逆序排序
            tasks_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return tasks_list

    def get_task(self, task_id: str) -> dict:
        with self.lock:
            data = self._read_data()
            for t in data.get("tasks", []):
                if t.get("id") == task_id:
                    return t
            return None

    def add_task(self, task_id: str, url: str, asr_mode: str = "local", summary_mode: str = "local") -> dict:
        with self.lock:
            data = self._read_data()
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
                "obsidian_synced": False
            }
            data["tasks"].append(new_task)
            self._write_data(data)
            return new_task

    def update_task(self, task_id: str, **kwargs):
        with self.lock:
            data = self._read_data()
            for t in data.get("tasks", []):
                if t.get("id") == task_id:
                    for k, v in kwargs.items():
                        t[k] = v
                    self._write_data(data)
                    return t
            return None

    def delete_task(self, task_id: str) -> bool:
        with self.lock:
            data = self._read_data()
            initial_count = len(data.get("tasks", []))
            data["tasks"] = [t for t in data["tasks"] if t.get("id") != task_id]
            if len(data["tasks"]) < initial_count:
                # Cascade delete paragraphs, cards, and links associated with this podcast
                data["paragraphs"] = [p for p in data.get("paragraphs", []) if p.get("podcast_id") != task_id]
                data["cards"] = [c for c in data.get("cards", []) if c.get("podcast_id") != task_id]
                # Filter out links whose cards were deleted
                remaining_card_ids = {c["id"] for c in data["cards"]}
                data["links"] = [l for l in data.get("links", []) if l.get("source_card_id") in remaining_card_ids and l.get("target_card_id") in remaining_card_ids]
                
                self._write_data(data)
                return True
            return False

    def get_paragraphs_by_podcast(self, podcast_id: str) -> list[dict]:
        with self.lock:
            data = self._read_data()
            return [p for p in data.get("paragraphs", []) if p.get("podcast_id") == podcast_id]

    def delete_paragraphs_by_podcast(self, podcast_id: str):
        with self.lock:
            data = self._read_data()
            if "paragraphs" in data:
                data["paragraphs"] = [p for p in data["paragraphs"] if p.get("podcast_id") != podcast_id]
                self._write_data(data)

    def add_paragraphs(self, paragraphs: list[dict]):
        with self.lock:
            data = self._read_data()
            if "paragraphs" not in data:
                data["paragraphs"] = []
            
            # Prevent duplicates by removing existing paragraphs for these IDs
            new_ids = {p["id"] for p in paragraphs}
            data["paragraphs"] = [p for p in data["paragraphs"] if p["id"] not in new_ids]
            
            data["paragraphs"].extend(paragraphs)
            self._write_data(data)

    def get_all_cards(self) -> list[dict]:
        with self.lock:
            data = self._read_data()
            return data.get("cards", [])

    def get_cards_by_podcast(self, podcast_id: str) -> list[dict]:
        with self.lock:
            data = self._read_data()
            return [c for c in data.get("cards", []) if c.get("podcast_id") == podcast_id]

    def get_card(self, card_id: str) -> dict:
        with self.lock:
            data = self._read_data()
            for c in data.get("cards", []):
                if c.get("id") == card_id:
                    return c
            return None

    def create_card(self, card: dict) -> dict:
        with self.lock:
            data = self._read_data()
            if "cards" not in data:
                data["cards"] = []
            
            # Remove any existing card with the same ID or same paragraph_id to avoid duplication
            data["cards"] = [c for c in data["cards"] if c["id"] != card["id"] and c["paragraph_id"] != card["paragraph_id"]]
            
            data["cards"].append(card)
            self._write_data(data)
            return card

    def update_card(self, card_id: str, **kwargs) -> dict:
        with self.lock:
            data = self._read_data()
            for c in data.get("cards", []):
                if c.get("id") == card_id:
                    for k, v in kwargs.items():
                        c[k] = v
                    self._write_data(data)
                    return c
            return None

    def delete_card(self, card_id: str) -> bool:
        with self.lock:
            data = self._read_data()
            initial_count = len(data.get("cards", []))
            data["cards"] = [c for c in data["cards"] if c.get("id") != card_id]
            if len(data["cards"]) < initial_count:
                # Also delete associated links
                data["links"] = [l for l in data.get("links", []) if l.get("source_card_id") != card_id and l.get("target_card_id") != card_id]
                self._write_data(data)
                return True
            return False

    def get_all_links(self) -> list[dict]:
        with self.lock:
            data = self._read_data()
            return data.get("links", [])

    def create_link(self, link: dict) -> dict:
        with self.lock:
            data = self._read_data()
            if "links" not in data:
                data["links"] = []
            
            # Check if this link already exists
            exists = False
            for l in data["links"]:
                if (l["source_card_id"] == link["source_card_id"] and l["target_card_id"] == link["target_card_id"]) or \
                   (l["source_card_id"] == link["target_card_id"] and l["target_card_id"] == link["source_card_id"]):
                    l["my_synthesis"] = link["my_synthesis"]
                    exists = True
                    break
            
            if not exists:
                data["links"].append(link)
                
            self._write_data(data)
            return link

    def delete_link(self, link_id: str) -> bool:
        with self.lock:
            data = self._read_data()
            initial_count = len(data.get("links", []))
            data["links"] = [l for l in data["links"] if l.get("id") != link_id]
            if len(data["links"]) < initial_count:
                self._write_data(data)
                return True
            return False

# 实例化全局单例数据库对象
db = LocalDatabase()
