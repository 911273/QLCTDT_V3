"""Tk dialogs for Excel template management and export."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox

import ttkbootstrap as tb

from services.excel_template_service import ExcelTemplateService
from services.excel_export_service import ExcelExportService
from ui.theme.design_system import UI_THEME
from ui.widgets.dialog_base import configure_dialog
from ui.widgets.searchable_tree import apply_tree_defaults, restripe_tree


class ExcelTemplateManagerDialog(tb.Toplevel):
    def __init__(self, parent, db, hp_id: int | None = None):
        super().__init__(parent)
        self.db = db
        self.hp_id = hp_id
        self.svc = ExcelTemplateService(db)
        self.export_svc = ExcelExportService(db)
        self._templates = []

        self.title("Quan ly Excel Template")
        configure_dialog(self, parent, width=960, height=620, min_width=820, min_height=500)
        self._build_ui()
        self._refresh_list()

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 960) // 2
        y = (self.winfo_screenheight() - 620) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        self.configure(padx=UI_THEME["padding_x"], pady=UI_THEME["padding_y"])
        header = tb.Label(self, text="Quan ly Excel Template dong", style="AppTitle.TLabel")
        header.pack(anchor="w", pady=(0, 10))

        split = tb.Frame(self)
        split.pack(fill="both", expand=True)

        left = tb.Labelframe(split, text="Danh sach template", padding=8)
        left.pack(side="left", fill="both", padx=(0, 8))

        self.tree = tb.Treeview(left, columns=("ten", "count", "default", "updated"), show="headings", height=16)
        apply_tree_defaults(self.tree)
        for col, text, width in [
            ("ten", "Ten", 210),
            ("count", "Placeholder", 85),
            ("default", "Mac dinh", 85),
            ("updated", "Cap nhat", 110),
        ]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="center" if col != "ten" else "w")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        btns = tb.Frame(left)
        btns.pack(fill="x", pady=(8, 0))
        tb.Button(btns, text="Upload .xlsx", command=self._upload, bootstyle="success").pack(side="left", padx=2)
        tb.Button(btns, text="Xoa", command=self._delete, bootstyle="danger-outline").pack(side="left", padx=2)

        right = tb.Labelframe(split, text="Chi tiet", padding=10)
        right.pack(side="left", fill="both", expand=True)

        form = tb.Frame(right)
        form.pack(fill="x")
        tb.Label(form, text="Ten:", width=12, anchor="e").grid(row=0, column=0, sticky="e", pady=3)
        self.var_ten = tk.StringVar()
        tb.Entry(form, textvariable=self.var_ten, width=36).grid(row=0, column=1, sticky="w", pady=3)
        tb.Label(form, text="Mo ta:", width=12, anchor="e").grid(row=1, column=0, sticky="e", pady=3)
        self.var_mo_ta = tk.StringVar()
        tb.Entry(form, textvariable=self.var_mo_ta, width=48).grid(row=1, column=1, sticky="w", pady=3)
        tb.Label(form, text="File:", width=12, anchor="e").grid(row=2, column=0, sticky="e", pady=3)
        self.var_path = tk.StringVar()
        tb.Label(form, textvariable=self.var_path, font=("Consolas", 8)).grid(row=2, column=1, sticky="w", pady=3)

        action_row = tb.Frame(right)
        action_row.pack(fill="x", pady=(8, 6))
        tb.Button(action_row, text="Dat mac dinh", command=self._set_default, bootstyle="warning").pack(side="left", padx=2)
        tb.Button(action_row, text="Cap nhat ten", command=self._save_name, bootstyle="secondary-outline").pack(side="left", padx=2)
        tb.Button(action_row, text="Validate", command=self._validate, bootstyle="info-outline").pack(side="left", padx=2)

        helper_row = tb.Frame(right)
        helper_row.pack(fill="x", pady=(0, 6))
        tb.Button(helper_row, text="Tao template mau", command=self._generate_default, bootstyle="primary-outline").pack(side="left", padx=2)
        tb.Button(helper_row, text="Xuat catalog placeholder", command=self._export_catalog, bootstyle="light").pack(side="left", padx=2)
        tb.Button(helper_row, text="Preview placeholders", command=self._preview_placeholders, bootstyle="light").pack(side="left", padx=2)

        self.txt = tk.Text(right, height=16, font=("Consolas", 9), wrap="word")
        self.txt.pack(fill="both", expand=True, pady=(4, 8))

        bottom = tb.Frame(right)
        bottom.pack(fill="x")
        if self.hp_id:
            tb.Button(bottom, text="Xuat de cuong bang template nay", command=self._export_current, bootstyle="success").pack(side="left")
        tb.Button(bottom, text="Dong", command=self.destroy, bootstyle="secondary-outline").pack(side="right")

    def _refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._templates = self.svc.get_all()
        for tpl in self._templates:
            self.tree.insert(
                "",
                "end",
                iid=str(tpl["id"]),
                values=(
                    tpl.get("ten", ""),
                    tpl.get("placeholder_count", 0),
                    "Co" if tpl.get("la_mac_dinh") else "-",
                    (tpl.get("updated_at") or tpl.get("created_at") or "")[:16],
                ),
            )
        restripe_tree(self.tree)

    def _selected_id(self) -> int | None:
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _selected_tpl(self) -> dict | None:
        tid = self._selected_id()
        return next((tpl for tpl in self._templates if tpl["id"] == tid), None) if tid else None

    def _on_select(self, _event=None):
        tpl = self._selected_tpl()
        if not tpl:
            return
        self.var_ten.set(tpl.get("ten", ""))
        self.var_mo_ta.set(tpl.get("mo_ta", ""))
        self.var_path.set(os.path.basename(tpl.get("file_path") or ""))
        self._write(f"Template: {tpl.get('ten')}\nFile: {tpl.get('file_path')}\n")

    def _write(self, text: str):
        self.txt.delete("1.0", "end")
        self.txt.insert("end", text)

    def _upload(self):
        path = filedialog.askopenfilename(title="Chon Excel template", filetypes=[("Excel", "*.xlsx")], parent=self)
        if not path:
            return
        name = os.path.splitext(os.path.basename(path))[0]
        try:
            template_id = self.svc.upload(path, name)
            self.svc.set_default(template_id) if not self._templates else None
            self._refresh_list()
            messagebox.showinfo("Thanh cong", "Da upload template Excel.", parent=self)
        except Exception as exc:
            messagebox.showerror("Loi upload", str(exc), parent=self)

    def _delete(self):
        tid = self._selected_id()
        if not tid:
            return
        if messagebox.askyesno("Xac nhan", "Xoa template Excel nay?", parent=self):
            self.svc.delete(tid)
            self._refresh_list()

    def _set_default(self):
        tid = self._selected_id()
        if not tid:
            return
        self.svc.set_default(tid)
        self._refresh_list()

    def _save_name(self):
        tid = self._selected_id()
        if not tid:
            return
        self.svc.update_name(tid, self.var_ten.get().strip(), self.var_mo_ta.get().strip())
        self._refresh_list()

    def _validate(self):
        tpl = self._selected_tpl()
        if not tpl:
            return
        try:
            context = self.export_svc.build_context(self.hp_id) if self.hp_id else {}
            result = self.svc.validate_template_file(tpl["file_path"], context)
            if result["valid"]:
                self._write(f"Template hop le.\nTong placeholder/marker: {result.get('total_keys', 0)}")
            else:
                lines = ["Template co loi:"]
                for err in result["errors"]:
                    line = f"Sheet: {err['sheet']} Cell: {err['cell']} {err['message']}"
                    if err.get("suggestion"):
                        line += f" Suggestion: {err['suggestion']}"
                    lines.append(line)
                self._write("\n".join(lines))
        except Exception as exc:
            messagebox.showerror("Loi validate", str(exc), parent=self)

    def _preview_placeholders(self):
        tpl = self._selected_tpl()
        if not tpl:
            return
        scan = self.svc.scan_placeholders(tpl["file_path"])
        lines = ["Scalars:"]
        lines += [f"- {p['sheet']}!{p['cell']}: {p['name']}" for p in scan["scalars"]]
        lines.append("\nLoops:")
        lines += [f"- {p['sheet']}!{p['cell']}: {p['kind']} {p['name']}" for p in scan["loops"]]
        self._write("\n".join(lines))

    def _generate_default(self):
        path = filedialog.asksaveasfilename(
            title="Luu template mau",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile="default_syllabus_template.xlsx",
            parent=self,
        )
        if not path:
            return
        self.svc.create_default_template(path)
        messagebox.showinfo("Thanh cong", f"Da tao template mau:\n{path}", parent=self)

    def _export_catalog(self):
        path = filedialog.asksaveasfilename(
            title="Luu placeholder catalog",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile="placeholder_catalog.xlsx",
            parent=self,
        )
        if not path:
            return
        self.svc.create_placeholder_catalog(path)
        messagebox.showinfo("Thanh cong", f"Da xuat catalog:\n{path}", parent=self)

    def _export_current(self):
        tpl = self._selected_tpl()
        if not tpl or not self.hp_id:
            return
        default = f"{tpl.get('ten', 'syllabus')}.xlsx"
        out = filedialog.asksaveasfilename(
            title="Luu de cuong Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=default,
            parent=self,
        )
        if not out:
            return
        try:
            self.export_svc.export_with_template(self.hp_id, tpl["id"], out)
            messagebox.showinfo("Thanh cong", f"Da xuat Excel:\n{out}", parent=self)
        except Exception as exc:
            messagebox.showerror("Loi xuat Excel", str(exc), parent=self)


class ExcelTemplateChoiceDialog(tb.Toplevel):
    def __init__(self, parent, db, hp_id: int):
        super().__init__(parent)
        self.db = db
        self.hp_id = hp_id
        self.svc = ExcelTemplateService(db)
        self.export_svc = ExcelExportService(db)
        self._templates = self.svc.get_all()

        self.title("Chon Excel Template")
        configure_dialog(self, parent, width=560, height=380, min_width=500, min_height=320)
        self._build_ui()

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 520) // 2
        y = (self.winfo_screenheight() - 360) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        frame = tb.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)
        tb.Label(frame, text="Chon template Excel de xuat", style="SectionHeader.TLabel").pack(anchor="w", pady=(0, 8))
        self.tree = tb.Treeview(frame, columns=("name", "default"), show="headings", height=9)
        apply_tree_defaults(self.tree)
        self.tree.heading("name", text="Template")
        self.tree.heading("default", text="Mac dinh")
        self.tree.column("name", width=330)
        self.tree.column("default", width=90, anchor="center")
        self.tree.pack(fill="both", expand=True)
        for tpl in self._templates:
            self.tree.insert("", "end", iid=str(tpl["id"]), values=(tpl.get("ten", ""), "Co" if tpl.get("la_mac_dinh") else "-"))
            if tpl.get("la_mac_dinh"):
                self.tree.selection_set(str(tpl["id"]))
        if self._templates and not self.tree.selection():
            self.tree.selection_set(str(self._templates[0]["id"]))
        restripe_tree(self.tree)

        btns = tb.Frame(frame)
        btns.pack(fill="x", pady=(10, 0))
        tb.Button(btns, text="Quan ly template", command=self._open_manager, bootstyle="secondary-outline").pack(side="left")
        tb.Button(btns, text="Xuat", command=self._export, bootstyle="success").pack(side="right", padx=4)
        tb.Button(btns, text="Dong", command=self.destroy, bootstyle="secondary-outline").pack(side="right")

    def _selected_id(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _open_manager(self):
        ExcelTemplateManagerDialog(self, self.db, self.hp_id)
        self._templates = self.svc.get_all()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for tpl in self._templates:
            self.tree.insert("", "end", iid=str(tpl["id"]), values=(tpl.get("ten", ""), "Co" if tpl.get("la_mac_dinh") else "-"))
        restripe_tree(self.tree)

    def _export(self):
        template_id = self._selected_id()
        if not template_id:
            messagebox.showwarning("Chua chon", "Hay chon template Excel.", parent=self)
            return
        out = filedialog.asksaveasfilename(
            title="Luu de cuong Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile="de_cuong_chi_tiet.xlsx",
            parent=self,
        )
        if not out:
            return
        try:
            self.export_svc.export_with_template(self.hp_id, template_id, out)
            messagebox.showinfo("Thanh cong", f"Da xuat Excel:\n{out}", parent=self)
            self.destroy()
        except Exception as exc:
            messagebox.showerror("Loi xuat Excel", str(exc), parent=self)
