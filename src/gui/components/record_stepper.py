"""Bottom-of-canvas live spreadsheet record stepper bar."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from src.core.data_loader import SpreadsheetData
from src.gui.styles import (
    COLOR_BG_PANEL,
    COLOR_BORDER,
    COLOR_PRIMARY_HEADER,
    COLOR_TEXT_SECONDARY,
    FONT_BODY_BOLD,
    FONT_SMALL,
)


class LiveRecordStepper(ttk.Frame):
    """Navigation bar allowing teachers to step through loaded student records on the canvas."""

    def __init__(
        self,
        parent: tk.Misc,
        on_record_changed: Optional[Callable[[Optional[dict[str, str]], int], None]] = None,
    ) -> None:
        super().__init__(parent, style="Card.TFrame")
        self.on_record_changed = on_record_changed
        self.spreadsheet: Optional[SpreadsheetData] = None
        self.current_index: int = 0
        self.var_live_preview = tk.BooleanVar(value=True)

        self._build_ui()
        self._update_display()

    def _build_ui(self) -> None:
        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(side=tk.TOP, fill=tk.X)

        inner = tk.Frame(self, bg=COLOR_BG_PANEL, padx=12, pady=6)
        inner.pack(side=tk.TOP, fill=tk.X)

        self.chk_live = ttk.Checkbutton(
            inner,
            text="Preview Live Spreadsheet Data on Canvas",
            variable=self.var_live_preview,
            style="Card.TCheckbutton",
            command=self._on_toggle_preview,
        )
        self.chk_live.pack(side=tk.LEFT, padx=(0, 14))

        nav_frame = tk.Frame(inner, bg=COLOR_BG_PANEL)
        nav_frame.pack(side=tk.LEFT)

        self.btn_first = ttk.Button(
            nav_frame, text="|< First", width=8, command=self.go_first
        )
        self.btn_first.pack(side=tk.LEFT, padx=2)

        self.btn_prev = ttk.Button(
            nav_frame, text="< Prev Record", width=13, command=self.go_prev
        )
        self.btn_prev.pack(side=tk.LEFT, padx=2)

        self.lbl_counter = tk.Label(
            nav_frame,
            text="Record 0 of 0",
            bg="#EEF2FF",
            fg=COLOR_PRIMARY_HEADER,
            font=FONT_BODY_BOLD,
            padx=10,
            pady=3,
        )
        self.lbl_counter.pack(side=tk.LEFT, padx=6)

        self.btn_next = ttk.Button(
            nav_frame, text="Next Record >", width=13, command=self.go_next
        )
        self.btn_next.pack(side=tk.LEFT, padx=2)

        self.btn_last = ttk.Button(
            nav_frame, text="Last >|", width=8, command=self.go_last
        )
        self.btn_last.pack(side=tk.LEFT, padx=2)

        self.lbl_row_summary = tk.Label(
            inner,
            text="No spreadsheet loaded",
            bg=COLOR_BG_PANEL,
            fg=COLOR_TEXT_SECONDARY,
            font=FONT_SMALL,
            anchor="e",
        )
        self.lbl_row_summary.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(12, 0))

    def set_spreadsheet(self, data: Optional[SpreadsheetData]) -> None:
        """Sets the active SpreadsheetData and resets stepper to the first record."""
        self.spreadsheet = data
        self.current_index = 0
        self._update_display()
        self._emit_change()

    def get_active_preview_record(self) -> Optional[dict[str, str]]:
        """Returns the current record dictionary if live preview is enabled, else None."""
        if not self.var_live_preview.get() or self.spreadsheet is None or not self.spreadsheet.rows:
            return None
        safe_idx = max(0, min(self.current_index, len(self.spreadsheet.rows) - 1))
        return self.spreadsheet.rows[safe_idx]

    def go_first(self) -> None:
        if self.spreadsheet and self.spreadsheet.rows:
            self.current_index = 0
            self._update_display()
            self._emit_change()

    def go_prev(self) -> None:
        if self.spreadsheet and self.spreadsheet.rows and self.current_index > 0:
            self.current_index -= 1
            self._update_display()
            self._emit_change()

    def go_next(self) -> None:
        if (
            self.spreadsheet
            and self.spreadsheet.rows
            and self.current_index < len(self.spreadsheet.rows) - 1
        ):
            self.current_index += 1
            self._update_display()
            self._emit_change()

    def go_last(self) -> None:
        if self.spreadsheet and self.spreadsheet.rows:
            self.current_index = len(self.spreadsheet.rows) - 1
            self._update_display()
            self._emit_change()

    def _on_toggle_preview(self) -> None:
        self._update_display()
        self._emit_change()

    def _update_display(self) -> None:
        has_rows = self.spreadsheet is not None and len(self.spreadsheet.rows) > 0
        if not has_rows or self.spreadsheet is None:
            self.lbl_counter.config(text="Record 0 of 0")
            self.lbl_row_summary.config(text="No spreadsheet loaded (.xlsx / .csv)")
            for btn in (self.btn_first, self.btn_prev, self.btn_next, self.btn_last):
                btn.config(state="disabled")
            return

        total = len(self.spreadsheet.rows)
        self.current_index = max(0, min(self.current_index, total - 1))
        self.lbl_counter.config(text=f"Record {self.current_index + 1} of {total}")

        self.btn_first.config(state="normal" if self.current_index > 0 else "disabled")
        self.btn_prev.config(state="normal" if self.current_index > 0 else "disabled")
        self.btn_next.config(state="normal" if self.current_index < total - 1 else "disabled")
        self.btn_last.config(state="normal" if self.current_index < total - 1 else "disabled")

        row = self.spreadsheet.rows[self.current_index]
        preview_pairs: list[str] = []
        for col in self.spreadsheet.headers[:3]:
            val = row.get(col, "")
            if len(val) > 24:
                val = val[:21] + "..."
            preview_pairs.append(f"{col}: {val}")
        summary_str = "  |  ".join(preview_pairs)
        if not self.var_live_preview.get():
            summary_str = f"[Placeholder Mode]  {summary_str}"
        self.lbl_row_summary.config(text=summary_str)

    def _emit_change(self) -> None:
        if self.on_record_changed:
            self.on_record_changed(self.get_active_preview_record(), self.current_index)
