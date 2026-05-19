"""End-to-end syllabus consistency validation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.template_service import TemplateEngine


@dataclass(frozen=True)
class ValidationIssue:
    level: str
    section: str
    message: str

    def as_dict(self) -> dict:
        return {"level": self.level, "section": self.section, "message": self.message}


class SyllabusWorkflowValidator:
    """Validate the practical I-IX syllabus workflow from DB/export context."""

    def __init__(self, db: Any):
        self.db = db
        self.template_engine = TemplateEngine(db)

    def validate(self, hp_id: int) -> dict:
        context = self.template_engine.build_context(hp_id)
        issues: list[ValidationIssue] = []

        self._validate_course_info(context, issues)
        self._validate_objectives(context, issues)
        self._validate_clos(context, issues)
        self._validate_materials(context, issues)
        self._validate_content(context, issues)
        self._validate_assessment(context, issues)
        self._validate_revision(context, issues)
        self._validate_approval(context, issues)

        return {
            "valid": not any(issue.level == "error" for issue in issues),
            "issues": [issue.as_dict() for issue in issues],
            "context": context,
        }

    def _validate_course_info(self, context: dict, issues: list[ValidationIssue]) -> None:
        for key in ("CourseName", "CourseCode", "Credits"):
            if not context.get(key):
                issues.append(ValidationIssue("error", "I.course_info", f"Missing required field: {key}"))
        for key in ("HoursLT", "HoursBT", "HoursTH", "HoursTL", "HoursTuHoc", "TotalHours"):
            value = context.get(key) or 0
            try:
                if float(value) < 0:
                    issues.append(ValidationIssue("error", "I.course_info", f"Negative hour value: {key}"))
            except (TypeError, ValueError):
                issues.append(ValidationIssue("error", "I.course_info", f"Invalid numeric hour value: {key}"))

    def _validate_objectives(self, context: dict, issues: list[ValidationIssue]) -> None:
        if not context.get("Objectives"):
            issues.append(ValidationIssue("warning", "III.objectives", "No objectives defined"))

    def _validate_clos(self, context: dict, issues: list[ValidationIssue]) -> None:
        clos = context.get("CLOs") or []
        if not clos:
            issues.append(ValidationIssue("error", "IV.clos", "No CLO defined"))
            return
        seen = set()
        for row in clos:
            code = (row.get("Code") or "").strip()
            if not code:
                issues.append(ValidationIssue("error", "IV.clos", "CLO without code"))
                continue
            if code in seen:
                issues.append(ValidationIssue("error", "IV.clos", f"Duplicate CLO code: {code}"))
            seen.add(code)
            if not row.get("PLO"):
                issues.append(ValidationIssue("warning", "IV.clos", f"CLO {code} has no PLO mapping"))
            if row.get("Level") and row.get("Level") not in {"I", "R", "M"}:
                issues.append(ValidationIssue("error", "IV.clos", f"CLO {code} has invalid I/R/M level"))

    def _validate_materials(self, context: dict, issues: list[ValidationIssue]) -> None:
        if not (context.get("MainRefs") or context.get("SupRefs") or context.get("OtherRefs")):
            issues.append(ValidationIssue("warning", "V.materials", "No learning material defined"))

    def _validate_content(self, context: dict, issues: list[ValidationIssue]) -> None:
        rows = (context.get("ContentLT") or []) + (context.get("ContentTH") or [])
        if not rows:
            issues.append(ValidationIssue("warning", "VI.course_content", "No course content rows defined"))
        for index, row in enumerate(rows, start=1):
            total = sum(float(row.get(key) or 0) for key in ("gio_lt", "gio_bt", "gio_tl", "gio_th_tn", "gio_th"))
            if total < 0:
                issues.append(ValidationIssue("error", "VI.course_content", f"Negative hour total at row {index}"))

    def _validate_assessment(self, context: dict, issues: list[ValidationIssue]) -> None:
        rows = context.get("AssessmentRows") or []
        if not rows:
            issues.append(ValidationIssue("warning", "VII.assessment", "No assessment rows defined"))
            return
        weights = []
        for row in rows:
            raw = row.get("ty_trong") or row.get("ty_trong_nhom") or 0
            try:
                weights.append(float(raw))
            except (TypeError, ValueError):
                issues.append(ValidationIssue("error", "VII.assessment", f"Invalid assessment weight: {raw}"))
        if weights and abs(sum(weights) - 100.0) > 0.01:
            issues.append(ValidationIssue("error", "VII.assessment", f"Assessment weights total {sum(weights):.2f}, expected 100"))

    def _validate_revision(self, context: dict, issues: list[ValidationIssue]) -> None:
        if not context.get("History"):
            issues.append(ValidationIssue("warning", "VIII.revision_history", "No revision history defined"))

    def _validate_approval(self, context: dict, issues: list[ValidationIssue]) -> None:
        if not context.get("SignerLeftName"):
            issues.append(ValidationIssue("warning", "IX.approval_info", "Missing author signer name"))
        if not context.get("SignerRightName"):
            issues.append(ValidationIssue("warning", "IX.approval_info", "Missing approval signer name"))
