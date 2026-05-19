"""CRUD and helper operations for Excel templates."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from services.excel_template_engine import ExcelTemplateEngine


EXCEL_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "excel_templates")


def _ensure_template_dir() -> None:
    os.makedirs(EXCEL_TEMPLATE_DIR, exist_ok=True)


class ExcelTemplateService:
    def __init__(self, db):
        self.db = db
        self.engine = ExcelTemplateEngine()
        _ensure_template_dir()

    def get_all(self) -> list[dict]:
        rows = self.db.conn.execute(
            "SELECT * FROM excel_template ORDER BY la_mac_dinh DESC, ten"
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            try:
                item["placeholder_count"] = len(json.loads(item.get("placeholders") or "[]"))
            except Exception:
                item["placeholder_count"] = 0
            result.append(item)
        return result

    def get_by_id(self, template_id: int) -> Optional[dict]:
        row = self.db.conn.execute("SELECT * FROM excel_template WHERE id=?", (template_id,)).fetchone()
        return dict(row) if row else None

    def get_default(self) -> Optional[dict]:
        row = self.db.conn.execute(
            "SELECT * FROM excel_template WHERE la_mac_dinh=1 ORDER BY id LIMIT 1"
        ).fetchone()
        return dict(row) if row else None

    def upload(self, source_path: str, ten: str, mo_ta: str = "") -> int:
        if not source_path.lower().endswith(".xlsx"):
            raise ValueError("Excel template must be a .xlsx file")

        validation = self.engine.validate_template(source_path)
        if not validation["valid"]:
            errors = []
            for err in validation["errors"]:
                errors.append(f"Sheet: {err['sheet']} Cell: {err['cell']} {err['message']}")
            raise ValueError("Template validation failed:\n" + "\n".join(errors))

        _ensure_template_dir()
        src = Path(source_path)
        stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        dest = os.path.join(EXCEL_TEMPLATE_DIR, f"{stamp}_{src.name}")
        shutil.copy2(source_path, dest)

        placeholders = sorted(
            {p["name"] for p in validation.get("scalars", [])}
            | {p["name"] for p in validation.get("loops", [])}
        )
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.transaction():
            cur = self.db.conn.execute(
                """
                INSERT INTO excel_template(ten, mo_ta, file_path, placeholders, la_mac_dinh, created_at, updated_at)
                VALUES(?,?,?,?,?,?,?)
                """,
                (ten, mo_ta, dest, json.dumps(placeholders, ensure_ascii=False), 0, now, now),
            )
        return cur.lastrowid

    def update_name(self, template_id: int, ten: str, mo_ta: str = "") -> None:
        with self.db.transaction():
            self.db.conn.execute(
                "UPDATE excel_template SET ten=?, mo_ta=?, updated_at=? WHERE id=?",
                (ten, mo_ta, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), template_id),
            )

    def delete(self, template_id: int) -> None:
        tpl = self.get_by_id(template_id)
        if not tpl:
            return
        with self.db.transaction():
            self.db.conn.execute("DELETE FROM excel_template WHERE id=?", (template_id,))

        file_path = tpl.get("file_path")
        if file_path and os.path.exists(file_path):
            still_used = self.db.conn.execute(
                "SELECT id FROM excel_template WHERE file_path=?", (file_path,)
            ).fetchone()
            if not still_used:
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    def set_default(self, template_id: int) -> None:
        with self.db.transaction():
            self.db.conn.execute("UPDATE excel_template SET la_mac_dinh=0")
            self.db.conn.execute(
                "UPDATE excel_template SET la_mac_dinh=1, updated_at=? WHERE id=?",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), template_id),
            )

    def validate_template_file(self, template_path: str, context: dict | None = None) -> dict:
        return self.engine.validate_template(template_path, context)

    def scan_placeholders(self, template_path: str) -> dict:
        return self.engine.scan_placeholders(template_path)

    def create_default_template(self, output_path: str) -> str:
        return self.engine.create_default_template(output_path)

    def create_placeholder_catalog(self, output_path: str) -> str:
        return self.engine.create_placeholder_catalog(output_path)

    def render(self, template_id: int, context: dict, output_path: str) -> None:
        tpl = self.get_by_id(template_id)
        if not tpl:
            raise ValueError(f"Excel template id={template_id} does not exist")
        template_path = tpl.get("file_path")
        if not template_path or not os.path.exists(template_path):
            raise FileNotFoundError(f"Excel template file does not exist: {template_path}")
        self.engine.render(template_path, context, output_path)
