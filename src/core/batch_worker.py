"""Multi-threaded batch PDF and merged master PDF generation worker."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import threading
import time
from typing import Callable, Optional
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore", FutureWarning)
    import fitz

from src.core.data_loader import SpreadsheetData
from src.core.template_renderer import open_template_as_pdf_bytes, render_record_to_doc
from src.models.batch_result import BatchSummary, RowStatus, RowTaskResult
from src.models.field_node import FieldNode
from src.models.project_state import ExportMode, OutputSettings
from src.utils.config import get_max_worker_threads
from src.utils.filename_parser import format_dynamic_filename, sanitize_filename_segment
from src.utils.logger import get_logger

logger = get_logger("batch_worker")


class TemplateBatchWorker:
    """Executes multithreaded batch PDF rendering and optional master PDF merging."""

    def __init__(
        self,
        template_path: str,
        spreadsheet: SpreadsheetData,
        fields: list[FieldNode],
        output_settings: OutputSettings,
        max_workers: Optional[int] = None,
        on_row_processed: Optional[Callable[[RowTaskResult, int, int], None]] = None,
        on_batch_finished: Optional[Callable[[BatchSummary], None]] = None,
    ) -> None:
        self.template_path = template_path
        self.spreadsheet = spreadsheet
        self.fields = list(fields)
        self.output_settings = output_settings
        self.max_workers = max_workers or get_max_worker_threads()
        self.on_row_processed = on_row_processed
        self.on_batch_finished = on_batch_finished
        self.cancel_event = threading.Event()
        self._filename_lock = threading.Lock()
        self._reserved_filenames: set[str] = set()

    def cancel(self) -> None:
        """Signals the batch worker to stop processing remaining rows."""
        self.cancel_event.set()
        logger.info("Batch cancellation requested.")

    def _allocate_unique_filepath(
        self,
        out_dir: Path,
        pattern: str,
        record: dict[str, str],
        row_index: int,
    ) -> Path:
        """Thread-safely resolves a unique output filename within out_dir."""
        with self._filename_lock:
            base_name = format_dynamic_filename(pattern, record, row_index, target_dir=out_dir)
            stem = base_name[:-4] if base_name.lower().endswith(".pdf") else base_name
            candidate_name = f"{stem}.pdf"
            counter = 1
            while (
                candidate_name.lower() in self._reserved_filenames
                or (out_dir / candidate_name).exists()
            ):
                candidate_name = f"{stem}_{counter}.pdf"
                counter += 1
            self._reserved_filenames.add(candidate_name.lower())
            return out_dir / candidate_name

    def _process_single_row(
        self,
        row_index: int,
        record: dict[str, str],
        template_pdf_bytes: bytes,
        out_dir: Path,
        write_individual: bool,
        need_merged_bytes: bool,
    ) -> tuple[RowTaskResult, Optional[bytes]]:
        """Renders a single spreadsheet row into PDF bytes and optionally writes an individual PDF."""
        t0 = time.perf_counter()
        if self.cancel_event.is_set():
            return (
                RowTaskResult(
                    row_index=row_index,
                    output_file=None,
                    status=RowStatus.FAILED,
                    error_message="Cancelled by user",
                    duration_ms=0.0,
                ),
                None,
            )

        try:
            doc = render_record_to_doc(
                template_pdf_bytes=template_pdf_bytes,
                fields=self.fields,
                record=record,
            )
            try:
                pdf_bytes = doc.tobytes(garbage=2, deflate=True)
            finally:
                doc.close()

            saved_path_str: Optional[str] = None
            if write_individual:
                target_path = self._allocate_unique_filepath(
                    out_dir=out_dir,
                    pattern=self.output_settings.filename_pattern,
                    record=record,
                    row_index=row_index,
                )
                target_path.write_bytes(pdf_bytes)
                saved_path_str = str(target_path)

            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            result = RowTaskResult(
                row_index=row_index,
                output_file=saved_path_str,
                status=RowStatus.SUCCESS,
                error_message=None,
                duration_ms=elapsed_ms,
            )
            return result, (pdf_bytes if need_merged_bytes else None)
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            logger.error("Failed processing row %d: %s", row_index + 1, exc)
            return (
                RowTaskResult(
                    row_index=row_index,
                    output_file=None,
                    status=RowStatus.FAILED,
                    error_message=str(exc),
                    duration_ms=elapsed_ms,
                ),
                None,
            )

    def run(self) -> BatchSummary:
        """Executes the batch job synchronously (call from a worker thread or CLI/tests)."""
        out_dir = Path(self.output_settings.output_dir or "output")
        out_dir.mkdir(parents=True, exist_ok=True)

        template_pdf_bytes = open_template_as_pdf_bytes(self.template_path)
        total_rows = len(self.spreadsheet.rows)

        mode = self.output_settings.export_mode
        write_individual = mode in (ExportMode.INDIVIDUAL_PDFS, ExportMode.BOTH)
        write_merged = mode in (ExportMode.MERGED_MASTER_PDF, ExportMode.BOTH)

        results_by_index: dict[int, RowTaskResult] = {}
        pdf_bytes_by_index: dict[int, bytes] = {}
        completed_count = 0

        logger.info(
            "Starting batch export of %d rows (mode=%s, workers=%d)",
            total_rows,
            mode.value,
            self.max_workers,
        )

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_idx = {
                executor.submit(
                    self._process_single_row,
                    idx,
                    row,
                    template_pdf_bytes,
                    out_dir,
                    write_individual,
                    write_merged,
                ): idx
                for idx, row in enumerate(self.spreadsheet.rows)
            }

            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                row_result, rendered_bytes = future.result()
                results_by_index[idx] = row_result
                if rendered_bytes is not None:
                    pdf_bytes_by_index[idx] = rendered_bytes

                completed_count += 1
                if self.on_row_processed is not None:
                    try:
                        self.on_row_processed(row_result, completed_count, total_rows)
                    except Exception as cb_exc:
                        logger.warning("Progress callback error: %s", cb_exc)

        ordered_results = [results_by_index[i] for i in sorted(results_by_index.keys())]
        succeeded = sum(1 for r in ordered_results if r.status == RowStatus.SUCCESS)
        failed = sum(1 for r in ordered_results if r.status != RowStatus.SUCCESS)

        merged_pdf_path: Optional[str] = None
        if write_merged and succeeded > 0 and not self.cancel_event.is_set():
            merged_pdf_path = self._write_merged_master_pdf(out_dir, pdf_bytes_by_index)

        summary = BatchSummary(
            total_rows=total_rows,
            succeeded=succeeded,
            failed=failed,
            merged_pdf_path=merged_pdf_path,
            results=ordered_results,
        )

        if self.on_batch_finished is not None:
            try:
                self.on_batch_finished(summary)
            except Exception as cb_exc:
                logger.warning("Batch finished callback error: %s", cb_exc)

        return summary

    def _write_merged_master_pdf(
        self,
        out_dir: Path,
        pdf_bytes_by_index: dict[int, bytes],
    ) -> str:
        """Assembles all rendered row pages in order into a single multi-page master PDF inside out_dir."""
        raw_merged = Path(self.output_settings.merged_filename or "Master_Batch_Output.pdf").name
        merged_name = sanitize_filename_segment(raw_merged) or "Master_Batch_Output.pdf"
        if not merged_name.lower().endswith(".pdf"):
            merged_name = f"{merged_name}.pdf"
        if merged_name[:-4].strip(" .") == "":
            merged_name = "Master_Batch_Output.pdf"
        merged_target = (out_dir / merged_name).resolve()
        if merged_target.parent != out_dir.resolve():
            merged_target = out_dir.resolve() / "Master_Batch_Output.pdf"

        master_doc = fitz.open()
        try:
            for i in sorted(pdf_bytes_by_index.keys()):
                single_doc = fitz.open(stream=pdf_bytes_by_index[i], filetype="pdf")
                try:
                    master_doc.insert_pdf(single_doc)
                finally:
                    single_doc.close()
            master_doc.save(str(merged_target), garbage=3, deflate=True)
            logger.info("Saved merged master PDF at: %s", merged_target)
            return str(merged_target)
        finally:
            master_doc.close()

