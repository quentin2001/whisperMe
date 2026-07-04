import json
from datetime import datetime

class SpeakerRepository:
    def __init__(self, core):
        self.core = core

    def get_all_speakers(self) -> list[dict]:
        """获取全局声纹库列表（不返回 embedding 向量）"""
        c = self.core.conn.cursor()
        c.execute("SELECT id, name, sample_count, last_seen_at, created_at, updated_at FROM speakers ORDER BY sample_count DESC, name ASC")
        return c.fetchall()

    def get_speaker(self, name: str) -> dict:
        """按名字查询单个声纹（含 embedding）"""
        c = self.core.conn.cursor()
        c.execute("SELECT * FROM speakers WHERE name=?", (name,))
        return c.fetchone()

    def get_all_speakers_with_embeddings(self) -> dict:
        """获取全局声纹库 {name: embedding_list}，供匹配使用"""
        c = self.core.conn.cursor()
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
