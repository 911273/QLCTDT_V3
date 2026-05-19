"""Enterprise schema readiness and dynamic metadata browser."""

from __future__ import annotations

import tkinter as tk
try:
    import ttkbootstrap as tb
except Exception:  # pragma: no cover
    from tkinter import ttk as tb

from services.enterprise_schema_service import EnterpriseSchemaService
from ui.widgets.dialog_base import DialogFrame, configure_dialog
from ui.widgets.searchable_tree import SearchableTree


class EnterpriseSchemaDialog(tb.Toplevel):
    """Small UI surface for schema-driven enterprise modules."""

    def __init__(self, parent, db):
        super().__init__(parent)
        self.title("Enterprise Academic QA Schema")
        self.db = db
        self.service = EnterpriseSchemaService(db)
        self._entity_names: list[str] = []
        configure_dialog(self, parent, width=1040, height=640, min_width=900, min_height=560)
        self._build()
        self._refresh()

    def _build(self) -> None:
        root = DialogFrame(self)
        root.pack(fill="both", expand=True)

        header = tb.Frame(root)
        header.pack(fill="x", pady=(0, 10))
        tb.Label(header, text="Enterprise Academic QA Foundation", style="AppTitle.TLabel").pack(side="left")
        tb.Button(header, text="Validate", bootstyle="info", command=self._validate_schema).pack(side="right", padx=(6, 0))
        tb.Button(header, text="Bridge legacy data", bootstyle="success", command=self._bridge_legacy).pack(side="right")

        self.status_var = tk.StringVar(value="Ready")
        tb.Label(root, textvariable=self.status_var, style="Muted.TLabel").pack(fill="x", pady=(0, 8))

        paned = tb.Panedwindow(root, orient="horizontal")
        paned.pack(fill="both", expand=True)

        left = tb.Frame(paned, padding=(0, 0, 8, 0))
        right = tb.Frame(paned, padding=(8, 0, 0, 0))
        paned.add(left, weight=1)
        paned.add(right, weight=2)

        tb.Label(left, text="Entities", style="SectionHeader.TLabel").pack(anchor="w", pady=(0, 6))
        self.entity_tree = SearchableTree(
            left,
            columns=("entity", "group", "fields"),
            headings=("Entity", "Domain", "Fields"),
            widths=(190, 140, 70),
            height=18,
        )
        self.entity_tree.pack(fill="both", expand=True)
        self.entity_tree.tree.bind("<<TreeviewSelect>>", self._on_entity_selected)

        tb.Label(right, text="Dynamic form fields", style="SectionHeader.TLabel").pack(anchor="w", pady=(0, 6))
        self.field_tree = SearchableTree(
            right,
            columns=("field", "type", "widget", "required", "json"),
            headings=("Field", "Type", "Widget", "Required", "JSON"),
            widths=(210, 130, 130, 80, 70),
            height=18,
        )
        self.field_tree.pack(fill="both", expand=True)

        self.detail = tk.Text(right, height=5, wrap="word")
        self.detail.pack(fill="x", pady=(8, 0))
        self.detail.configure(state="disabled")

    def _refresh(self) -> None:
        result = self.service.ensure_ready()
        entities = self.service.repo.list_entities()
        self._entity_names = []
        self.entity_tree.tree.delete(*self.entity_tree.tree.get_children())
        for index, row in enumerate(entities):
            entity = row["entity_name"]
            self._entity_names.append(entity)
            fields = len(self.service.repo.form_schema(entity))
            self.entity_tree.tree.insert(
                "",
                "end",
                iid=str(index),
                values=(entity, row.get("domain_group") or "", fields),
                tags=("even" if index % 2 == 0 else "odd",),
            )
        self.entity_tree.set_empty_state("No enterprise schema metadata.")
        coverage = result["coverage"]
        self.status_var.set(
            f"Schema tables: {coverage['table_count']} | complete: {coverage['complete']} | "
            f"created: {result['upgrade']['created']} | altered: {result['upgrade']['altered']}"
        )
        if self._entity_names:
            self.entity_tree.tree.selection_set("0")
            self._load_fields(self._entity_names[0])

    def _on_entity_selected(self, _event=None) -> None:
        selected = self.entity_tree.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        if idx < len(self._entity_names):
            self._load_fields(self._entity_names[idx])

    def _load_fields(self, entity: str) -> None:
        form = self.service.get_dynamic_form_schema(entity)
        self.field_tree.tree.delete(*self.field_tree.tree.get_children())
        for index, field in enumerate(form["fields"]):
            self.field_tree.tree.insert(
                "",
                "end",
                values=(
                    field["field_name"],
                    field["declared_type"],
                    field["widget_type"],
                    "yes" if field["required"] else "",
                    "yes" if field["json_path_enabled"] else "",
                ),
                tags=("even" if index % 2 == 0 else "odd",),
            )
        self.field_tree.set_empty_state("No field metadata.")
        self._set_detail(
            f"Entity: {entity}\n"
            f"Content type aware: {'yes' if entity == 'syllabus' else 'no'}\n"
            f"Fields are loaded from academic_field_meta, not hardcoded in the dialog."
        )

    def _validate_schema(self) -> None:
        coverage = self.service.validate_schema_coverage()
        if coverage["complete"]:
            self.status_var.set(f"Schema coverage complete: {coverage['table_count']} domain tables.")
            self._set_detail("All enterprise schema tables and columns are present.")
            return
        self.status_var.set("Schema coverage has gaps.")
        self._set_detail(
            "Missing tables: "
            + ", ".join(coverage["missing_tables"])
            + "\nMissing columns: "
            + str(coverage["missing_columns"])
        )

    def _bridge_legacy(self) -> None:
        self.status_var.set("Bridging legacy V23 data into enterprise tables...")
        self.update_idletasks()
        counts = self.service.bridge_legacy_data()
        self.status_var.set("Legacy bridge completed.")
        self._set_detail("\n".join(f"{key}: {value}" for key, value in counts.items()))
        self._refresh()

    def _set_detail(self, text: str) -> None:
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("1.0", text)
        self.detail.configure(state="disabled")
