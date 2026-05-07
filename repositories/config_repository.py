from typing import Optional

from .base_repository import BaseRepository


class ConfigRepository(BaseRepository):
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        row = self.conn.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set(self, key: str, value) -> None:
        with self.db.transaction():
            self.conn.execute(
                "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                (key, str(value)),
            )

    def get_many(self, keys: list[str]) -> dict:
        if not keys:
            return {}
        placeholders = ",".join("?" for _ in keys)
        rows = self.conn.execute(
            f"SELECT key, value FROM config WHERE key IN ({placeholders})", keys
        ).fetchall()
        return {r["key"]: r["value"] for r in rows}

    def get_all(self) -> dict:
        rows = self.conn.execute("SELECT key, value FROM config ORDER BY key").fetchall()
        return {r["key"]: r["value"] for r in rows}

