"""Enterprise academic domain schema and SQLite migration helpers.

This module is intentionally metadata-first. UI forms, import/export mapping,
and repository validation can read the same schema instead of hardcoding field
lists in each screen.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any, Iterable


ACADEMIC_SYSTEM_SCHEMA: dict[str, dict[str, str]] = {
    "department": {
        "id": "INTEGER PRIMARY KEY",
        "department_code": "TEXT UNIQUE",
        "department_name_vi": "TEXT",
        "department_name_en": "TEXT",
        "description": "TEXT",
        "phone": "TEXT",
        "email": "TEXT",
        "website": "TEXT",
        "status": "TEXT",
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
    },
    "instructor": {
        "id": "INTEGER PRIMARY KEY",
        "department_id": "INTEGER",
        "staff_code": "TEXT UNIQUE",
        "full_name": "TEXT",
        "academic_rank": "TEXT",
        "degree": "TEXT",
        "email": "TEXT",
        "phone": "TEXT",
        "date_of_birth": "DATE",
        "specialization": "TEXT",
        "training_country": "TEXT",
        "graduation_year": "INTEGER",
        "employment_type": "TEXT",
        "status": "TEXT",
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
    },
    "material_library": {
        "id": "INTEGER PRIMARY KEY",
        "material_code": "TEXT UNIQUE",
        "title": "TEXT",
        "authors": "TEXT",
        "publisher": "TEXT",
        "published_year": "INTEGER",
        "edition": "TEXT",
        "isbn": "TEXT",
        "doi": "TEXT",
        "url": "TEXT",
        "material_type": "TEXT",
        "language": "TEXT",
        "quantity": "INTEGER",
        "library_location": "TEXT",
        "status": "TEXT",
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
    },
    "program": {
        "id": "INTEGER PRIMARY KEY",
        "department_id": "INTEGER",
        "program_code": "TEXT UNIQUE",
        "program_name_vi": "TEXT",
        "program_name_en": "TEXT",
        "education_level": "TEXT",
        "degree_name": "TEXT",
        "training_duration_years": "REAL",
        "total_credits": "INTEGER",
        "admission_requirements": "TEXT",
        "graduation_requirements": "TEXT",
        "program_philosophy": "TEXT",
        "program_mission": "TEXT",
        "program_vision": "TEXT",
        "general_objectives": "TEXT",
        "accreditation_standard": "TEXT",
        "status": "TEXT",
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
    },
    "major": {
        "id": "INTEGER PRIMARY KEY",
        "program_id": "INTEGER",
        "major_code": "TEXT UNIQUE",
        "major_name_vi": "TEXT",
        "major_name_en": "TEXT",
        "description": "TEXT",
        "total_credits": "INTEGER",
        "status": "TEXT",
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
    },
    "peo": {
        "id": "INTEGER PRIMARY KEY",
        "program_id": "INTEGER",
        "peo_code": "TEXT UNIQUE",
        "description": "TEXT",
        "target_year_after_graduation": "INTEGER",
        "stakeholders": "JSON",
        "measurement_method": "TEXT",
        "review_cycle_years": "INTEGER",
        "status": "TEXT",
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
    },
    "plo": {
        "id": "INTEGER PRIMARY KEY",
        "program_id": "INTEGER",
        "plo_code": "TEXT UNIQUE",
        "description": "TEXT",
        "domain": "TEXT",
        "bloom_level": "TEXT",
        "assessment_strategy": "TEXT",
        "target_attainment": "REAL",
        "evaluation_cycle": "TEXT",
        "status": "TEXT",
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
    },
    "pi": {
        "id": "INTEGER PRIMARY KEY",
        "plo_id": "INTEGER",
        "pi_code": "TEXT UNIQUE",
        "description": "TEXT",
        "performance_level": "TEXT",
        "weight": "REAL",
        "measurement_method": "TEXT",
        "target_score": "REAL",
        "assessment_frequency": "TEXT",
        "rubric_id": "INTEGER",
        "status": "TEXT",
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
    },
    "course": {
        "id": "INTEGER PRIMARY KEY",
        "program_id": "INTEGER",
        "major_id": "INTEGER",
        "course_code": "TEXT UNIQUE",
        "course_name_vi": "TEXT",
        "course_name_en": "TEXT",
        "knowledge_block": "TEXT",
        "course_type": "TEXT",
        "course_nature": "TEXT",
        "mandatory": "BOOLEAN",
        "credits": "INTEGER",
        "class_hours": "INTEGER",
        "theory_hours": "INTEGER",
        "practice_hours": "INTEGER",
        "discussion_hours": "INTEGER",
        "project_hours": "INTEGER",
        "internship_hours": "INTEGER",
        "self_study_hours": "INTEGER",
        "total_hours": "INTEGER",
        "semester": "INTEGER",
        "teaching_mode": "TEXT",
        "prerequisite_courses": "JSON",
        "parallel_courses": "JSON",
        "replacement_course": "TEXT",
        "summary": "TEXT",
        "status": "TEXT",
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
    },
    "syllabus": {
        "id": "INTEGER PRIMARY KEY",
        "course_id": "INTEGER",
        "program_id": "INTEGER",
        "major_id": "INTEGER",
        "version": "TEXT",
        "title": "TEXT",
        "summary": "TEXT",
        "content_type": "TEXT",
        "status": "TEXT",
        "created_by": "INTEGER",
        "approved_by": "INTEGER",
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
        "approved_date": "DATE",
    },
    "syllabus_course_info": {
        "syllabus_id": "INTEGER PRIMARY KEY",
        "department": "TEXT",
        "education_level": "TEXT",
        "course_type": "TEXT",
        "course_nature": "TEXT",
        "teaching_mode": "TEXT",
        "class_hours": "INTEGER",
        "theory_hours": "INTEGER",
        "practice_hours": "INTEGER",
        "discussion_hours": "INTEGER",
        "project_hours": "INTEGER",
        "internship_hours": "INTEGER",
        "self_study_hours": "INTEGER",
        "total_hours": "INTEGER",
    },
    "syllabus_main_lecturer": {
        "syllabus_id": "INTEGER PRIMARY KEY",
        "instructor_id": "INTEGER",
        "academic_rank": "TEXT",
        "degree": "TEXT",
        "full_name": "TEXT",
        "phone": "TEXT",
        "email": "TEXT",
    },
    "syllabus_sub_lecturer": {
        "id": "INTEGER PRIMARY KEY",
        "syllabus_id": "INTEGER",
        "instructor_id": "INTEGER",
        "academic_rank": "TEXT",
        "degree": "TEXT",
        "full_name": "TEXT",
        "phone": "TEXT",
        "email": "TEXT",
    },
    "syllabus_prerequisite": {
        "id": "INTEGER PRIMARY KEY",
        "syllabus_id": "INTEGER",
        "course_code": "TEXT",
        "course_name": "TEXT",
    },
    "syllabus_parallel_course": {
        "id": "INTEGER PRIMARY KEY",
        "syllabus_id": "INTEGER",
        "course_code": "TEXT",
        "course_name": "TEXT",
    },
    "syllabus_replacement_course": {
        "id": "INTEGER PRIMARY KEY",
        "syllabus_id": "INTEGER",
        "course_code": "TEXT",
        "course_name": "TEXT",
    },
    "syllabus_objective": {
        "id": "INTEGER PRIMARY KEY",
        "syllabus_id": "INTEGER",
        "objective_no": "TEXT",
        "description": "TEXT",
        "plo_code": "TEXT",
    },
    "clo": {
        "id": "INTEGER PRIMARY KEY",
        "syllabus_id": "INTEGER",
        "course_id": "INTEGER",
        "clo_code": "TEXT",
        "description": "TEXT",
        "plo_code": "TEXT",
        "pi_code": "TEXT",
        "mapping_level": "TEXT",
        "bloom_level": "TEXT",
        "assessment_methods": "JSON",
        "passing_threshold": "REAL",
        "status": "TEXT",
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
    },
    "syllabus_material": {
        "id": "INTEGER PRIMARY KEY",
        "syllabus_id": "INTEGER",
        "material_library_id": "INTEGER",
        "material_type": "TEXT",
        "title": "TEXT",
        "authors": "TEXT",
        "year": "INTEGER",
        "publisher": "TEXT",
        "library_code": "TEXT",
        "url": "TEXT",
        "doi": "TEXT",
        "isbn": "TEXT",
        "edition": "TEXT",
        "required": "BOOLEAN",
        "source_type": "TEXT",
        "description": "TEXT",
    },
    "syllabus_facility": {
        "syllabus_id": "INTEGER PRIMARY KEY",
        "classroom_requirements": "TEXT",
        "teaching_equipment": "TEXT",
        "lab_equipment": "TEXT",
        "extracurricular_activities": "TEXT",
    },
    "syllabus_research_resource": {
        "syllabus_id": "INTEGER PRIMARY KEY",
        "databases": "JSON",
        "labs": "JSON",
        "software": "JSON",
        "research_projects": "JSON",
    },
    "syllabus_schedule": {
        "id": "INTEGER PRIMARY KEY",
        "syllabus_id": "INTEGER",
        "schedule_type": "TEXT",
        "week": "TEXT",
        "semester": "TEXT",
        "topic": "TEXT",
        "milestone": "TEXT",
        "theory_hours": "INTEGER",
        "practice_hours": "INTEGER",
        "seminar_hours": "INTEGER",
        "research_hours": "INTEGER",
        "self_study_hours": "INTEGER",
        "teaching_activities": "JSON",
        "learning_activities": "JSON",
        "clos": "JSON",
        "assessments": "JSON",
        "ordering": "INTEGER",
    },
    "student_responsibility": {
        "id": "INTEGER PRIMARY KEY",
        "syllabus_id": "INTEGER",
        "description": "TEXT",
    },
    "academic_regulation": {
        "id": "INTEGER PRIMARY KEY",
        "syllabus_id": "INTEGER",
        "description": "TEXT",
    },
    "assessment_component": {
        "id": "INTEGER PRIMARY KEY",
        "syllabus_id": "INTEGER",
        "component_name": "TEXT",
        "component_weight": "REAL",
    },
    "assessment": {
        "id": "INTEGER PRIMARY KEY",
        "component_id": "INTEGER",
        "assessment_code": "TEXT",
        "assessment_name": "TEXT",
        "assessment_method": "TEXT",
        "assessment_type": "TEXT",
        "week": "INTEGER",
        "rubric_id": "INTEGER",
        "evaluation_criteria": "TEXT",
        "description": "TEXT",
    },
    "assessment_clo": {
        "id": "INTEGER PRIMARY KEY",
        "assessment_id": "INTEGER",
        "clo_id": "INTEGER",
        "clo_code": "TEXT",
        "max_score": "REAL",
        "clo_weight": "REAL",
    },
    "rubric": {
        "id": "INTEGER PRIMARY KEY",
        "syllabus_id": "INTEGER",
        "rubric_code": "TEXT",
        "rubric_name": "TEXT",
        "description": "TEXT",
        "status": "TEXT",
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
    },
    "rubric_criterion": {
        "id": "INTEGER PRIMARY KEY",
        "rubric_id": "INTEGER",
        "criterion_name": "TEXT",
        "weight": "REAL",
        "performance_levels": "JSON",
    },
    "curriculum_matrix": {
        "id": "INTEGER PRIMARY KEY",
        "program_id": "INTEGER",
        "course_id": "INTEGER",
        "plo_id": "INTEGER",
        "mapping_level": "TEXT",
        "weight": "REAL",
        "semester": "INTEGER",
    },
    "clo_plo_mapping": {
        "id": "INTEGER PRIMARY KEY",
        "course_id": "INTEGER",
        "clo_id": "INTEGER",
        "plo_id": "INTEGER",
        "pi_id": "INTEGER",
        "mapping_level": "TEXT",
        "weight": "REAL",
        "assessment_component": "TEXT",
        "evidence_source": "TEXT",
    },
    "survey": {
        "id": "INTEGER PRIMARY KEY",
        "program_id": "INTEGER",
        "survey_type": "TEXT",
        "semester": "TEXT",
        "questions": "JSON",
        "results": "JSON",
        "analysis": "TEXT",
        "created_at": "DATETIME",
    },
    "cqi_action": {
        "id": "INTEGER PRIMARY KEY",
        "program_id": "INTEGER",
        "semester": "TEXT",
        "issue_detected": "TEXT",
        "evidence": "TEXT",
        "improvement_action": "TEXT",
        "responsible_person": "TEXT",
        "deadline": "DATE",
        "status": "TEXT",
        "created_at": "DATETIME",
    },
    "attainment_result": {
        "id": "INTEGER PRIMARY KEY",
        "program_id": "INTEGER",
        "course_id": "INTEGER",
        "plo_id": "INTEGER",
        "pi_id": "INTEGER",
        "semester": "TEXT",
        "attainment_score": "REAL",
        "target_score": "REAL",
        "achievement_rate": "REAL",
        "status": "TEXT",
        "created_at": "DATETIME",
    },
    "syllabus_revision": {
        "id": "INTEGER PRIMARY KEY",
        "syllabus_id": "INTEGER",
        "version": "TEXT",
        "description": "TEXT",
        "change_type": "TEXT",
        "update_date": "DATE",
        "updated_by": "TEXT",
    },
    "syllabus_approval": {
        "syllabus_id": "INTEGER PRIMARY KEY",
        "dean_name": "TEXT",
        "dean_title": "TEXT",
        "dean_signed_date": "DATE",
        "author_name": "TEXT",
        "author_title": "TEXT",
        "author_signed_date": "DATE",
        "approved_date": "DATE",
    },
}


CONTENT_TYPES = ("theory", "literature_review", "doctoral_topic", "doctoral_research")
STATUS_VALUES = ("draft", "review", "approved", "archived")
MAPPING_LEVELS = ("I", "R", "M")


FOREIGN_KEYS: dict[tuple[str, str], tuple[str, str, str]] = {
    ("instructor", "department_id"): ("department", "id", "SET NULL"),
    ("program", "department_id"): ("department", "id", "SET NULL"),
    ("major", "program_id"): ("program", "id", "CASCADE"),
    ("peo", "program_id"): ("program", "id", "CASCADE"),
    ("plo", "program_id"): ("program", "id", "CASCADE"),
    ("pi", "plo_id"): ("plo", "id", "CASCADE"),
    ("pi", "rubric_id"): ("rubric", "id", "SET NULL"),
    ("course", "program_id"): ("program", "id", "SET NULL"),
    ("course", "major_id"): ("major", "id", "SET NULL"),
    ("syllabus", "course_id"): ("course", "id", "CASCADE"),
    ("syllabus", "program_id"): ("program", "id", "SET NULL"),
    ("syllabus", "major_id"): ("major", "id", "SET NULL"),
    ("syllabus", "created_by"): ("instructor", "id", "SET NULL"),
    ("syllabus", "approved_by"): ("instructor", "id", "SET NULL"),
    ("syllabus_course_info", "syllabus_id"): ("syllabus", "id", "CASCADE"),
    ("syllabus_main_lecturer", "syllabus_id"): ("syllabus", "id", "CASCADE"),
    ("syllabus_main_lecturer", "instructor_id"): ("instructor", "id", "SET NULL"),
    ("syllabus_sub_lecturer", "syllabus_id"): ("syllabus", "id", "CASCADE"),
    ("syllabus_sub_lecturer", "instructor_id"): ("instructor", "id", "SET NULL"),
    ("syllabus_prerequisite", "syllabus_id"): ("syllabus", "id", "CASCADE"),
    ("syllabus_parallel_course", "syllabus_id"): ("syllabus", "id", "CASCADE"),
    ("syllabus_replacement_course", "syllabus_id"): ("syllabus", "id", "CASCADE"),
    ("syllabus_objective", "syllabus_id"): ("syllabus", "id", "CASCADE"),
    ("clo", "syllabus_id"): ("syllabus", "id", "CASCADE"),
    ("clo", "course_id"): ("course", "id", "CASCADE"),
    ("syllabus_material", "syllabus_id"): ("syllabus", "id", "CASCADE"),
    ("syllabus_material", "material_library_id"): ("material_library", "id", "SET NULL"),
    ("syllabus_facility", "syllabus_id"): ("syllabus", "id", "CASCADE"),
    ("syllabus_research_resource", "syllabus_id"): ("syllabus", "id", "CASCADE"),
    ("syllabus_schedule", "syllabus_id"): ("syllabus", "id", "CASCADE"),
    ("student_responsibility", "syllabus_id"): ("syllabus", "id", "CASCADE"),
    ("academic_regulation", "syllabus_id"): ("syllabus", "id", "CASCADE"),
    ("assessment_component", "syllabus_id"): ("syllabus", "id", "CASCADE"),
    ("assessment", "component_id"): ("assessment_component", "id", "CASCADE"),
    ("assessment", "rubric_id"): ("rubric", "id", "SET NULL"),
    ("assessment_clo", "assessment_id"): ("assessment", "id", "CASCADE"),
    ("assessment_clo", "clo_id"): ("clo", "id", "CASCADE"),
    ("rubric", "syllabus_id"): ("syllabus", "id", "CASCADE"),
    ("rubric_criterion", "rubric_id"): ("rubric", "id", "CASCADE"),
    ("curriculum_matrix", "program_id"): ("program", "id", "CASCADE"),
    ("curriculum_matrix", "course_id"): ("course", "id", "CASCADE"),
    ("curriculum_matrix", "plo_id"): ("plo", "id", "CASCADE"),
    ("clo_plo_mapping", "course_id"): ("course", "id", "CASCADE"),
    ("clo_plo_mapping", "clo_id"): ("clo", "id", "CASCADE"),
    ("clo_plo_mapping", "plo_id"): ("plo", "id", "CASCADE"),
    ("clo_plo_mapping", "pi_id"): ("pi", "id", "SET NULL"),
    ("survey", "program_id"): ("program", "id", "CASCADE"),
    ("cqi_action", "program_id"): ("program", "id", "CASCADE"),
    ("attainment_result", "program_id"): ("program", "id", "CASCADE"),
    ("attainment_result", "course_id"): ("course", "id", "CASCADE"),
    ("attainment_result", "plo_id"): ("plo", "id", "CASCADE"),
    ("attainment_result", "pi_id"): ("pi", "id", "SET NULL"),
    ("syllabus_revision", "syllabus_id"): ("syllabus", "id", "CASCADE"),
    ("syllabus_approval", "syllabus_id"): ("syllabus", "id", "CASCADE"),
}


@dataclass(frozen=True)
class SchemaColumn:
    table: str
    name: str
    declared_type: str
    sqlite_type: str
    required: bool = False
    unique: bool = False
    json: bool = False
    primary_key: bool = False


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def column_sql_type(declared_type: str) -> str:
    normalized = declared_type.strip().upper()
    if "PRIMARY KEY" in normalized:
        return declared_type
    if normalized == "JSON":
        return "TEXT"
    if normalized == "BOOLEAN":
        return "INTEGER"
    if normalized == "DATETIME":
        return "TEXT"
    if normalized == "DATE":
        return "TEXT"
    return declared_type


def column_meta(table: str, name: str, declared_type: str) -> SchemaColumn:
    normalized = declared_type.upper()
    return SchemaColumn(
        table=table,
        name=name,
        declared_type=declared_type,
        sqlite_type=column_sql_type(declared_type),
        required="NOT NULL" in normalized or name.endswith("_code"),
        unique="UNIQUE" in normalized,
        json=normalized == "JSON",
        primary_key="PRIMARY KEY" in normalized,
    )


def iter_columns() -> Iterable[SchemaColumn]:
    for table, columns in ACADEMIC_SYSTEM_SCHEMA.items():
        for name, declared_type in columns.items():
            yield column_meta(table, name, declared_type)


def _quote(identifier: str) -> str:
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", identifier):
        raise ValueError(f"Unsafe SQL identifier: {identifier}")
    return f'"{identifier}"'


def create_table_sql(table: str) -> str:
    columns = ACADEMIC_SYSTEM_SCHEMA[table]
    parts: list[str] = []
    for name, declared_type in columns.items():
        col = column_meta(table, name, declared_type)
        part = f"{_quote(name)} {col.sqlite_type}"
        fk = FOREIGN_KEYS.get((table, name))
        if fk and "PRIMARY KEY" not in col.sqlite_type.upper():
            target_table, target_col, on_delete = fk
            part += f" REFERENCES {_quote(target_table)}({_quote(target_col)}) ON DELETE {on_delete}"
        parts.append(part)

    return f"CREATE TABLE IF NOT EXISTS {_quote(table)} (\n    " + ",\n    ".join(parts) + "\n)"


def table_exists(conn: Any, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND lower(name)=lower(?)",
        (table,),
    ).fetchone()
    return row is not None


def resolve_table_name(conn: Any, table: str) -> str:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND lower(name)=lower(?)",
        (table,),
    ).fetchone()
    return row[0] if row else table


def existing_columns(conn: Any, table: str) -> set[str]:
    actual = resolve_table_name(conn, table)
    return {row[1] for row in conn.execute(f"PRAGMA table_info({_quote(actual)})").fetchall()}


def add_missing_columns_sql(conn: Any, table: str) -> list[str]:
    present = existing_columns(conn, table)
    actual = resolve_table_name(conn, table)
    statements = []
    for name, declared_type in ACADEMIC_SYSTEM_SCHEMA[table].items():
        if name in present:
            continue
        col = column_meta(table, name, declared_type)
        col_type = col.sqlite_type
        col_type = re.sub(r"\s+PRIMARY\s+KEY\b", "", col_type, flags=re.IGNORECASE)
        col_type = re.sub(r"\s+UNIQUE\b", "", col_type, flags=re.IGNORECASE)
        statements.append(f"ALTER TABLE {_quote(actual)} ADD COLUMN {_quote(name)} {col_type}")
    return statements


def index_sql() -> list[str]:
    statements: list[str] = []
    for table, columns in ACADEMIC_SYSTEM_SCHEMA.items():
        for col in columns:
            if (table, col) in FOREIGN_KEYS:
                statements.append(
                    f"CREATE INDEX IF NOT EXISTS idx_{table}_{col} ON {_quote(table)}({_quote(col)})"
                )
            if col.endswith("_code"):
                statements.append(
                    f"CREATE INDEX IF NOT EXISTS idx_{table}_{col}_lookup ON {_quote(table)}({_quote(col)})"
                )
    statements.extend(
        [
            'CREATE INDEX IF NOT EXISTS idx_course_program_semester ON "course"("program_id", "semester")',
            'CREATE INDEX IF NOT EXISTS idx_syllabus_course_status ON "syllabus"("course_id", "status")',
            'CREATE INDEX IF NOT EXISTS idx_clo_course_code ON "clo"("course_id", "clo_code")',
            'CREATE INDEX IF NOT EXISTS idx_curriculum_matrix_program ON "curriculum_matrix"("program_id", "semester")',
        ]
    )
    return statements


def metadata_tables_sql() -> list[str]:
    return [
        """
        CREATE TABLE IF NOT EXISTS academic_entity_meta (
            entity_name TEXT PRIMARY KEY,
            display_name TEXT,
            domain_group TEXT,
            form_order INTEGER,
            supports_versioning INTEGER DEFAULT 0,
            supports_approval INTEGER DEFAULT 0,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS academic_field_meta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_name TEXT NOT NULL,
            field_name TEXT NOT NULL,
            declared_type TEXT,
            sqlite_type TEXT,
            widget_type TEXT,
            required INTEGER DEFAULT 0,
            readonly INTEGER DEFAULT 0,
            json_path_enabled INTEGER DEFAULT 0,
            field_order INTEGER,
            updated_at TEXT,
            UNIQUE(entity_name, field_name)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS academic_schema_upgrade_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration_version TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS legacy_academic_bridge (
            legacy_table TEXT NOT NULL,
            legacy_id INTEGER NOT NULL,
            enterprise_table TEXT NOT NULL,
            enterprise_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(legacy_table, legacy_id, enterprise_table)
        )
        """,
    ]


def infer_widget_type(col: SchemaColumn) -> str:
    if col.primary_key:
        return "readonly"
    if col.json:
        return "json_editor"
    if col.name in {"status", "content_type", "mapping_level", "education_level"}:
        return "combo"
    if col.sqlite_type.upper().startswith("INTEGER") or col.sqlite_type.upper().startswith("REAL"):
        return "number"
    if col.name.endswith("_date") or col.declared_type.upper() in {"DATE", "DATETIME"}:
        return "date"
    if col.name in {"description", "summary", "analysis", "evidence", "questions", "results"}:
        return "textarea"
    return "entry"


def seed_metadata(conn: Any) -> None:
    now = now_text()
    for order, table in enumerate(ACADEMIC_SYSTEM_SCHEMA, start=1):
        conn.execute(
            """
            INSERT INTO academic_entity_meta(entity_name, display_name, domain_group, form_order, supports_versioning, supports_approval, updated_at)
            VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(entity_name) DO UPDATE SET
                display_name=excluded.display_name,
                domain_group=excluded.domain_group,
                form_order=excluded.form_order,
                supports_versioning=excluded.supports_versioning,
                supports_approval=excluded.supports_approval,
                updated_at=excluded.updated_at
            """,
            (
                table,
                table.replace("_", " ").title(),
                _domain_group(table),
                order,
                1 if "revision" in table else 0,
                1 if "approval" in table or table == "syllabus" else 0,
                now,
            ),
        )
        for field_order, col in enumerate(
            (column_meta(table, name, typ) for name, typ in ACADEMIC_SYSTEM_SCHEMA[table].items()),
            start=1,
        ):
            conn.execute(
                """
                INSERT INTO academic_field_meta(entity_name, field_name, declared_type, sqlite_type, widget_type,
                                                required, readonly, json_path_enabled, field_order, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(entity_name, field_name) DO UPDATE SET
                    declared_type=excluded.declared_type,
                    sqlite_type=excluded.sqlite_type,
                    widget_type=excluded.widget_type,
                    required=excluded.required,
                    readonly=excluded.readonly,
                    json_path_enabled=excluded.json_path_enabled,
                    field_order=excluded.field_order,
                    updated_at=excluded.updated_at
                """,
                (
                    col.table,
                    col.name,
                    col.declared_type,
                    col.sqlite_type,
                    infer_widget_type(col),
                    1 if col.required else 0,
                    1 if col.primary_key else 0,
                    1 if col.json else 0,
                    field_order,
                    now,
                ),
            )


def _domain_group(table: str) -> str:
    if table in {"department", "instructor", "material_library"}:
        return "master_data"
    if table in {"program", "major", "course"}:
        return "program_structure"
    if table in {"peo", "plo", "pi", "curriculum_matrix", "clo_plo_mapping"}:
        return "obe_mapping"
    if table.startswith("syllabus") or table in {"clo", "student_responsibility", "academic_regulation"}:
        return "syllabus"
    if table.startswith("assessment") or table.startswith("rubric"):
        return "assessment"
    if table in {"survey", "cqi_action", "attainment_result"}:
        return "quality_assurance"
    return "system"


def apply_enterprise_schema_upgrade(db: Any) -> dict[str, int]:
    """Apply enterprise schema without rebuilding existing legacy tables."""
    conn = db.conn
    created = 0
    altered = 0
    indexed = 0

    conn.execute("PRAGMA foreign_keys = ON")
    for sql in metadata_tables_sql():
        conn.execute(sql)

    for table in ACADEMIC_SYSTEM_SCHEMA:
        if not table_exists(conn, table):
            conn.execute(create_table_sql(table))
            created += 1
        else:
            for sql in add_missing_columns_sql(conn, table):
                conn.execute(sql)
                altered += 1

    for sql in index_sql():
        try:
            conn.execute(sql)
            indexed += 1
        except Exception:
            # Existing legacy tables can have duplicate/partial state. Keep the
            # schema upgrade non-destructive and expose gaps through validation.
            pass

    seed_metadata(conn)
    conn.execute(
        """
        INSERT INTO academic_schema_upgrade_log(migration_version, action, details, created_at)
        VALUES(?,?,?,?)
        """,
        (
            "v19",
            "enterprise_schema_upgrade",
            f"created={created}; altered={altered}; indexed={indexed}",
            now_text(),
        ),
    )
    return {"created": created, "altered": altered, "indexed": indexed}
