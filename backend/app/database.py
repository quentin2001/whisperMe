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
                    json.dump({"tasks": []}, f, ensure_ascii=False, indent=2)

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
                    "title": t.get("title", "未命名任务"),
                    "podcast_name": t.get("podcast_name", "未知播客"),
                    "status": t.get("status", "pending"),
                    "progress": t.get("progress", 0),
                    "created_at": t.get("created_at"),
                    "error_message": t.get("error_message"),
                    "like_count": t.get("metadata", {}).get("like_count", 0),
                    "comment_count": t.get("metadata", {}).get("comment_count", 0),
                    "obsidian_synced": t.get("obsidian_synced", False)
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

    def add_task(self, task_id: str, url: str, asr_mode: str = "local") -> dict:
        with self.lock:
            data = self._read_data()
            new_task = {
                "id": task_id,
                "url": url,
                "asr_mode": asr_mode,
                "title": "等待解析中...",
                "podcast_name": "等待解析...",
                "status": "pending",
                "progress": 0.0,
                "error_message": None,
                "created_at": datetime.now().isoformat(),
                "metadata": {
                    "title": "等待解析...",
                    "podcast_name": "等待解析...",
                    "shownotes": "",
                    "like_count": 0,
                    "comment_count": 0,
                    "comments": [],
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
                self._write_data(data)
                return True
            return False

# 实例化全局单例数据库对象
db = LocalDatabase()
