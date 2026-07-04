from datetime import datetime

class InsightRepository:
    def __init__(self, core):
        self.core = core

    def _insert_insight_internal(self, c, insight: dict):
        c.execute('''INSERT OR REPLACE INTO insights 
            (id, podcast_id, original_text, refined_content, review_count, next_review_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (insight.get("id"), insight.get("podcast_id"), insight.get("original_text", ""),
             insight.get("refined_content", ""), insight.get("review_count", 0),
             insight.get("next_review_date", ""), insight.get("status", "ACTIVE"),
             insight.get("created_at", datetime.now().isoformat())))

    def get_all_insights(self) -> list[dict]:
        c = self.core.conn.cursor()
        c.execute("SELECT * FROM insights WHERE status != 'DELETED' ORDER BY created_at DESC")
        return c.fetchall()

    def get_insights_for_review(self) -> list[dict]:
        c = self.core.conn.cursor()
        c.execute("SELECT * FROM insights WHERE status = 'ACTIVE' ORDER BY RANDOM() LIMIT 5")
        return c.fetchall()

    def create_insight(self, insight: dict) -> dict:
        import uuid
        if "id" not in insight or not insight["id"]:
            insight["id"] = str(uuid.uuid4())
        if "created_at" not in insight:
            insight["created_at"] = datetime.now().isoformat()
        with self.core.write_lock:
            c = self.core.conn.cursor()
            self._insert_insight_internal(c, insight)
            self.core.conn.commit()
            return insight

    def update_insight(self, insight_id: str, **kwargs) -> dict:
        with self.core.write_lock:
            c = self.core.conn.cursor()
            c.execute("SELECT * FROM insights WHERE id=?", (insight_id,))
            row = c.fetchone()
            if not row:
                return None
            for k, v in kwargs.items():
                row[k] = v
            self._insert_insight_internal(c, row)
            self.core.conn.commit()
            
            c.execute("SELECT * FROM insights WHERE id=?", (insight_id,))
            return c.fetchone()

    def delete_insight(self, insight_id: str) -> bool:
        with self.core.write_lock:
            c = self.core.conn.cursor()
            c.execute("UPDATE insights SET status = 'DELETED' WHERE id=?", (insight_id,))
            if c.rowcount > 0:
                self.core.conn.commit()
                return True
            return False
