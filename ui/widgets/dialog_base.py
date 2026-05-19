"""Reusable dialog sizing and layout helpers."""

from __future__ import annotations

import tkinter as tk
try:
    import ttkbootstrap as tb
except Exception:  # pragma: no cover
    from tkinter import ttk as tb

from ui.theme.design_system import UI_THEME


def center_window(window: tk.Toplevel, width: int | None = None, height: int | None = None) -> None:
    window.update_idletasks()
    if width is None:
        width = max(window.winfo_width(), UI_THEME["min_dialog_width"])
    if height is None:
        height = max(window.winfo_height(), UI_THEME["min_dialog_height"])
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    x = max(0, (screen_w - width) // 2)
    y = max(0, (screen_h - height) // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


def configure_dialog(
    window: tk.Toplevel,
    parent=None,
    width: int = 820,
    height: int = 560,
    min_width: int | None = None,
    min_height: int | None = None,
    modal: bool = True,
    resizable: bool = True,
) -> None:
    min_width = min_width or min(width, UI_THEME["min_dialog_width"])
    min_height = min_height or min(height, UI_THEME["min_dialog_height"])
    window.minsize(min_width, min_height)
    window.resizable(resizable, resizable)
    if parent is not None:
        window.transient(parent)
    center_window(window, width, height)
    if modal:
        window.grab_set()


class DialogFrame(tb.Frame):
    """Standard padded frame for dialog content."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, padding=UI_THEME["dialog_pad"], **kwargs)


def make_button_bar(parent, primary=None, secondary=None):
    bar = tb.Frame(parent, padding=(0, UI_THEME["padding_y"], 0, 0))
    bar.pack(fill="x")
    if secondary:
        for label, command, style in secondary:
            tb.Button(bar, text=label, command=command, bootstyle=style).pack(side="left", padx=(0, UI_THEME["toolbar_gap"]))
    if primary:
        for label, command, style in primary:
            tb.Button(bar, text=label, command=command, bootstyle=style).pack(side="right", padx=(UI_THEME["toolbar_gap"], 0))
    return bar
