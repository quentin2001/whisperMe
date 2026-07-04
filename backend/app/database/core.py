import os
import json
import threading
import sqlite3
from app.config import PROJECT_DIR, STORAGE_BASE

DB_FILE_PATH = os.path.join(STORAGE_BASE, "whisperMe.db")

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        val = row[idx]
        if isinstance(val, str):
            if (val.startswith('{') and val.endswith('}')) or (val.startswith('[') and val.endswith(']')):
                try:
                    val = json.loads(val)
                except Exception:
                    pass
        d[col[0]] = val
    return d

class DatabaseCore:
    def __init__(self):
        self._local = threading.local()
        self.write_lock = threading.Lock()
        
    @property
    def conn(self):
        if not hasattr(self._local, "conn"):
            # Enable WAL mode safely and use a timeout
            try:
                conn = sqlite3.connect(DB_FILE_PATH, check_same_thread=False, timeout=30.0)
                conn.row_factory = dict_factory
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA foreign_keys=ON;")
                conn.execute("PRAGMA busy_timeout=30000;")
                self._local.conn = conn
            except Exception as e:
                print(f"❌ [DB CORE] Failed to connect to database: {e}")
                raise e
        return self._local.conn
