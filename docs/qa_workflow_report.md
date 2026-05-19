# QA Workflow Report

Date: 2026-05-19

## Round 1 - Regression Baseline

Commands:

```powershell
python -m unittest discover -s tests -v
python -m compileall .
```

Result:

- Existing unit/regression tests passed before new fixes.
- Broad compile passed, though the broad command also traversed `.venv`; later runs use targeted compile paths.

Findings:

- Migration version numbering was off by one. The first incremental patch is `_migration_v2`, but `run_migrations()` recorded it as schema version 1.
- Default Excel template did not include Rubrics, RevisionHistory, or Approval sheets.
- SQLite backup opened a destination connection without explicitly closing it.
- Generic repository validation used substring matching and produced false warnings for optional fields such as `ten_anh` and `cdr_ma`.

Fixes:

- `core/migrations.py`: migration targets now start at v2.
- `tests/test_migrations.py`: added versioning regression coverage.
- `services/excel_template_engine.py`: default template now includes Rubrics, RevisionHistory, and Approval.
- `services/placeholder_registry.py`: added approval placeholders and RevisionHistory normalization.
- `db.py`: `backup()` explicitly closes the backup SQLite connection; `close()` is idempotent and clears the connection reference.
- `repositories/base_repository.py`: narrowed persistence warnings to table-specific required fields.

## Round 2 - Workflow End-to-End

New tests:

- `tests/test_workflows_e2e.py`
- `services/syllabus_workflow_validator.py`

Covered workflows:

- Create full syllabus data set.
- Save/reopen SQLite database.
- Validate syllabus I-IX business sections.
- Bridge legacy V23 data into enterprise schema.
- Export Excel using default template.
- Reopen exported workbook with `openpyxl`.
- Verify Unicode Vietnamese values, CLO, Assessment, Rubrics, RevisionHistory, and Approval sheets.
- Detect broken duplicate CLO, invalid I/R/M level, and assessment weight total not equal to 100.

Command:

```powershell
python -W error::ResourceWarning -m unittest discover -s tests -v
```

Result:

- 35 tests passed.
- Resource warnings are clean.

## Artifact Status

The existing `excel_templates/default_syllabus_template.xlsx` could not be overwritten because Windows returned
`PermissionError: [Errno 13] Permission denied`. The file attributes were normal, so this is likely a file lock or
Google Drive sync lock.

Fallback artifacts created:

- `excel_templates/default_syllabus_template_v19.xlsx`
- `excel_templates/placeholder_catalog_v19.xlsx`

## Live Database Validation

Command result against `qlctdt.db`:

- Schema version: 19
- Enterprise schema coverage: complete
- Course count: 28

Data-quality issues in the existing dataset:

- 28 courses have no objectives.
- 28 courses have no CLO.
- 28 courses have no learning materials.
- 28 courses have no course content rows.
- 28 courses have no assessment rows.
- 28 courses have no revision history.
- 28 courses have missing author/approval signer names.

These are content completeness issues, not migration/runtime failures. They were not auto-filled because generating
academic CLO/rubric/assessment content without a source document would fabricate academic data.

## Current Gate

Passed:

```powershell
python -m compileall core repositories services controllers utils sections ui main.py enterprise_schema_dialog.py tests
python -W error::ResourceWarning -m unittest discover -s tests -v
python -c "import main, enterprise_schema_dialog, settings_dialog, excel_template_manager_dialog, template_manager_dialog; print('ui imports ok')"
```

Not fully automated in this round:

- Real GUI click simulation.
- OCR benchmark, because this V23 checkout does not currently contain an OCR pipeline implementation or OCR fixtures.
- Excel open in Microsoft Excel itself; workbook integrity is validated through `openpyxl`.
