"""Small helpers for consistent form sections."""

from __future__ import annotations

try:
    import ttkbootstrap as tb
except Exception:  # pragma: no cover
    from tkinter import ttk as tb

from ui.theme.design_system import UI_THEME


def form_label(parent, text, required=False, **kwargs):
    suffix = " *" if required else ""
    return tb.Label(parent, text=f"{text}{suffix}", anchor="e", style="TLabel", **kwargs)


def section_frame(parent, title: str, **kwargs):
    return tb.Labelframe(parent, text=title, padding=UI_THEME["dialog_pad"], style="App.TLabelframe", **kwargs)


def configure_form_grid(parent, label_col: int = 0, field_col: int = 1):
    parent.columnconfigure(label_col, weight=0)
    parent.columnconfigure(field_col, weight=1)
