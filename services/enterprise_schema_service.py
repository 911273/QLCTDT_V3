"""Services for enterprise academic schema readiness and legacy migration."""

from __future__ import annotations

from typing import Any

from core.enterprise_schema import (
    ACADEMIC_SYSTEM_SCHEMA,
    CONTENT_TYPES,
    MAPPING_LEVELS,
    STATUS_VALUES,
    apply_enterprise_schema_upgrade,
    now_text,
)
from repositories.enterprise_repository import EnterpriseRepository


class EnterpriseSchemaService:
    """Coordinate enterprise schema validation and legacy data bridging."""

    def __init__(self, db: Any):
        self.db = db
        self.repo = EnterpriseRepository(db)

    def ensure_ready(self) -> dict[str, Any]:
        """Run the non-destructive schema upgrade and return coverage status."""
        result = apply_enterprise_schema_upgrade(self.db)
        coverage = self.validate_schema_coverage()
        return {"upgrade": result, "coverage": coverage}

    def validate_schema_coverage(self) -> dict[str, Any]:
        missing_tables: list[str] = []
        missing_columns: dict[str, list[str]] = {}
        for table, fields in ACADEMIC_SYSTEM_SCHEMA.items():
            if not self._table_exists(table):
                missing_tables.append(table)
                continue
            cols = self._columns(table)
            missing = [field for field in fields if field not in cols]
            if missing:
                missing_columns[table] = missing
        return {
            "table_count": len(ACADEMIC_SYSTEM_SCHEMA),
            "missing_tables": missing_tables,
            "missing_columns": missing_columns,
            "complete": not missing_tables and not missing_columns,
        }

    def get_dynamic_form_schema(self, entity_name: str, content_type: str | None = None) -> dict[str, Any]:
        """Return UI-ready field metadata for schema-driven form rendering."""
        fields = self.repo.form_schema(entity_name)
        if entity_name == "syllabus":
            for field in fields:
                if field["field_name"] == "content_type":
                    field["choices"] = list(CONTENT_TYPES)
                elif field["field_name"] == "status":
                    field["choices"] = list(STATUS_VALUES)
        elif any(field["field_name"] == "mapping_level" for field in fields):
            for field in fields:
                if field["field_name"] == "mapping_level":
                    field["choices"] = list(MAPPING_LEVELS)
        return {
            "entity": entity_name,
            "content_type": content_type,
            "fields": fields,
        }

    def bridge_legacy_data(self) -> dict[str, int]:
        """Copy current V23 legacy data into enterprise tables without deleting legacy data."""
        counts = {
            "departments": self._bridge_departments(),
            "programs": self._bridge_programs(),
            "majors": self._bridge_majors(),
            "instructors": self._bridge_instructors(),
            "courses": self._bridge_courses(),
            "syllabi": self._bridge_syllabi(),
            "clo_rows": self._bridge_clos(),
            "objectives": self._bridge_objectives(),
            "materials": self._bridge_materials(),
        }
        self.db.conn.execute(
            """
            INSERT INTO academic_schema_upgrade_log(migration_version, action, details, created_at)
            VALUES(?,?,?,?)
            """,
            (
                "bridge",
                "legacy_to_enterprise",
                "; ".join(f"{key}={value}" for key, value in counts.items()),
                now_text(),
            ),
        )
        self.db.conn.commit()
        return counts

    def _bridge_departments(self) -> int:
        if not self._table_exists("khoa"):
            return 0
        count = 0
        for row in self.db.conn.execute("SELECT * FROM khoa").fetchall():
            code = row["ma"] or f"KHOA-{row['id']}"
            entity_id = self.repo.upsert_by_unique(
                "department",
                "department_code",
                code,
                {
                    "department_name_vi": row["ten"],
                    "status": "active",
                },
            )
            self.repo.link_legacy("khoa", row["id"], "department", entity_id)
            count += 1
        return count

    def _bridge_programs(self) -> int:
        if not self._table_exists("chuong_trinh_dao_tao"):
            return 0
        count = 0
        for row in self.db.conn.execute("SELECT * FROM chuong_trinh_dao_tao").fetchall():
            department_id = self._legacy_id("khoa", row["khoa_id"], "department") if row["khoa_id"] else None
            code = f"CTDT-{row['id']}"
            entity_id = self.repo.upsert_by_unique(
                "program",
                "program_code",
                code,
                {
                    "department_id": department_id,
                    "program_name_vi": row["ten"],
                    "education_level": self._normalize_level(row["bac"]),
                    "degree_name": row["bac"],
                    "status": "active",
                },
            )
            self.repo.link_legacy("chuong_trinh_dao_tao", row["id"], "program", entity_id)
            count += 1
        return count

    def _bridge_majors(self) -> int:
        if not self._table_exists("chuyen_nganh"):
            return 0
        count = 0
        for row in self.db.conn.execute("SELECT * FROM chuyen_nganh").fetchall():
            program_id = self._legacy_id("chuong_trinh_dao_tao", row["ctdt_id"], "program")
            code = f"CN-{row['id']}"
            entity_id = self.repo.upsert_by_unique(
                "major",
                "major_code",
                code,
                {
                    "program_id": program_id,
                    "major_name_vi": row["ten"],
                    "status": "active",
                },
            )
            self.repo.link_legacy("chuyen_nganh", row["id"], "major", entity_id)
            count += 1
        return count

    def _bridge_instructors(self) -> int:
        if not self._table_exists("giang_vien"):
            return 0
        count = 0
        for row in self.db.conn.execute("SELECT * FROM giang_vien").fetchall():
            department_id = self._legacy_id("khoa", row["khoa_id"], "department") if "khoa_id" in row.keys() and row["khoa_id"] else None
            staff_code = row["ma_can_bo"] if "ma_can_bo" in row.keys() and row["ma_can_bo"] else f"GV-{row['id']}"
            entity_id = self.repo.upsert_by_unique(
                "instructor",
                "staff_code",
                staff_code,
                {
                    "department_id": department_id,
                    "full_name": row["ho_ten"],
                    "degree": row["hoc_vi"] if "hoc_vi" in row.keys() else None,
                    "email": row["email"] if "email" in row.keys() else None,
                    "phone": row["sdt"] if "sdt" in row.keys() else None,
                    "date_of_birth": row["ngay_sinh"] if "ngay_sinh" in row.keys() else None,
                    "training_country": row["co_so_dao_tao"] if "co_so_dao_tao" in row.keys() else None,
                    "graduation_year": row["nam_tot_nghiep"] if "nam_tot_nghiep" in row.keys() else None,
                    "specialization": row["nganh_dao_tao"] if "nganh_dao_tao" in row.keys() else None,
                    "status": "active",
                },
            )
            self.repo.link_legacy("giang_vien", row["id"], "instructor", entity_id)
            count += 1
        return count

    def _bridge_courses(self) -> int:
        if not self._table_exists("hoc_phan"):
            return 0
        count = 0
        for row in self.db.conn.execute("SELECT * FROM hoc_phan").fetchall():
            program_id, major_id = self._course_program_major(row["id"])
            course_code = row["ma"] or f"HP-{row['id']}"
            entity_id = self.repo.upsert_by_unique(
                "course",
                "course_code",
                course_code,
                {
                    "program_id": program_id,
                    "major_id": major_id,
                    "course_name_vi": row["ten_viet"],
                    "course_name_en": row["ten_anh"] if "ten_anh" in row.keys() else None,
                    "knowledge_block": row["khoi_kien_thuc"] if "khoi_kien_thuc" in row.keys() else None,
                    "course_type": row["loai"] if "loai" in row.keys() else None,
                    "course_nature": row["tinh_chat"] if "tinh_chat" in row.keys() else None,
                    "mandatory": 1 if (row["loai"] if "loai" in row.keys() else "") != "Tu chon" else 0,
                    "credits": row["so_tin_chi"] if "so_tin_chi" in row.keys() else None,
                    "class_hours": row["tong_gio"] if "tong_gio" in row.keys() else None,
                    "theory_hours": row["gio_lt"] if "gio_lt" in row.keys() else None,
                    "practice_hours": row["gio_th"] if "gio_th" in row.keys() else None,
                    "discussion_hours": row["gio_tl"] if "gio_tl" in row.keys() else None,
                    "project_hours": row["gio_tieu_luan"] if "gio_tieu_luan" in row.keys() else None,
                    "internship_hours": row["gio_thuc_tap"] if "gio_thuc_tap" in row.keys() else None,
                    "self_study_hours": row["gio_tu_hoc"] if "gio_tu_hoc" in row.keys() else None,
                    "total_hours": row["tong_gio"] if "tong_gio" in row.keys() else None,
                    "prerequisite_courses": row["hp_tien_quyet"] if "hp_tien_quyet" in row.keys() else None,
                    "replacement_course": row["hp_thay_the"] if "hp_thay_the" in row.keys() else None,
                    "summary": row["mo_ta"] if "mo_ta" in row.keys() else None,
                    "status": row["trang_thai"] if "trang_thai" in row.keys() else "draft",
                },
            )
            self.repo.link_legacy("hoc_phan", row["id"], "course", entity_id)
            count += 1
        return count

    def _bridge_syllabi(self) -> int:
        if not self._table_exists("hoc_phan"):
            return 0
        count = 0
        for row in self.db.conn.execute("SELECT * FROM hoc_phan").fetchall():
            existing = self.repo.enterprise_id_for_legacy("hoc_phan", row["id"], "syllabus")
            course_id = self._legacy_id("hoc_phan", row["id"], "course")
            if not course_id:
                continue
            program_id, major_id = self._course_program_major(row["id"])
            payload = {
                "course_id": course_id,
                "program_id": program_id,
                "major_id": major_id,
                "version": "1.0",
                "title": row["ten_viet"],
                "summary": row["mo_ta"] if "mo_ta" in row.keys() else None,
                "content_type": self._infer_content_type(row),
                "status": self._normalize_status(row["trang_thai"] if "trang_thai" in row.keys() else None),
            }
            if existing:
                self.repo.update("syllabus", existing, payload)
                syllabus_id = existing
            else:
                syllabus_id = self.repo.insert("syllabus", payload)
            self.repo.link_legacy("hoc_phan", row["id"], "syllabus", syllabus_id)
            self._upsert_course_info(row, syllabus_id)
            count += 1
        return count

    def _bridge_clos(self) -> int:
        if not self._table_exists("clo"):
            return 0
        cols = self._columns("clo")
        if "hp_id" not in cols:
            return 0
        count = 0
        for row in self.db.conn.execute("SELECT * FROM clo WHERE hp_id IS NOT NULL").fetchall():
            course_id = self._legacy_id("hoc_phan", row["hp_id"], "course")
            syllabus_id = self._legacy_id("hoc_phan", row["hp_id"], "syllabus")
            if not course_id and not syllabus_id:
                continue
            payload = {
                "syllabus_id": self._row_value(row, "syllabus_id") or syllabus_id,
                "course_id": self._row_value(row, "course_id") or course_id,
                "clo_code": self._row_value(row, "clo_code") or self._row_value(row, "ma"),
                "description": self._row_value(row, "description") or self._row_value(row, "mo_ta"),
                "plo_code": self._row_value(row, "plo_code") or self._row_value(row, "cdr_ma"),
                "mapping_level": self._row_value(row, "mapping_level") or self._row_value(row, "level_irm"),
                "bloom_level": self._row_value(row, "bloom_level") or self._row_value(row, "cap_do_bloom"),
                "status": self._row_value(row, "status") or "active",
            }
            self.repo.update("clo", row["id"], payload)
            self.repo.link_legacy("clo", row["id"], "clo", row["id"])
            count += 1
        return count

    def _bridge_objectives(self) -> int:
        if not self._table_exists("muc_tieu"):
            return 0
        count = 0
        for row in self.db.conn.execute("SELECT * FROM muc_tieu WHERE hp_id IS NOT NULL").fetchall():
            syllabus_id = self._legacy_id("hoc_phan", row["hp_id"], "syllabus")
            if not syllabus_id:
                continue
            existing = self.repo.enterprise_id_for_legacy("muc_tieu", row["id"], "syllabus_objective")
            payload = {
                "syllabus_id": syllabus_id,
                "objective_no": str(row["so_thu_tu"] if "so_thu_tu" in row.keys() and row["so_thu_tu"] is not None else row["id"]),
                "description": row["mo_ta"] if "mo_ta" in row.keys() else None,
                "plo_code": row["cdr_ma"] if "cdr_ma" in row.keys() else None,
            }
            if existing:
                self.repo.update("syllabus_objective", existing, payload)
                objective_id = existing
            else:
                objective_id = self.repo.insert("syllabus_objective", payload)
            self.repo.link_legacy("muc_tieu", row["id"], "syllabus_objective", objective_id)
            count += 1
        return count

    def _bridge_materials(self) -> int:
        if not self._table_exists("hoc_lieu"):
            return 0
        count = 0
        for row in self.db.conn.execute("SELECT * FROM hoc_lieu WHERE hp_id IS NOT NULL").fetchall():
            syllabus_id = self._legacy_id("hoc_phan", row["hp_id"], "syllabus")
            if not syllabus_id:
                continue
            existing = self.repo.enterprise_id_for_legacy("hoc_lieu", row["id"], "syllabus_material")
            payload = {
                "syllabus_id": syllabus_id,
                "material_library_id": row["tai_lieu_id"] if "tai_lieu_id" in row.keys() else None,
                "material_type": row["loai"] if "loai" in row.keys() else None,
                "title": row["ten"] if "ten" in row.keys() else row["noi_dung"],
                "authors": row["tac_gia"] if "tac_gia" in row.keys() else None,
                "description": row["thong_tin"] if "thong_tin" in row.keys() else None,
            }
            if existing:
                self.repo.update("syllabus_material", existing, payload)
                material_id = existing
            else:
                material_id = self.repo.insert("syllabus_material", payload)
            self.repo.link_legacy("hoc_lieu", row["id"], "syllabus_material", material_id)
            count += 1
        return count

    def _upsert_course_info(self, row: Any, syllabus_id: int) -> None:
        self.db.conn.execute(
            """
            INSERT INTO syllabus_course_info(
                syllabus_id, education_level, course_type, course_nature,
                class_hours, theory_hours, practice_hours, discussion_hours,
                project_hours, internship_hours, self_study_hours, total_hours
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(syllabus_id) DO UPDATE SET
                education_level=excluded.education_level,
                course_type=excluded.course_type,
                course_nature=excluded.course_nature,
                class_hours=excluded.class_hours,
                theory_hours=excluded.theory_hours,
                practice_hours=excluded.practice_hours,
                discussion_hours=excluded.discussion_hours,
                project_hours=excluded.project_hours,
                internship_hours=excluded.internship_hours,
                self_study_hours=excluded.self_study_hours,
                total_hours=excluded.total_hours
            """,
            (
                syllabus_id,
                row["trinh_do"] if "trinh_do" in row.keys() else None,
                row["loai"] if "loai" in row.keys() else None,
                row["tinh_chat"] if "tinh_chat" in row.keys() else None,
                row["tong_gio"] if "tong_gio" in row.keys() else None,
                row["gio_lt"] if "gio_lt" in row.keys() else None,
                row["gio_th"] if "gio_th" in row.keys() else None,
                row["gio_tl"] if "gio_tl" in row.keys() else None,
                row["gio_tieu_luan"] if "gio_tieu_luan" in row.keys() else None,
                row["gio_thuc_tap"] if "gio_thuc_tap" in row.keys() else None,
                row["gio_tu_hoc"] if "gio_tu_hoc" in row.keys() else None,
                row["tong_gio"] if "tong_gio" in row.keys() else None,
            ),
        )

    def _course_program_major(self, hp_id: int) -> tuple[int | None, int | None]:
        if not self._table_exists("ctdt_hoc_phan"):
            return None, None
        row = self.db.conn.execute(
            "SELECT * FROM ctdt_hoc_phan WHERE hp_id=? ORDER BY thu_tu, id LIMIT 1",
            (hp_id,),
        ).fetchone()
        if not row:
            return None, None
        program_id = self._legacy_id("chuong_trinh_dao_tao", row["ctdt_id"], "program")
        major_id = None
        if "chuyen_nganh" in row.keys() and row["chuyen_nganh"] and self._table_exists("chuyen_nganh"):
            major = self.db.conn.execute(
                "SELECT id FROM chuyen_nganh WHERE ten=? AND ctdt_id=? LIMIT 1",
                (row["chuyen_nganh"], row["ctdt_id"]),
            ).fetchone()
            if major:
                major_id = self._legacy_id("chuyen_nganh", major["id"], "major")
        return program_id, major_id

    def _legacy_id(self, legacy_table: str, legacy_id: int | None, enterprise_table: str) -> int | None:
        if legacy_id is None:
            return None
        return self.repo.enterprise_id_for_legacy(legacy_table, int(legacy_id), enterprise_table)

    @staticmethod
    def _normalize_level(value: str | None) -> str | None:
        text = (value or "").lower()
        if "thac" in text or "thạc" in text:
            return "master"
        if "tien" in text or "tiến" in text or "ts" in text:
            return "doctorate"
        if text:
            return "undergraduate"
        return None

    @staticmethod
    def _normalize_status(value: str | None) -> str:
        mapping = {
            "nhap": "draft",
            "cho_duyet": "review",
            "da_duyet": "approved",
            "can_sua": "draft",
        }
        return mapping.get(value or "", value or "draft")

    @staticmethod
    def _infer_content_type(row: Any) -> str:
        text = " ".join(str(row[key] or "") for key in row.keys()).lower()
        if "tieu luan" in text or "tiểu luận" in text:
            return "literature_review"
        if "chuyen de" in text or "chuyên đề" in text:
            return "doctoral_topic"
        if "luan an" in text or "luận án" in text or "nghien cuu" in text:
            return "doctoral_research"
        return "theory"

    def _table_exists(self, table: str) -> bool:
        row = self.db.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND lower(name)=lower(?)",
            (table,),
        ).fetchone()
        return row is not None

    def _columns(self, table: str) -> set[str]:
        return {row[1] for row in self.db.conn.execute(f"PRAGMA table_info({table})").fetchall()}

    @staticmethod
    def _row_value(row: Any, key: str, default: Any = None) -> Any:
        return row[key] if key in row.keys() else default
