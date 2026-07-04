from datetime import datetime

class BoardRepository:
    def __init__(self, core):
        self.core = core

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

    # ==================== CARDS ====================
    def get_all_cards(self) -> list[dict]:
        c = self.core.conn.cursor()
        c.execute("SELECT * FROM cards")
        return c.fetchall()

    def get_cards_by_podcast(self, podcast_id: str) -> list[dict]:
        c = self.core.conn.cursor()
        c.execute("SELECT * FROM cards WHERE podcast_id=?", (podcast_id,))
        return c.fetchall()

    def get_card(self, card_id: str) -> dict:
        c = self.core.conn.cursor()
        c.execute("SELECT * FROM cards WHERE id=?", (card_id,))
        return c.fetchone()

    def create_card(self, card: dict) -> dict:
        with self.core.write_lock:
            c = self.core.conn.cursor()
            pid = card.get("paragraph_id")
            if pid:
                c.execute("DELETE FROM cards WHERE paragraph_id=?", (pid,))
            
            self._insert_card_internal(c, card)
            self.core.conn.commit()
            return card

    def update_card(self, card_id: str, **kwargs) -> dict:
        with self.core.write_lock:
            c = self.core.conn.cursor()
            c.execute("SELECT * FROM cards WHERE id=?", (card_id,))
            row = c.fetchone()
            if not row:
                return None
            for k, v in kwargs.items():
                row[k] = v
            self._insert_card_internal(c, row)
            self.core.conn.commit()
            
            c.execute("SELECT * FROM cards WHERE id=?", (card_id,))
            return c.fetchone()

    def delete_card(self, card_id: str) -> bool:
        with self.core.write_lock:
            c = self.core.conn.cursor()
            c.execute("DELETE FROM cards WHERE id=?", (card_id,))
            if c.rowcount > 0:
                c.execute('''DELETE FROM links 
                             WHERE source_card_id=? OR target_card_id=?''', 
                          (card_id, card_id))
                self.core.conn.commit()
                return True
            return False

    # ==================== LINKS ====================
    def get_all_links(self) -> list[dict]:
        c = self.core.conn.cursor()
        c.execute("SELECT * FROM links")
        return c.fetchall()

    def create_link(self, link: dict) -> dict:
        with self.core.write_lock:
            c = self.core.conn.cursor()
            c.execute('''SELECT * FROM links 
                         WHERE (source_card_id=? AND target_card_id=?) 
                         OR (source_card_id=? AND target_card_id=?)''',
                      (link["source_card_id"], link["target_card_id"],
                       link["target_card_id"], link["source_card_id"]))
            row = c.fetchone()
            if row:
                row["my_synthesis"] = link.get("my_synthesis", "")
                self._insert_link_internal(c, row)
                self.core.conn.commit()
                return row
            else:
                import uuid
                if "id" not in link:
                    link["id"] = str(uuid.uuid4())
                self._insert_link_internal(c, link)
                self.core.conn.commit()
                return link

    def delete_link(self, link_id: str) -> bool:
        with self.core.write_lock:
            c = self.core.conn.cursor()
            c.execute("DELETE FROM links WHERE id=?", (link_id,))
            if c.rowcount > 0:
                self.core.conn.commit()
                return True
            return False

    # ==================== BOARDS ====================
    def get_all_boards(self) -> list[dict]:
        c = self.core.conn.cursor()
        c.execute("SELECT * FROM boards ORDER BY created_at ASC")
        return c.fetchall()

    def create_board(self, board_id: str, name: str) -> dict:
        with self.core.write_lock:
            c = self.core.conn.cursor()
            board = {
                "id": board_id,
                "name": name,
                "created_at": datetime.now().isoformat()
            }
            c.execute("INSERT INTO boards (id, name, created_at) VALUES (?, ?, ?)", 
                      (board["id"], board["name"], board["created_at"]))
            self.core.conn.commit()
            return board

    def get_cards_by_board(self, board_id: str) -> list[dict]:
        c = self.core.conn.cursor()
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
        with self.core.write_lock:
            c = self.core.conn.cursor()
            c.execute("INSERT OR IGNORE INTO board_cards (board_id, card_id, pos_x, pos_y) VALUES (?, ?, ?, ?)",
                      (board_id, card_id, pos_x, pos_y))
            self.core.conn.commit()

    def update_board_card_position(self, board_id: str, card_id: str, pos_x: float, pos_y: float):
        with self.core.write_lock:
            c = self.core.conn.cursor()
            c.execute("UPDATE board_cards SET pos_x=?, pos_y=? WHERE board_id=? AND card_id=?",
                      (pos_x, pos_y, board_id, card_id))
            self.core.conn.commit()
