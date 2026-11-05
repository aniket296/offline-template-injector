"""Main Tkinter application controller wiring Toolbar, Canvas, Inspector, Stepper, and Batch Export."""

from __future__ import annotations

import ctypes
from pathlib import Path
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any, Optional
import uuid

from src.core.batch_worker import TemplateBatchWorker
from src.core.data_loader import SpreadsheetData, load_spreadsheet
from src.core.project_io import load_project_preset, save_project_preset
from src.core.template_renderer import open_template_as_pdf_bytes
from src.gui.components.canvas_editor import TemplateCanvasEditor
from src.gui.components.export_panel import BatchExportPanel
from src.gui.components.field_inspector import FieldPropertyInspector
from src.gui.components.record_stepper import LiveRecordStepper
from src.gui.components.toolbar import TopActionToolbar
from src.gui.styles import (
    COLOR_BG_MAIN,
    COLOR_BG_PANEL,
    COLOR_BORDER,
    apply_slate_indigo_theme,
)
from src.models.batch_result import BatchSummary, RowTaskResult
from src.models.field_node import FieldNode, FieldType
from src.models.project_state import TemplateProject
from src.utils.logger import get_logger

logger = get_logger("gui.app")


def enable_windows_high_dpi() -> None:
    """Enables per-monitor High-DPI awareness on Windows."""
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def resolve_asset_path(relative_path: str) -> Path:
    """Resolves asset paths both in local source checkouts and PyInstaller bundles."""
    if hasattr(sys, "_MEIPASS"):
        base_dir = Path(getattr(sys, "_MEIPASS"))
    else:
        base_dir = Path(__file__).resolve().parent.parent.parent
    return base_dir / relative_path


