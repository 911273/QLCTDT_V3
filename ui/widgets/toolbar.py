"""Reusable action toolbar helpers."""

from __future__ import annotations

try:
    import ttkbootstrap as tb
except Exception:  # pragma: no cover
    from tkinter import ttk as tb

from ui.theme.design_system import UI_THEME


class StandardToolbar(tb.Frame):
    def __init__(self, parent, actions=None, **kwargs):
        super().__init__(parent, padding=(0, 0, 0, UI_THEME["padding_y"]), **kwargs)
        self._count = 0
        for action in actions or []:
            if action is None:
                self.add_separator()
            else:
                self.add_action(*action)

    def add_action(self, text, command, style="secondary-outline", side="left"):
        btn = tb.Button(self, text=text, command=command, bootstyle=style)
        btn.pack(side=side, padx=(0, UI_THEME["toolbar_gap"]))
        self._count += 1
        return btn

    def add_separator(self):
        sep = tb.Separator(self, orient="vertical")
        sep.pack(side="left", fill="y", padx=(0, UI_THEME["toolbar_gap"]))
        return sep
