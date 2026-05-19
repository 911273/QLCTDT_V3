"""Shared placeholder catalog for Word/Excel template features."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PLACEHOLDER_REGISTRY = {
    "Course": {
        "type": "group",
        "children": {
            "CourseName": {"type": "scalar", "desc": "Course name"},
            "CourseCode": {"type": "scalar", "desc": "Course code"},
            "Credits": {"type": "scalar", "desc": "Credits"},
            "Department": {"type": "scalar", "desc": "Department"},
            "Lecturer": {"type": "scalar", "desc": "Main lecturer"},
            "CourseType": {"type": "scalar", "desc": "Course type"},
            "Semester": {"type": "scalar", "desc": "Semester"},
            "ProgramName": {"type": "scalar", "desc": "Program name"},
            "MajorName": {"type": "scalar", "desc": "Major name"},
            "Summary": {"type": "scalar", "desc": "Course summary"},
            "Outcomes": {"type": "scalar", "desc": "Learning outcomes summary"},
            "TeachingMethod": {"type": "scalar", "desc": "Teaching method"},
            "AssessmentPlan": {"type": "scalar", "desc": "Assessment plan"},
            "Prerequisite": {"type": "scalar", "desc": "Prerequisite course"},
            "ReplacementCourse": {"type": "scalar", "desc": "Replacement course"},
            "SignPlace": {"type": "scalar", "desc": "Approval signing place"},
            "SignDate": {"type": "scalar", "desc": "Approval signing date"},
            "SignerLeftTitle": {"type": "scalar", "desc": "Left signer title"},
            "SignerLeftName": {"type": "scalar", "desc": "Left signer name"},
            "SignerRightTitle": {"type": "scalar", "desc": "Right signer title"},
            "SignerRightName": {"type": "scalar", "desc": "Right signer name"},
        },
    },
    "Loops": {
        "type": "group",
        "children": {
            "CLOs": {
                "type": "loop",
                "children": ["Code", "Description", "PLO", "Level", "BloomLevel", "Group"],
            },
            "Objectives": {
                "type": "loop",
                "children": ["No", "Description", "PLO"],
            },
            "TeachingContents": {
                "type": "loop",
                "children": [
                    "No",
                    "Title",
                    "HoursLT",
                    "HoursBT",
                    "HoursTL",
                    "HoursTH",
                    "TeachingMethod",
                    "LearningTask",
                    "CLO",
                    "Assessment",
                ],
            },
            "AssessmentRows": {
                "type": "loop",
                "children": [
                    "No",
                    "Group",
                    "Content",
                    "Method",
                    "Time",
                    "Scale",
                    "Weight",
                    "CLO",
                ],
            },
            "Rubrics": {
                "type": "loop",
                "children": ["Name", "Code", "Description"],
            },
            "RevisionHistory": {
                "type": "loop",
                "children": ["Version", "Description", "Date", "UpdatedBy"],
            },
            "MainMaterials": {
                "type": "loop",
                "children": ["No", "Title", "Author", "Info", "Content"],
            },
            "ReferenceMaterials": {
                "type": "loop",
                "children": ["No", "Title", "Author", "Info", "Content"],
            },
            "Policies": {
                "type": "loop",
                "children": ["Type", "Content"],
            },
            "Checklists": {
                "type": "loop",
                "children": ["Item", "Status"],
            },
            "Lecturers": {
                "type": "loop",
                "children": ["Name", "Degree", "Role", "Phone", "Email", "Unit"],
            },
        },
    },
}


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _join_rows(rows: list[dict], fields: list[str], sep: str = "; ") -> str:
    parts = []
    for row in rows or []:
        vals = [_safe_text(row.get(field)).strip() for field in fields]
        vals = [val for val in vals if val]
        if vals:
            parts.append(" - ".join(vals))
    return sep.join(parts)


def _material(row: dict) -> dict:
    return {
        "No": row.get("so_thu_tu") or row.get("stt") or "",
        "Title": row.get("ten") or "",
        "Author": row.get("tac_gia") or "",
        "Info": row.get("thong_tin") or "",
        "Content": row.get("noi_dung") or row.get("ten") or "",
    }


def normalize_template_context(context: dict) -> dict:
    """Return a copy of TemplateEngine context with stable Excel aliases."""
    result = deepcopy(context or {})

    lecturers = result.get("Lecturers") or []
    main_lecturer = result.get("MainLecturer") or (lecturers[0] if lecturers else {})
    programs = result.get("Programs") or []
    first_program = programs[0] if programs else {}

    result.setdefault("Lecturer", main_lecturer.get("Name") or "")
    result.setdefault("CourseType", result.get("CourseType") or result.get("loai_hp") or "")
    result.setdefault("Semester", result.get("Semester") or "")
    result.setdefault("ProgramName", first_program.get("ten") or "")
    result.setdefault("MajorName", result.get("Major") or result.get("Specialization") or "")
    result.setdefault("Summary", result.get("Description") or "")
    result.setdefault("TeachingMethod", result.get("TeachingMethods") or "")
    result.setdefault("Prerequisite", result.get("PrereqCourse") or "")
    result.setdefault("ReplacementCourse", result.get("SubstituteCourse") or "")

    clos = []
    for row in result.get("CLOs") or []:
        clos.append(
            {
                "Code": row.get("Code") or row.get("ma") or "",
                "Description": row.get("Description") or row.get("Desc") or row.get("mo_ta") or "",
                "Desc": row.get("Desc") or row.get("Description") or row.get("mo_ta") or "",
                "PLO": row.get("PLO") or row.get("cdr_ma") or "",
                "Level": row.get("Level") or row.get("level_irm") or "",
                "BloomLevel": row.get("BloomLevel") or row.get("cap_do_bloom") or "",
                "Group": row.get("Group") or row.get("nhom") or "",
            }
        )
    result["CLOs"] = clos
    result.setdefault("Outcomes", _join_rows(clos, ["Code", "Description"]))

    objectives = []
    for i, row in enumerate(result.get("Objectives") or [], start=1):
        objectives.append(
            {
                "No": row.get("No") or row.get("so_thu_tu") or i,
                "Description": row.get("Description") or row.get("Desc") or row.get("mo_ta") or "",
                "Desc": row.get("Desc") or row.get("Description") or row.get("mo_ta") or "",
                "PLO": row.get("PLO") or row.get("cdr_ma") or "",
            }
        )
    result["Objectives"] = objectives

    teaching_contents = []
    for i, row in enumerate((result.get("ContentLT") or []) + (result.get("ContentTH") or []), start=1):
        teaching_contents.append(
            {
                "No": row.get("thu_tu") or i,
                "Title": row.get("ten") or "",
                "HoursLT": row.get("gio_lt") or 0,
                "HoursBT": row.get("gio_bt") or 0,
                "HoursTL": row.get("gio_tl") or 0,
                "HoursTH": row.get("gio_th_tn") or row.get("gio_th") or 0,
                "TeachingMethod": row.get("pp_day") or "",
                "LearningTask": row.get("pp_hoc") or row.get("nhiem_vu_ncs") or "",
                "CLO": row.get("cdr_ma") or "",
                "Assessment": row.get("bai_danh_gia") or "",
            }
        )
    result["TeachingContents"] = teaching_contents

    assessment_rows = []
    for i, row in enumerate(result.get("AssessmentRows") or [], start=1):
        assessment_rows.append(
            {
                "No": row.get("thu_tu") or i,
                "Group": row.get("nhom") or "",
                "Content": row.get("noi_dung") or "",
                "Method": row.get("hinh_thuc") or "",
                "Time": row.get("thoi_gian") or "",
                "Scale": row.get("thang_diem") or "",
                "Weight": row.get("ty_trong") or row.get("ty_trong_nhom") or "",
                "CLO": row.get("clo_lien_quan") or "",
            }
        )
    result["AssessmentRows"] = assessment_rows
    result.setdefault("AssessmentPlan", _join_rows(assessment_rows, ["Group", "Content", "Weight"]))

    result["MainMaterials"] = [_material(row) for row in result.get("MainRefs") or []]
    refs = (result.get("SupRefs") or []) + (result.get("OtherRefs") or [])
    result["ReferenceMaterials"] = [_material(row) for row in refs]

    result["Policies"] = [
        {"Type": row.get("loai_chinh_sach") or row.get("Type") or "", "Content": row.get("noi_dung") or row.get("Content") or ""}
        for row in result.get("Policies") or []
    ]
    result["Checklists"] = [
        {"Item": row.get("hang_muc") or row.get("Item") or "", "Status": row.get("trang_thai") or row.get("Status") or ""}
        for row in result.get("Checklists") or []
    ]
    result["Rubrics"] = [
        {
            "Name": row.get("ten") or row.get("Name") or "",
            "Code": row.get("ky_hieu") or row.get("ma") or row.get("Code") or "",
            "Description": row.get("mo_ta") or row.get("Description") or "",
        }
        for row in result.get("Rubrics") or result.get("rubrics") or []
    ]
    result["RevisionHistory"] = [
        {
            "Version": row.get("version") or row.get("lan") or row.get("Version") or "",
            "Description": row.get("noi_dung") or row.get("description") or row.get("Description") or "",
            "Date": row.get("ngay") or row.get("update_date") or row.get("Date") or "",
            "UpdatedBy": row.get("nguoi_cap_nhat") or row.get("updated_by") or row.get("UpdatedBy") or "",
        }
        for row in result.get("History") or result.get("RevisionHistory") or []
    ]

    return result


def flatten_registry() -> list[dict]:
    rows = []
    for group_name, group in PLACEHOLDER_REGISTRY.items():
        for key, meta in group.get("children", {}).items():
            row = {"key": key, "group": group_name, "type": meta.get("type", "scalar"), "desc": meta.get("desc", "")}
            if meta.get("children"):
                row["children"] = list(meta["children"])
            rows.append(row)
    return rows


def valid_scalar_keys() -> set[str]:
    return {row["key"] for row in flatten_registry() if row["type"] == "scalar"}


def valid_loop_keys() -> set[str]:
    return {row["key"] for row in flatten_registry() if row["type"] == "loop"}


def valid_child_keys(loop_name: str) -> set[str]:
    for row in flatten_registry():
        if row["key"] == loop_name:
            return set(row.get("children") or [])
    return set()