class OfflineTemplateInjectorApp:
    """Top-level desktop application controller and window shell."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Offline Template & Variable Field Injector v1.0.0")
        self.root.geometry("1400x880")
        self.root.minsize(1140, 740)
        self.root.configure(bg=COLOR_BG_MAIN)

        self._load_window_icon()
        self.style = apply_slate_indigo_theme(self.root)

        # Application State
        self.template_path: str = ""
        self.template_pdf_bytes: Optional[bytes] = None
        self.data_source_path: str = ""
        self.spreadsheet: Optional[SpreadsheetData] = None
        self.fields: list[FieldNode] = []

        # Background Batch Worker State
        self._active_worker: Optional[TemplateBatchWorker] = None
        self._worker_thread: Optional[threading.Thread] = None
        self._ui_event_queue: queue.Queue[tuple[str, Any]] = queue.Queue()

        self._build_layout()
        self._poll_ui_events()

    def _load_window_icon(self) -> None:
        """Sets the window icon from assets/app_icon.ico if available."""
        icon_path = resolve_asset_path("assets/app_icon.ico")
        if icon_path.exists():
            try:
                self.root.iconbitmap(default=str(icon_path))
            except Exception as exc:
                logger.debug("Could not load window icon: %s", exc)

    def _build_layout(self) -> None:
        # 1. Top Action Toolbar
        self.toolbar = TopActionToolbar(
            self.root,
            on_load_template=self.action_load_template,
            on_load_data=self.action_load_data,
            on_add_field=self.action_add_field,
            on_delete_field=self.action_delete_selected_field,
            on_save_preset=self.action_save_preset,
            on_load_preset=self.action_load_preset,
        )
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # 2. Main Split Workspace
        self.main_workspace = ttk.Frame(self.root, style="TFrame")
        self.main_workspace.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Right Sidebar (Field Property Inspector + Batch Export Panel)
        right_sidebar_outer = tk.Frame(
            self.main_workspace, bg=COLOR_BG_PANEL, width=390
        )
        right_sidebar_outer.pack(side=tk.RIGHT, fill=tk.Y)
        right_sidebar_outer.pack_propagate(False)

        tk.Frame(self.main_workspace, bg=COLOR_BORDER, width=1).pack(
            side=tk.RIGHT, fill=tk.Y
        )

        self.inspector = FieldPropertyInspector(
            right_sidebar_outer,
            on_property_changed=self._on_inspector_property_changed,
        )
        self.inspector.pack(side=tk.TOP, fill=tk.X)

        self.export_panel = BatchExportPanel(
            right_sidebar_outer,
            on_start_batch=self.action_start_batch_export,
            on_cancel_batch=self.action_cancel_batch_export,
        )
        self.export_panel.pack(side=tk.BOTTOM, fill=tk.X)

        # Left/Center Pane (Interactive Template Canvas + Live Record Stepper)
        left_pane = ttk.Frame(self.main_workspace, style="TFrame")
        left_pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.record_stepper = LiveRecordStepper(
            left_pane,
            on_record_changed=self._on_stepper_record_changed,
        )
        self.record_stepper.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas_editor = TemplateCanvasEditor(
            left_pane,
            on_field_selected=self._on_canvas_field_selected,
            on_field_modified=self._on_canvas_field_modified,
            on_field_deleted=lambda _f: self.action_delete_selected_field(),
        )
        self.canvas_editor.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # --- Toolbar Actions ---

    def action_load_template(self, file_path: Optional[str] = None) -> None:
        """Opens a file dialog to load a PDF or Image template into the canvas."""
        chosen = file_path or filedialog.askopenfilename(
            title="Select Certificate or Report Card Template",
            filetypes=[
                ("Templates (PDF & Images)", "*.pdf *.png *.jpg *.jpeg *.bmp"),
                ("PDF Documents", "*.pdf"),
                ("Image Files", "*.png *.jpg *.jpeg *.bmp"),
                ("All Files", "*.*"),
            ],
        )
        if not chosen:
            return

        try:
            pdf_bytes = open_template_as_pdf_bytes(chosen)
            self.template_path = chosen
            self.template_pdf_bytes = pdf_bytes
            self.canvas_editor.set_template_bytes(pdf_bytes)
            logger.info("Loaded template: %s", chosen)
        except Exception as exc:
            logger.error("Failed to load template: %s", exc)
            messagebox.showerror("Template Load Error", str(exc), parent=self.root)

    def action_load_data(self, file_path: Optional[str] = None) -> None:
        """Opens a file dialog to load an Excel (.xlsx) or CSV (.csv) student data file."""
        chosen = file_path or filedialog.askopenfilename(
            title="Select Student Spreadsheet (.xlsx or .csv)",
            filetypes=[
                ("Spreadsheets (.xlsx, .csv)", "*.xlsx *.csv"),
                ("Excel Workbook", "*.xlsx"),
                ("CSV File", "*.csv"),
                ("All Files", "*.*"),
            ],
        )
        if not chosen:
            return

        try:
            data = load_spreadsheet(chosen)
            self.data_source_path = chosen
            self.spreadsheet = data
            self.inspector.set_available_columns(data.headers)
            self.export_panel.set_column_chips(data.headers)
            self.record_stepper.set_spreadsheet(data)
            self.export_panel.update_progress(0, len(data.rows), "Ready")
            logger.info(
                "Loaded data source '%s' (%d rows, %d columns)",
                chosen,
                len(data.rows),
                len(data.headers),
            )
        except Exception as exc:
            logger.error("Failed to load spreadsheet: %s", exc)
            messagebox.showerror("Spreadsheet Load Error", str(exc), parent=self.root)

    def action_add_field(self, field_type: FieldType) -> None:
        """Adds a new variable field box onto the template canvas and selects it."""
        idx = len(self.fields) + 1
        short_id = f"fld_{uuid.uuid4().hex[:6]}"
        offset = (idx - 1) * 18 % 140

        default_col = ""
        if self.spreadsheet and self.spreadsheet.headers:
            default_col = self.spreadsheet.headers[
                min(idx - 1, len(self.spreadsheet.headers) - 1)
            ]

        if field_type == FieldType.TEXT:
            node = FieldNode(
                field_id=short_id,
                field_type=FieldType.TEXT,
                label=default_col or f"Text Field {idx}",
                mapped_column=default_col,
                x=120.0 + offset,
                y=160.0 + offset,
                width=200.0,
                height=36.0,
            )
        elif field_type == FieldType.IMAGE:
            node = FieldNode(
                field_id=short_id,
                field_type=FieldType.IMAGE,
                label=f"Signature / Image {idx}",
                mapped_column="",
                x=140.0 + offset,
                y=260.0 + offset,
                width=150.0,
                height=55.0,
            )
        else:
            node = FieldNode(
                field_id=short_id,
                field_type=FieldType.QR,
                label=f"QR Code {idx}",
                mapped_column=default_col,
                x=160.0 + offset,
                y=320.0 + offset,
                width=85.0,
                height=85.0,
            )

        self.fields.append(node)
        self.canvas_editor.set_fields(self.fields)
        self.canvas_editor.select_field(node.field_id, notify=True)
        logger.info("Added %s field '%s'", field_type.value, node.label)

    def action_delete_selected_field(self) -> None:
        """Deletes the currently selected field from the template canvas."""
        selected = self.canvas_editor.get_selected_field()
        if selected is None:
            return
        self.fields = [f for f in self.fields if f.field_id != selected.field_id]
        self.canvas_editor.set_fields(self.fields)
        new_sel = self.fields[-1] if self.fields else None
        self.canvas_editor.select_field(
            new_sel.field_id if new_sel else None, notify=True
        )
        logger.info("Deleted field '%s'", selected.label)

    def action_save_preset(self) -> None:
        """Saves the current layout and settings to a .otvi JSON preset file."""
        file_path = filedialog.asksaveasfilename(
            title="Save Template Layout Preset (.otvi)",
            defaultextension=".otvi",
            filetypes=[("OTVI Layout Preset", "*.otvi"), ("JSON Files", "*.json")],
        )
        if not file_path:
            return

        project = TemplateProject(
            template_path=self.template_path,
            data_source_path=self.data_source_path,
            fields=self.fields,
            output_settings=self.export_panel.get_output_settings(),
        )
        try:
            save_project_preset(project, file_path)
            logger.info("Saved layout preset to: %s", file_path)
            messagebox.showinfo(
                "Preset Saved",
                f"Layout preset saved successfully to:\n{file_path}",
                parent=self.root,
            )
        except Exception as exc:
            logger.error("Failed to save preset: %s", exc)
            messagebox.showerror("Save Preset Error", str(exc), parent=self.root)

    def action_load_preset(self) -> None:
        """Loads a .otvi layout preset file and restores template, data, and fields."""
        file_path = filedialog.askopenfilename(
            title="Load Template Layout Preset (.otvi)",
            filetypes=[("OTVI Layout Preset", "*.otvi"), ("JSON Files", "*.json")],
        )
        if not file_path:
            return

        try:
            project = load_project_preset(file_path)
            if project.template_path and Path(project.template_path).exists():
                self.action_load_template(project.template_path)
            if project.data_source_path and Path(project.data_source_path).exists():
                self.action_load_data(project.data_source_path)

            self.fields = list(project.fields)
            self.export_panel.load_output_settings(project.output_settings)
            self.canvas_editor.set_fields(self.fields)
            first_id = self.fields[0].field_id if self.fields else None
            self.canvas_editor.select_field(first_id, notify=True)
            logger.info("Loaded layout preset from: %s", file_path)
        except Exception as exc:
            logger.error("Failed to load preset: %s", exc)
            messagebox.showerror("Load Preset Error", str(exc), parent=self.root)

    # --- Synchronization Callbacks ---

    def _on_canvas_field_selected(self, field: Optional[FieldNode]) -> None:
        self.inspector.load_field(field)

    def _on_canvas_field_modified(self, field: FieldNode) -> None:
        self.inspector.sync_geometry_from_canvas(field)

    def _on_inspector_property_changed(self, _field: FieldNode) -> None:
        self.canvas_editor.refresh_canvas()

    def _on_stepper_record_changed(
        self, record: Optional[dict[str, str]], _index: int
    ) -> None:
        self.canvas_editor.set_preview_record(record)

    # --- Multithreaded Batch Export ---

    def action_start_batch_export(self) -> None:
        """Validates inputs and starts TemplateBatchWorker on a background daemon thread."""
        if not self.template_path or self.template_pdf_bytes is None:
            messagebox.showwarning(
                "Missing Template",
                "Please load a PDF or Image template first.",
                parent=self.root,
            )
            return

        if self.spreadsheet is None or not self.spreadsheet.rows:
            messagebox.showwarning(
                "Missing Student Data",
                "Please load an Excel (.xlsx) or CSV (.csv) data file first.",
                parent=self.root,
            )
            return

        if not self.fields:
            messagebox.showwarning(
                "No Fields Placed",
                "Please add at least one variable field onto the template before exporting.",
                parent=self.root,
            )
            return

        settings = self.export_panel.get_output_settings()
        self.export_panel.set_running_state(True)
        self.export_panel.update_progress(0, len(self.spreadsheet.rows), "Running...")

        def _on_row(res: RowTaskResult, done: int, total: int) -> None:
            self._ui_event_queue.put(("row_progress", (res, done, total)))

        def _on_done(summary: BatchSummary) -> None:
            self._ui_event_queue.put(("batch_done", summary))

        self._active_worker = TemplateBatchWorker(
            template_path=self.template_path,
            spreadsheet=self.spreadsheet,
            fields=self.fields,
            output_settings=settings,
            on_row_processed=_on_row,
            on_batch_finished=_on_done,
        )

        self._worker_thread = threading.Thread(
            target=self._active_worker.run,
            name="BatchExportWorkerThread",
            daemon=True,
        )
        self._worker_thread.start()

    def action_cancel_batch_export(self) -> None:
        """Requests cancellation of the running batch worker."""
        if self._active_worker is not None:
            self._active_worker.cancel()

    def _poll_ui_events(self) -> None:
        """Polls background worker progress events on the main Tkinter loop without freezing."""
        try:
            while True:
                event_type, payload = self._ui_event_queue.get_nowait()
                if event_type == "row_progress":
                    _res, done, total = payload
                    self.export_panel.update_progress(done, total, "Generating...")
                elif event_type == "batch_done":
                    summary: BatchSummary = payload
                    self.export_panel.set_running_state(False)
                    status_label = "Completed" if summary.failed == 0 else f"{summary.failed} Failed"
                    self.export_panel.update_progress(
                        summary.succeeded, summary.total_rows, status_label
                    )
                    self._show_batch_summary_dialog(summary)
        except queue.Empty:
            pass

        self.root.after(60, self._poll_ui_events)

    def _show_batch_summary_dialog(self, summary: BatchSummary) -> None:
        out_dir = self.export_panel.get_output_settings().output_dir
        lines = [
            f"Total Records Processed: {summary.total_rows}",
            f"Succeeded: {summary.succeeded}",
            f"Failed: {summary.failed}",
            f"\nOutput Folder:\n{out_dir}",
        ]
        if summary.merged_pdf_path:
            lines.append(f"\nMerged Master PDF:\n{summary.merged_pdf_path}")
        messagebox.showinfo(
            "Batch Export Complete", "\n".join(lines), parent=self.root
        )
