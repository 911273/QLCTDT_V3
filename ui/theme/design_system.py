"""Central UI design tokens and ttkbootstrap style setup."""

from __future__ import annotations

try:
    import ttkbootstrap as tb
except Exception:  # pragma: no cover - import fallback is for environments without UI deps.
    tb = None


UI_THEME = {
    "padding_x": 10,
    "padding_y": 8,
    "section_gap": 12,
    "group_gap": 16,
    "dialog_pad": 14,
    "dialog_padding": 14,
    "toolbar_gap": 6,
    "row_height": 30,
    "tree_header_height": 32,
    "font_main": ("Segoe UI", 10),
    "font_small": ("Segoe UI", 9),
    "font_title": ("Segoe UI", 13, "bold"),
    "font_section": ("Segoe UI", 11, "bold"),
    "font_mono": ("Consolas", 9),
    "color_surface": "#F8FAFC",
    "color_border": "#CBD5E1",
    "color_muted": "#64748B",
    "color_header": "#1E3A5F",
    "color_row_alt": "#F1F5F9",
    "color_focus": "#2563EB",
    "min_dialog_width": 720,
    "min_dialog_height": 480,
}


def spacing(name: str = "padding_x") -> int:
    return int(UI_THEME[name])


def setup_app_styles() -> None:
    if tb is None:
        return
    style = tb.Style()
    style.configure(".", font=UI_THEME["font_main"])
    style.configure("AppTitle.TLabel", font=UI_THEME["font_title"])
    style.configure("SectionHeader.TLabel", font=UI_THEME["font_section"])
    style.configure("Muted.TLabel", font=UI_THEME["font_small"], foreground=UI_THEME["color_muted"])
    style.configure("App.Treeview", font=UI_THEME["font_main"], rowheight=UI_THEME["row_height"])
    style.configure(
        "App.Treeview.Heading",
        font=("Segoe UI", 10, "bold"),
        background=UI_THEME["color_header"],
        foreground="white",
        relief="flat",
    )
    style.map(
        "App.Treeview",
        background=[("selected", UI_THEME["color_focus"])],
        foreground=[("selected", "white")],
    )
    style.configure("App.TLabelframe", padding=UI_THEME["dialog_pad"])
    style.configure("App.TLabelframe.Label", font=UI_THEME["font_section"])
