# Enterprise Academic QA Foundation

This slice adds the metadata-driven foundation for the larger academic QA system.

## Scope Completed

- Full `academic_system` schema registry in `core/enterprise_schema.py`.
- Migration v19 creates missing enterprise tables and adds missing columns to legacy tables that already exist.
- Field metadata is generated into `academic_entity_meta` and `academic_field_meta` for dynamic UI forms.
- `EnterpriseRepository` provides guarded generic CRUD for schema-defined entities.
- `EnterpriseSchemaService` validates schema coverage and bridges current V23 data into enterprise tables.
- `EnterpriseSchemaDialog` exposes schema validation, metadata browsing, and legacy bridge actions from the desktop app.

## Non-Destructive Compatibility

The current V23 app still uses legacy tables such as `hoc_phan`, `khoa`, `giang_vien`, and `clo`.
Migration v19 does not rebuild or delete those tables. For conflicting enterprise names, especially `clo`, it adds
the new enterprise columns in place so existing screens and new schema-driven workflows can coexist.

Legacy-to-enterprise links are tracked in `legacy_academic_bridge`:

- `khoa` -> `department`
- `giang_vien` -> `instructor`
- `chuong_trinh_dao_tao` -> `program`
- `chuyen_nganh` -> `major`
- `hoc_phan` -> `course`
- `hoc_phan` -> `syllabus`
- `muc_tieu` -> `syllabus_objective`
- `hoc_lieu` -> `syllabus_material`

## Dynamic UI Contract

New enterprise forms should read:

- `academic_entity_meta` for module/entity navigation.
- `academic_field_meta` for field order, widget type, JSON field handling, required fields, and readonly fields.
- `EnterpriseSchemaService.get_dynamic_form_schema(entity_name)` for UI-ready field definitions.

This keeps form rendering schema-driven instead of hardcoding fields per dialog.

## Validation

Run:

```powershell
python -m unittest discover -s tests -v
```

The enterprise tests cover:

- All domain tables are present after upgrade.
- Existing `clo` is upgraded with enterprise columns.
- Metadata rows are generated.
- Generic repository insert/form schema works.
- Legacy bridge is idempotent.
