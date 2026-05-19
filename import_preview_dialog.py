import tkinter as tk

import ttkbootstrap as tb
from ttkbootstrap.constants import *

from sections.base_section import make_tree, set_window_icon
from ui.theme.design_system import UI_THEME
from ui.widgets.dialog_base import configure_dialog
from ui.widgets.searchable_tree import restripe_tree


class ImportPreviewDialog(tb.Toplevel):
    def __init__(self, parent, preview_items):
        """
        Args:
            parent: Parent window.
            preview_items: List of dicts {file_name, data, status, existing_hp, selected, error}.
        """
        super().__init__(parent)
        set_window_icon(self)
        self.title("Xem truoc du lieu nhap tu Word")
        self.preview_items = preview_items
        self.result = None

        configure_dialog(self, parent, width=1040, height=680, min_width=840, min_height=520)
        self._build_ui()
        self._populate_tree()

    def _build_ui(self):
        main_frame = tb.Frame(self, padding=UI_THEME["dialog_padding"])
        main_frame.pack(fill=BOTH, expand=YES)

        total = len(self.preview_items)
        errors = len([i for i in self.preview_items if i["status"] == "ERROR"])
        updates = len([i for i in self.preview_items if i["status"] == "UPDATE"])
        news = len([i for i in self.preview_items if i["status"] == "NEW"])

        header_lbl = tb.Label(
            main_frame,
            text=f"Tim thay {total} hoc phan. (Moi: {news}, Cap nhat: {updates}, Loi: {errors})",
            style="SectionHeader.TLabel",
        )
        header_lbl.pack(anchor=W, pady=(0, UI_THEME["padding_y"]))

        info_lbl = tb.Label(
            main_frame,
            text="Chon cac hoc phan muon luu vao co so du lieu. Trang thai 'Cap nhat' se ghi de du lieu cu.",
            style="Muted.TLabel",
        )
        info_lbl.pack(anchor=W, pady=(0, UI_THEME["padding_y"]))

        cols = ("select", "file_name", "ma_hp", "ten_hp", "status")
        heads = ("Chon", "Ten file", "Ma hoc phan", "Ten hoc phan", "Trang thai")
        widths = (60, 220, 130, 380, 120)

        self.tree_frame, self.tree = make_tree(main_frame, cols, heads, widths, height=15)
        self.tree_frame.pack(fill=BOTH, expand=YES)

        self.tree.tag_configure("NEW", foreground="#2e7d32")
        self.tree.tag_configure("UPDATE", foreground="#b26a00")
        self.tree.tag_configure("ERROR", foreground="#b00020")

        action_fm = tb.Frame(main_frame)
        action_fm.pack(fill=X, pady=UI_THEME["padding_y"])

        tb.Button(action_fm, text="Chon tat ca", bootstyle=OUTLINE, command=self._select_all).pack(side=LEFT, padx=4)
        tb.Button(action_fm, text="Bo chon tat ca", bootstyle=OUTLINE, command=self._deselect_all).pack(side=LEFT, padx=4)

        btn_fm = tb.Frame(main_frame)
        btn_fm.pack(fill=X, side=BOTTOM, pady=(UI_THEME["section_gap"], 0))

        self.btn_confirm = tb.Button(
            btn_fm, text="Xac nhan nhap", bootstyle=SUCCESS, command=self._on_confirm
        )
        self.btn_confirm.pack(side=RIGHT, padx=5)
        tb.Button(btn_fm, text="Huy bo", bootstyle=DANGER, command=self.destroy).pack(side=RIGHT, padx=5)

        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<Double-1>", self._show_logs)

    def _populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        for i, item in enumerate(self.preview_items):
            status_text = item["status"]
            if status_text == "UPDATE":
                status_text = "Cap nhat"
            elif status_text == "NEW":
                status_text = "Moi"
            elif status_text == "ERROR":
                status_text = "Loi"

            check_mark = " [X] " if item.get("selected") else " [  ] "
            ma = item["data"]["hp"].get("ma", "") if "data" in item else ""
            ten = item["data"].get("ten_viet", "") if "data" in item else item.get("file_name", "")

            self.tree.insert(
                "",
                END,
                iid=str(i),
                values=(check_mark, item["file_name"], ma, ten, status_text),
                tags=(item["status"], "odd" if i % 2 else "even"),
            )
        restripe_tree(self.tree)

    def _on_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#1":
                item_id = self.tree.identify_row(event.y)
                if item_id:
                    idx = int(item_id)
                    self.preview_items[idx]["selected"] = not self.preview_items[idx]["selected"]
                    if self.preview_items[idx]["status"] == "ERROR":
                        self.preview_items[idx]["selected"] = False
                    self._populate_tree()

    def _show_logs(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        item = self.preview_items[idx]

        logs = item.get("logs", [])
        if not logs:
            if item["status"] == "ERROR":
                logs = [("error", "Critical", item.get("error", "Unknown error"))]
            else:
                logs = [("info", "He thong", "Khong co log chi tiet.")]

        top = tb.Toplevel(self)
        top.title(f"Log boc tach: {item['file_name']}")
        configure_dialog(top, self, width=640, height=420, min_width=520, min_height=320)

        txt = tk.Text(top, font=UI_THEME["font_mono"], padx=10, pady=10)
        txt.pack(fill=BOTH, expand=YES)

        for level, part, msg in logs:
            icon = "OK" if level == "success" else "ERR"
            txt.insert(END, f"{icon} [{part}]: {msg}\n")

        txt.config(state=DISABLED)
        tb.Button(top, text="Dong", command=top.destroy).pack(pady=10)

    def _select_all(self):
        for item in self.preview_items:
            if item["status"] != "ERROR":
                item["selected"] = True
        self._populate_tree()

    def _deselect_all(self):
        for item in self.preview_items:
            item["selected"] = False
        self._populate_tree()

    def _on_confirm(self):
        self.result = [item for item in self.preview_items if item.get("selected")]
        self.destroy()
