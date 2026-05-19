# UI/UX Audit and Refactor Plan

## Scope scanned

- Entry point and main shell: `main.py`
- Section framework and shared controls: `sections/base_section.py`, `sections/sec*.py`
- Dialog surfaces: `settings_dialog.py`, `import_preview_dialog.py`, `shared_data_dialog.py`, `template_manager_dialog.py`, `version_history_dialog.py`, `statistics_dialog.py`, `excel_template_manager_dialog.py`
- Utility UI helpers: `utils/ui_utils.py`, `utils/global_picker.py`, `utils/threading_utils.py`
- Main tree behavior: `controllers/tree_controller.py`

The module names in the task description do not exactly match this checkout. The real UI is concentrated in the files above.

## Main findings

1. Layout spacing is inconsistent. Most dialogs use local `padx`, `pady`, fonts, and fixed `geometry()` calls.
2. Dialog behavior is duplicated. Many `Toplevel` classes manually repeat `transient`, `grab_set`, centering, size, and minimum size logic.
3. Treeview setup is uneven. `sections/base_section.make_tree()` provides a helper, but the main tree and some dialogs used raw `Treeview` setup.
4. Table readability needs a shared treatment: row height, headings, alternate row color, and refresh-time striping were not consistently applied.
5. Import preview had a concrete button packing bug: the cancel button was constructed but never packed, while the confirm button was packed twice.
6. Typography is fragmented: `Arial`, `Times New Roman`, `Consolas`, inline bold, and local colors appear across UI modules.
7. Long dialogs rely on fixed sizes. This makes smaller screens and resize flows brittle.
8. Feedback is still messagebox-heavy. A status bar and inline validation can reduce modal interruptions in later phases.
9. Empty state and preview patterns are not standardized. Tables with no data often just appear blank.
10. Some text and icons are stored with mojibake in legacy files. This should be fixed in a dedicated encoding/content pass, not mixed into business refactors.

## Design system introduced

The shared design tokens live in `ui/theme/design_system.py`:

- spacing: `padding_x`, `padding_y`, `section_gap`, `group_gap`, `dialog_padding`
- typography: main, title, section, small, mono fonts
- tree metrics: row height and heading height
- semantic colors for muted text, alternate rows, borders, focus, danger, success
- shared ttk styles for app title, section header, muted text, labelframe, and treeview

## Component layer introduced

- `ui/widgets/dialog_base.py`: shared modal configuration, centering, dialog frame, button bar.
- `ui/widgets/searchable_tree.py`: shared tree defaults, sort behavior, alternate row striping, empty state wrapper.
- `ui/widgets/toolbar.py`: reusable toolbar/action row.
- `ui/widgets/form_section.py`: form label and section helpers.

## Refactor strategy

Phase 1 focuses on safe foundation:

- centralize tokens and styles
- route existing helper functions through shared tree defaults
- normalize modal sizing and centering
- fix concrete UI bugs

Phase 2 should migrate high-traffic dialogs to the component layer:

- settings
- template managers
- shared data manager
- version/history
- statistics

Phase 3 should add UX features:

- reusable search/filter bars
- context menus for table actions
- inline validation surfaces
- standard empty states
- preview panels for long text

Phase 4 should polish:

- keyboard shortcuts
- accessibility/focus pass
- performance pass for large table refreshes
- dark-mode hardcoded color audit

## Risks and boundaries

- Business logic should stay in controllers/services/repositories. UI refactors should only call existing public methods.
- Encoding cleanup is needed, but it can create large diffs. It should be done as a separate reviewable slice.
- Large dialogs should be converted incrementally. A full rewrite of every screen in one pass would be high-risk for this legacy Tkinter codebase.
