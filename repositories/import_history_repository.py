from datetime import datetime

from .base_repository import BaseRepository


class ImportHistoryRepository(BaseRepository):
    def add(
        self,
        type: str,
        total: int,
        success: int,
        error: int,
        details_json: str,
        user_action: str = "",
    ) -> int:
        with self.db.transaction():
            cur = self.conn.execute(
                """
                INSERT INTO import_export_history
                (type, timestamp, total_files, success_count, error_count, details_json, user_action)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    type,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    total,
                    success,
                    error,
                    details_json,
                    user_action,
                ),
            )
            return cur.lastrowid

    def get_history(self, limit: int = 50) -> list[dict]:
        limit = max(1, int(limit or 50))
        return self._fetch_all(
            "SELECT * FROM import_export_history ORDER BY timestamp DESC, id DESC LIMIT ?",
            (limit,),
        )

