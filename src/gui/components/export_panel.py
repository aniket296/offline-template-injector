"""Batch export settings panel with dynamic filename chip builder and progress indicator."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk
from typing import Callable, Optional

from src.gui.styles import (
    COLOR_BG_PANEL,
    COLOR_BORDER,
    COLOR_PRIMARY_HEADER,
    COLOR_TEXT_SECONDARY,
    FONT_BODY_BOLD,
    FONT_SECTION,
    FONT_SMALL,
)
from src.models.project_state import ExportMode, OutputSettings


_EXPORT_MODE_DISPLAY = {
    "Both (Individual + Merged Master PDF)": ExportMode.BOTH,
    "Individual PDFs Only": ExportMode.INDIVIDUAL_PDFS,
    "Single Merged Master PDF Only": ExportMode.MERGED_MASTER_PDF,
}
_EXPORT_MODE_TO_DISPLAY = {v: k for k, v in _EXPORT_MODE_DISPLAY.items()}


class BatchExportPanel(ttk.Frame):
    """Panel for configuring output directory, filename pattern chips, export mode, and batch trigger."""

    def __init__(
        self,
        parent: tk.Misc,
        on_start_batch: Optional[Callable[[], None]] = None,
        on_cancel_batch: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(12, 8))
        self.on_start_batch = on_start_batch
        self.on_cancel_batch = on_cancel_batch

        default_out = str((Path.cwd() / "output").resolve())
        self.var_output_dir = tk.StringVar(value=default_out)
        self.var_filename_pattern = tk.StringVar(value="{Index}_{Column0}")
        self.var_export_mode_display = tk.StringVar(
            value="Both (Individual + Merged Master PDF)"
        )
        self.var_merged_filename = tk.StringVar(value="Master_Batch_Output.pdf")

        self._build_ui()
        self.set_column_chips([])

    def _build_ui(self) -> None:
        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(
            side=tk.TOP, fill=tk.X, pady=(0, 8)
        )

        tk.Label(
            self,
            text="Batch Export & Output Settings",
            bg=COLOR_BG_PANEL,
            fg=COLOR_PRIMARY_HEADER,
            font=FONT_SECTION,
        ).pack(side=tk.TOP, anchor="w", pady=(0, 6))

        # Output Directory Selector
        ttk.Label(self, text="Output Folder:", style="Card.TLabel").pack(
            side=tk.TOP, anchor="w"
        )
        dir_row = tk.Frame(self, bg=COLOR_BG_PANEL)
        dir_row.pack(side=tk.TOP, fill=tk.X, pady=(2, 6))

        self.ent_out_dir = ttk.Entry(dir_row, textvariable=self.var_output_dir)
        self.ent_out_dir.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.btn_browse_dir = ttk.Button(
            dir_row,
            text="Browse Output Folder...",
            command=self._browse_output_dir,
        )
        self.btn_browse_dir.pack(side=tk.LEFT, padx=(5, 0))

        # Dynamic Filename Pattern Input
        ttk.Label(
            self,
            text="Dynamic Filename Pattern (auto-appends .pdf):",
            style="Card.TLabel",
        ).pack(side=tk.TOP, anchor="w")
        self.ent_pattern = ttk.Entry(self, textvariable=self.var_filename_pattern)
        self.ent_pattern.pack(side=tk.TOP, fill=tk.X, pady=(2, 4))

        # Clickable Column Tag Chips
        tk.Label(
            self,
            text="Click a tag chip to insert into filename pattern:",
            bg=COLOR_BG_PANEL,
            fg=COLOR_TEXT_SECONDARY,
            font=FONT_SMALL,
        ).pack(side=tk.TOP, anchor="w")

        self.chips_container = tk.Frame(self, bg=COLOR_BG_PANEL)
        self.chips_container.pack(side=tk.TOP, fill=tk.X, pady=(2, 6))

        # Export Mode Selector
        ttk.Label(self, text="Export Mode:", style="Card.TLabel").pack(
            side=tk.TOP, anchor="w"
        )
        self.cmb_export_mode = ttk.Combobox(
            self,
            textvariable=self.var_export_mode_display,
            state="readonly",
            values=list(_EXPORT_MODE_DISPLAY.keys()),
        )
        self.cmb_export_mode.pack(side=tk.TOP, fill=tk.X, pady=(2, 6))

        # Merged Master Filename
        merged_row = tk.Frame(self, bg=COLOR_BG_PANEL)
        merged_row.pack(side=tk.TOP, fill=tk.X, pady=(0, 8))
        ttk.Label(merged_row, text="Master PDF Name:", style="Card.TLabel").pack(
            side=tk.LEFT
        )
        self.ent_merged_name = ttk.Entry(
            merged_row, textvariable=self.var_merged_filename, width=24
        )
        self.ent_merged_name.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(6, 0))

        # Progress bar & status counter
        prog_frame = tk.Frame(self, bg=COLOR_BG_PANEL)
        prog_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))

        self.lbl_status = tk.Label(
            prog_frame,
            text="Processed 0 / 0 records (Ready)",
            bg=COLOR_BG_PANEL,
            fg=COLOR_PRIMARY_HEADER,
            font=FONT_BODY_BOLD,
        )
        self.lbl_status.pack(side=tk.TOP, anchor="w", pady=(0, 3))

        self.progress_bar = ttk.Progressbar(
            prog_frame,
            orient=tk.HORIZONTAL,
            mode="determinate",
            style="Emerald.Horizontal.TProgressbar",
        )
        self.progress_bar.pack(side=tk.TOP, fill=tk.X)

        # Action Buttons (Generate Batch PDFs / Cancel)
        btn_row = tk.Frame(self, bg=COLOR_BG_PANEL)
        btn_row.pack(side=tk.TOP, fill=tk.X, pady=(4, 0))

        self.btn_generate = ttk.Button(
            btn_row,
            text="Generate Batch PDFs",
            style="Success.TButton",
            command=self._handle_start,
        )
        self.btn_generate.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        self.btn_cancel = ttk.Button(
            btn_row,
            text="Cancel",
            style="Danger.TButton",
            state="disabled",
            command=self._handle_cancel,
        )
        self.btn_cancel.pack(side=tk.RIGHT)

    def set_column_chips(self, columns: list[str]) -> None:
        """Rebuilds clickable {Column_Name} tag chips below the filename pattern box."""
        for child in self.chips_container.winfo_children():
            child.destroy()

        tags = ["Index"] + list(columns[:6])
        for tag in tags:
            btn = ttk.Button(
                self.chips_container,
                text=f"{{{tag}}}",
                style="Chip.TButton",
                command=lambda t=tag: self._insert_chip_tag(t),
            )
            btn.pack(side=tk.LEFT, padx=(0, 4), pady=2)

    def _insert_chip_tag(self, tag_name: str) -> None:
        token = f"{{{tag_name}}}"
        current = self.var_filename_pattern.get().strip()
        if not current:
            self.var_filename_pattern.set(token)
        elif current.endswith("_") or current.endswith("-"):
            self.var_filename_pattern.set(f"{current}{token}")
        else:
            self.var_filename_pattern.set(f"{current}_{token}")

    def _browse_output_dir(self) -> None:
        chosen = filedialog.askdirectory(
            title="Select Batch PDF Output Folder",
            initialdir=self.var_output_dir.get() or str(Path.cwd()),
        )
        if chosen:
            self.var_output_dir.set(chosen)

    def get_output_settings(self) -> OutputSettings:
        """Builds an OutputSettings instance from the current panel inputs."""
        mode = _EXPORT_MODE_DISPLAY.get(
            self.var_export_mode_display.get(), ExportMode.BOTH
        )
        return OutputSettings(
            output_dir=self.var_output_dir.get().strip() or str(Path.cwd() / "output"),
            filename_pattern=self.var_filename_pattern.get().strip() or "{Index}_{Column0}",
            export_mode=mode,
            merged_filename=self.var_merged_filename.get().strip() or "Master_Batch_Output.pdf",
        )

    def load_output_settings(self, settings: OutputSettings) -> None:
        """Updates the UI controls from an OutputSettings object."""
        if settings.output_dir:
            self.var_output_dir.set(settings.output_dir)
        self.var_filename_pattern.set(settings.filename_pattern or "{Index}_{Column0}")
        self.var_export_mode_display.set(
            _EXPORT_MODE_TO_DISPLAY.get(
                settings.export_mode, "Both (Individual + Merged Master PDF)"
            )
        )
        self.var_merged_filename.set(settings.merged_filename or "Master_Batch_Output.pdf")

    def set_running_state(self, is_running: bool) -> None:
        """Toggles button states when a batch job starts or finishes."""
        if is_running:
            self.btn_generate.config(state="disabled")
            self.btn_cancel.config(state="normal")
        else:
            self.btn_generate.config(state="normal")
            self.btn_cancel.config(state="disabled")

    def update_progress(self, completed: int, total: int, status_suffix: str = "") -> None:
        """Updates the progress bar percentage and status counter label."""
        pct = (completed / total * 100.0) if total > 0 else 0.0
        self.progress_bar["value"] = pct
        suffix = f" ({status_suffix})" if status_suffix else ""
        self.lbl_status.config(text=f"Processed {completed} / {total} records{suffix}")

    def _handle_start(self) -> None:
        if self.on_start_batch:
            self.on_start_batch()

    def _handle_cancel(self) -> None:
        if self.on_cancel_batch:
            self.on_cancel_batch()
