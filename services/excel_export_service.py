"""Export syllabi to Excel templates."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime

from services.excel_template_service import ExcelTemplateService
from services.template_service import TemplateEngine


def _safe_filename(value: str) -> str:
    value = str(value or "").strip() or "Course"
    value = re.sub(r"[\\/:*?\"<>|]+", "_", value)
    value = re.sub(r"\s+", "_", value)
    return value[:120]


class ExcelExportService:
    def __init__(self, db):
        self.db = db
        self.template_engine = TemplateEngine(db)
        self.excel_templates = ExcelTemplateService(db)

    def build_context(self, hp_id: int) -> dict:
        return self.template_engine.build_context(hp_id)

    def export_with_template(self, hp_id: int, template_id: int, output_path: str) -> bool:
        context = self.build_context(hp_id)
        self.excel_templates.render(template_id, context, output_path)
        self.db.add_import_export_log(
            type="EXPORT_EXCEL",
            total=1,
            success=1,
            error=0,
            details_json=json.dumps(
                [{"hp_id": hp_id, "template_id": template_id, "path": output_path, "status": "ok"}],
                ensure_ascii=False,
            ),
            user_action=f"Export Excel syllabus hp_id={hp_id}",
        )
        return True

    def export_with_default(self, hp_id: int, output_path: str) -> bool:
        template = self.excel_templates.get_default()
        if not template:
            raise ValueError("No default Excel template is configured")
        return self.export_with_template(hp_id, template["id"], output_path)

    def export_batch(
        self,
        hp_ids: list[int],
        dir_path: str,
        template_id: int | None = None,
        progress_callback=None,
    ) -> dict:
        if template_id is None:
            template = self.excel_templates.get_default()
            if not template:
                raise ValueError("No default Excel template is configured")
            template_id = template["id"]

        results = {"success": 0, "errors": 0, "details": []}
        os.makedirs(dir_path, exist_ok=True)

        for index, hp_id in enumerate(hp_ids, start=1):
            if progress_callback:
                progress_callback(index, len(hp_ids), str(hp_id), "exporting")
            try:
                context = self.build_context(hp_id)
                code = context.get("CourseCode") or f"HP{hp_id}"
                version = context.get("Version") or datetime.now().strftime("%Y%m%d")
                out_path = os.path.join(dir_path, f"{_safe_filename(code)}_{_safe_filename(version)}.xlsx")
                self.excel_templates.render(template_id, context, out_path)
                results["success"] += 1
                results["details"].append({"hp_id": hp_id, "path": out_path, "status": "ok"})
            except Exception as exc:
                results["errors"] += 1
                results["details"].append({"hp_id": hp_id, "status": "error", "error": str(exc)})

        self.db.add_import_export_log(
            type="EXPORT_EXCEL",
            total=len(hp_ids),
            success=results["success"],
            error=results["errors"],
            details_json=json.dumps(results["details"], ensure_ascii=False),
            user_action=f"Batch export Excel {len(hp_ids)} syllabi",
        )
        return results
