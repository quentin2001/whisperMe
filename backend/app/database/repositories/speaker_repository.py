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

    def upsert_speaker(self, name: str, embedding: list[float], sample_count: int = 1) -> bool:
        """插入或更新声纹（存在则加权平均 embedding）"""
        with self.core.write_lock:
            c = self.core.conn.cursor()
            existing = self.get_speaker(name)
            now = datetime.now().isoformat()
            if existing:
                old_emb = existing["embedding"]
                if isinstance(old_emb, str):
                    try: old_emb = json.loads(old_emb)
                    except: old_emb = []
                old_count = existing.get("sample_count", 1)
                new_count = old_count + sample_count
                # 加权平均
                weighted = [(old_emb[i] * old_count + embedding[i] * sample_count) / new_count
                            for i in range(min(len(old_emb), len(embedding)))]
                c.execute(
                    "UPDATE speakers SET embedding=?, sample_count=?, updated_at=? WHERE name=?",
                    (json.dumps(weighted, ensure_ascii=False), new_count, now, name)
                )
            else:
                c.execute(
                    "INSERT INTO speakers (name, embedding, sample_count, last_seen_at, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, json.dumps(embedding, ensure_ascii=False), sample_count, now, now, now)
                )
            self.core.conn.commit()
            return True

    def merge_speakers(self, source_name: str, target_name: str) -> bool:
        """合并两个说话人（source → target），加权平均 embedding"""
        source = self.get_speaker(source_name)
        target = self.get_speaker(target_name)
        if not source or not target:
            return False
        with self.core.write_lock:
            c = self.core.conn.cursor()
            s_emb = source["embedding"]
            if isinstance(s_emb, str):
                try: s_emb = json.loads(s_emb)
                except: s_emb = []
            t_emb = target["embedding"]
            if isinstance(t_emb, str):
                try: t_emb = json.loads(t_emb)
                except: t_emb = []
            s_count = source.get("sample_count", 1)
            t_count = target.get("sample_count", 1)
            new_count = s_count + t_count
            weighted = [(s_emb[i] * s_count + t_emb[i] * t_count) / new_count
                        for i in range(min(len(s_emb), len(t_emb)))]
            now = datetime.now().isoformat()
            c.execute(
                "UPDATE speakers SET embedding=?, sample_count=?, updated_at=? WHERE name=?",
                (json.dumps(weighted, ensure_ascii=False), new_count, now, target_name)
            )
            c.execute("DELETE FROM speakers WHERE name=?", (source_name,))
            self.core.conn.commit()
            return True

    def delete_speaker(self, name: str) -> bool:
        """从声纹库删除指定说话人"""
        existing = self.get_speaker(name)
        if not existing:
            return False
        with self.core.write_lock:
            c = self.core.conn.cursor()
            c.execute("DELETE FROM speakers WHERE name=?", (name,))
            self.core.conn.commit()
            return True
