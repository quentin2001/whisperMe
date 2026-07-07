import json

class ParagraphRepository:
    def __init__(self, core):
        self.core = core

    def _insert_paragraph_internal(self, c, p: dict):
        sentences = json.dumps(p.get("sentences", []), ensure_ascii=False)
        c.execute('''INSERT OR REPLACE INTO paragraphs 
            (id, podcast_id, start_time, end_time, content, sentences, speaker)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (p.get("id"), p.get("podcast_id"), p.get("start_time"), p.get("end_time"),
             p.get("content"), sentences, p.get("speaker", "")))

    def get_paragraphs_by_podcast(self, podcast_id: str) -> list[dict]:
        c = self.core.conn.cursor()
        c.execute("SELECT * FROM paragraphs WHERE podcast_id=? ORDER BY start_time ASC", (podcast_id,))
        return c.fetchall()

    def delete_paragraphs_by_podcast(self, podcast_id: str):
        with self.core.write_lock:
            c = self.core.conn.cursor()
            c.execute("DELETE FROM paragraphs WHERE podcast_id=?", (podcast_id,))
            self.core.conn.commit()

    def add_paragraphs(self, paragraphs: list[dict]):
        if not paragraphs: return
        with self.core.write_lock:
            c = self.core.conn.cursor()
            for p in paragraphs:
                self._insert_paragraph_internal(c, p)
            self.core.conn.commit()
