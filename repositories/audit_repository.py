import json
from datetime import datetime
from typing import Optional

from .base_repository import BaseRepository


class AuditRepository(BaseRepository):
    def log(
        self,
        hp_id: Optional[int],
        table_name: str,
        action: str = "UPDATE",
        record_id: Optional[int] = None,
        details: Optional[dict] = None,
    ) -> int:
        payload = {
            "hp_id": hp_id,
            "table_name": table_name,
            "record_id": record_id,
            "action": action,
            "details": json.dumps(details or {}, ensure_ascii=False),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        with self.db.transaction():
            return self._safe_insert("audit_log", payload)

    def get_history(self, hp_id: Optional[int] = None, limit: int = 100) -> list[dict]:
        limit = max(1, int(limit or 100))
        if hp_id is not None:
            return self._fetch_all(
                "SELECT * FROM audit_log WHERE hp_id=? ORDER BY created_at DESC, id DESC LIMIT ?",
                (hp_id, limit),
            )
        return self._fetch_all(
            "SELECT * FROM audit_log ORDER BY created_at DESC, id DESC LIMIT ?",
            (limit,),
        )

