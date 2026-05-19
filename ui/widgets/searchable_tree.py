"""Standard Treeview wrapper with scrollbars, striping, and optional empty state."""

from __future__ import annotations

try:
    import ttkbootstrap as tb
except Exception:  # pragma: no cover
    from tkinter import ttk as tb

from ui.theme.design_system import UI_THEME


class SearchableTree(tb.Frame):
    def __init__(
        self,
        parent,
        columns,
        headings,
        widths=None,
        show="headings",
        height=12,
        style="App.Treeview",
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self.tree = tb.Treeview(self, columns=columns, show=show, height=height, style=style)
        self.empty_label = tb.Label(self, text="", style="Muted.TLabel")
        self.vsb = tb.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.hsb = tb.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.hsb.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        widths = widths or [120] * len(columns)
        for idx, col in enumerate(columns):
            heading = headings[idx] if idx < len(headings) else col
            self.tree.heading(col, text=heading, command=lambda c=col: self.sort_by(c))
            stretch = idx == len(columns) - 1
            self.tree.column(col, width=widths[idx] if idx < len(widths) else 120, minwidth=60, stretch=stretch)

        self.tree.tag_configure("odd", background=UI_THEME["color_row_alt"])
        self.tree.tag_configure("even", background="#FFFFFF")

    def sort_by(self, column: str, descending: bool = False):
        rows = [(self.tree.set(iid, column), iid) for iid in self.tree.get_children("")]
        rows.sort(reverse=descending)
        for index, (_value, iid) in enumerate(rows):
            self.tree.move(iid, "", index)
        self.tree.heading(column, command=lambda: self.sort_by(column, not descending))
        self.restripe()

    def restripe(self):
        for index, iid in enumerate(self.tree.get_children("")):
            tags = [tag for tag in self.tree.item(iid, "tags") if tag not in ("odd", "even")]
            tags.append("odd" if index % 2 else "even")
            self.tree.item(iid, tags=tuple(tags))

    def set_empty_state(self, message: str):
        self.empty_label.configure(text=message)
        if self.tree.get_children(""):
            self.empty_label.grid_forget()
        else:
            self.empty_label.grid(row=0, column=0, sticky="n", pady=UI_THEME["group_gap"])


def apply_tree_defaults(tree):
    try:
        tree.configure(style="App.Treeview")
        tree.tag_configure("odd", background=UI_THEME["color_row_alt"])
        tree.tag_configure("even", background="#FFFFFF")
    except Exception:
        pass
    return tree


def restripe_tree(tree):
    try:
        for index, iid in enumerate(tree.get_children("")):
            tags = [tag for tag in tree.item(iid, "tags") if tag not in ("odd", "even")]
            tags.append("odd" if index % 2 else "even")
            tree.item(iid, tags=tuple(tags))
    except Exception:
        pass
