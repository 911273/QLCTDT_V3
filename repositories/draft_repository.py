from datetime import datetime, timedelta
from typing import Optional

from .base_repository import BaseRepository


class DraftRepository(BaseRepository):
    def save(self, hp_id: int, data_json: str, ttl_days: int = 7) -> None:
        now = datetime.now()
        expires = now + timedelta(days=ttl_days)
        with self.db.transaction():
            self.conn.execute(
                """
                INSERT OR REPLACE INTO temp_draft (hp_id, data_json, updated_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    hp_id,
                    data_json,
                    now.strftime("%Y-%m-%d %H:%M:%S"),
                    expires.strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )

    def get(self, hp_id: int) -> Optional[dict]:
        return self._fetch_one("SELECT * FROM temp_draft WHERE hp_id=?", (hp_id,))

    def delete(self, hp_id: int) -> None:
        with self.db.transaction():
            self.conn.execute("DELETE FROM temp_draft WHERE hp_id=?", (hp_id,))

    def cleanup_expired(self) -> int:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.transaction():
            cur = self.conn.execute("DELETE FROM temp_draft WHERE expires_at < ?", (now,))
            return cur.rowcount

