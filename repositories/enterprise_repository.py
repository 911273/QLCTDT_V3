"""Metadata-driven repository for the enterprise academic schema."""

from __future__ import annotations

import json
import re
from typing import Any

from core.enterprise_schema import ACADEMIC_SYSTEM_SCHEMA, now_text


class EnterpriseRepository:
    """Generic CRUD repository guarded by the enterprise schema registry."""

    def __init__(self, db: Any):
        self.db = db
        self.conn = db.conn
        self._allowed_tables = set(ACADEMIC_SYSTEM_SCHEMA)
        self._allowed_tables.update(
            {
                "academic_entity_meta",
                "academic_field_meta",
                "academic_schema_upgrade_log",
                "legacy_academic_bridge",
            }
        )

    def list_entities(self) -> list[dict]:
        rows = self.conn.execute(
            """
            SELECT * FROM academic_entity_meta
            ORDER BY form_order, entity_name
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def form_schema(self, entity_name: str) -> list[dict]:
        self._validate_table(entity_name)
        rows = self.conn.execute(
            """
            SELECT * FROM academic_field_meta
            WHERE entity_name=?
            ORDER BY field_order
            """,
            (entity_name,),
        ).fetchall()
        return [dict(row) for row in rows]

    def get(self, table: str, record_id: int) -> dict | None:
        self._validate_table(table)
        row = self.conn.execute(
            f"SELECT * FROM {self._quote(table)} WHERE id=?",
            (record_id,),
        ).fetchone()
        return dict(row) if row else None

    def list(self, table: str, limit: int = 100, offset: int = 0, search: str = "") -> list[dict]:
        self._validate_table(table)
        cols = self._columns(table)
        params: list[Any] = []
        where = ""
        if search:
            text_cols = [col for col in cols if col.endswith("_code") or "name" in col or col in {"title", "description"}]
            if text_cols:
                like = f"%{search}%"
                where = " WHERE " + " OR ".join(f"{self._quote(col)} LIKE ?" for col in text_cols)
                params.extend([like] * len(text_cols))
        params.extend([limit, offset])
        rows = self.conn.execute(
            f"SELECT * FROM {self._quote(table)}{where} ORDER BY id DESC LIMIT ? OFFSET ?",
            params,
        ).fetchall()
        return [dict(row) for row in rows]

    def insert(self, table: str, data: dict) -> int:
        self._validate_table(table)
        safe = self._prepare_data(table, data, include_id=False)
        if "created_at" in self._columns(table) and not safe.get("created_at"):
            safe["created_at"] = now_text()
        if "updated_at" in self._columns(table) and not safe.get("updated_at"):
            safe["updated_at"] = now_text()
        cols = list(safe)
        values = [safe[col] for col in cols]
        placeholders = ",".join("?" for _ in cols)
        with self.db.transaction():
            cur = self.conn.execute(
                f"INSERT INTO {self._quote(table)}({','.join(self._quote(c) for c in cols)}) VALUES({placeholders})",
                values,
            )
        return int(cur.lastrowid)

    def update(self, table: str, record_id: int, data: dict) -> None:
        self._validate_table(table)
        safe = self._prepare_data(table, data, include_id=False)
        if "updated_at" in self._columns(table):
            safe["updated_at"] = now_text()
        if not safe:
            return
        sets = ",".join(f"{self._quote(col)}=?" for col in safe)
        with self.db.transaction():
            self.conn.execute(
                f"UPDATE {self._quote(table)} SET {sets} WHERE id=?",
                list(safe.values()) + [record_id],
            )

    def upsert_by_unique(self, table: str, unique_field: str, unique_value: Any, data: dict) -> int:
        self._validate_table(table)
        self._validate_column(table, unique_field)
        row = self.conn.execute(
            f"SELECT id FROM {self._quote(table)} WHERE {self._quote(unique_field)}=?",
            (unique_value,),
        ).fetchone()
        payload = dict(data)
        payload[unique_field] = unique_value
        if row:
            self.update(table, int(row["id"]), payload)
            return int(row["id"])
        return self.insert(table, payload)

    def delete(self, table: str, record_id: int) -> None:
        self._validate_table(table)
        with self.db.transaction():
            self.conn.execute(f"DELETE FROM {self._quote(table)} WHERE id=?", (record_id,))

    def link_legacy(self, legacy_table: str, legacy_id: int, enterprise_table: str, enterprise_id: int) -> None:
        self._validate_table(enterprise_table)
        now = now_text()
        with self.db.transaction():
            self.conn.execute(
                """
                INSERT INTO legacy_academic_bridge(legacy_table, legacy_id, enterprise_table, enterprise_id, created_at, updated_at)
                VALUES(?,?,?,?,?,?)
                ON CONFLICT(legacy_table, legacy_id, enterprise_table) DO UPDATE SET
                    enterprise_id=excluded.enterprise_id,
                    updated_at=excluded.updated_at
                """,
                (legacy_table, legacy_id, enterprise_table, enterprise_id, now, now),
            )

    def enterprise_id_for_legacy(self, legacy_table: str, legacy_id: int, enterprise_table: str) -> int | None:
        row = self.conn.execute(
            """
            SELECT enterprise_id FROM legacy_academic_bridge
            WHERE legacy_table=? AND legacy_id=? AND enterprise_table=?
            """,
            (legacy_table, legacy_id, enterprise_table),
        ).fetchone()
        return int(row["enterprise_id"]) if row else None

    def _prepare_data(self, table: str, data: dict, include_id: bool) -> dict:
        cols = self._columns(table)
        safe = {}
        json_fields = {
            name for name, typ in ACADEMIC_SYSTEM_SCHEMA.get(table, {}).items() if typ.upper() == "JSON"
        }
        for key, value in data.items():
            if key == "id" and not include_id:
                continue
            if key not in cols:
                continue
            if key in json_fields and value is not None and not isinstance(value, str):
                value = json.dumps(value, ensure_ascii=False)
            safe[key] = value
        return safe

    def _columns(self, table: str) -> set[str]:
        self._validate_table(table)
        return {row[1] for row in self.conn.execute(f"PRAGMA table_info({self._quote(table)})").fetchall()}

    def _validate_table(self, table: str) -> None:
        if table not in self._allowed_tables:
            raise ValueError(f"Unauthorized enterprise table: {table}")
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", table):
            raise ValueError(f"Unsafe table identifier: {table}")

    def _validate_column(self, table: str, column: str) -> None:
        if column not in self._columns(table):
            raise ValueError(f"Unknown column {column} for table {table}")

    @staticmethod
    def _quote(identifier: str) -> str:
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", identifier):
            raise ValueError(f"Unsafe SQL identifier: {identifier}")
        return f'"{identifier}"'
