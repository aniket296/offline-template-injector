"""Core processing engines for Offline Template Injector."""

from src.core.batch_worker import TemplateBatchWorker
from src.core.data_loader import SpreadsheetData, SpreadsheetLoadError, load_spreadsheet
from src.core.project_io import PresetIOError, load_project_preset, save_project_preset
from src.core.qr_generator import generate_qr_png_bytes
from src.core.template_renderer import (
    open_template_as_pdf_bytes,
    render_canvas_preview,
    render_record_to_doc,
)
from src.core.text_fitter import (
    calculate_fitted_font_size,
    hex_to_rgb_float,
    resolve_pdf_font_name,
)

__all__ = [
    "SpreadsheetData",
    "SpreadsheetLoadError",
    "load_spreadsheet",
    "calculate_fitted_font_size",
    "hex_to_rgb_float",
    "resolve_pdf_font_name",
    "generate_qr_png_bytes",
    "open_template_as_pdf_bytes",
    "render_record_to_doc",
    "render_canvas_preview",
    "PresetIOError",
    "save_project_preset",
    "load_project_preset",
    "TemplateBatchWorker",
]
