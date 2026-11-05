"""Non-destructive PDF and image template renderer using PyMuPDF (fitz)."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional
import warnings

from PIL import Image

with warnings.catch_warnings():
    warnings.simplefilter("ignore", FutureWarning)
    import fitz

from src.core.qr_generator import generate_qr_png_bytes
from src.core.text_fitter import (
    calculate_fitted_font_size,
    hex_to_rgb_float,
    resolve_pdf_font_name,
)
from src.models.field_node import FieldNode, FieldType, TextAlignment


_SUPPORTED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}


def open_template_as_pdf_bytes(template_path: str) -> bytes:
    """Opens a .pdf or image (.png, .jpg, .jpeg) file and returns normalized PDF bytes."""
    path = Path(template_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Template file not found: {template_path}")

    ext = path.suffix.lower()
    if ext == ".pdf":
        doc = fitz.open(str(path))
        try:
            if doc.page_count == 0:
                raise ValueError(f"PDF template '{path.name}' has zero pages.")
            return doc.tobytes()
        finally:
            doc.close()

    if ext in _SUPPORTED_IMAGE_EXTS:
        with Image.open(path) as img:
            rgb_img = img.convert("RGB")
            width, height = rgb_img.size
            img_buf = io.BytesIO()
            rgb_img.save(img_buf, format="PNG")
            img_bytes = img_buf.getvalue()

        doc = fitz.open()
        try:
            page = doc.new_page(width=float(width), height=float(height))
            rect = fitz.Rect(0.0, 0.0, float(width), float(height))
            page.insert_image(rect, stream=img_bytes, keep_proportion=True)
            return doc.tobytes()
        finally:
            doc.close()

    raise ValueError(
        f"Unsupported template format '{ext}'. Supported formats: .pdf, .png, .jpg, .jpeg"
    )


def _resolve_field_value(
    field: FieldNode,
    record: Optional[dict[str, str]],
    use_placeholder_when_no_record: bool = False,
) -> str:
    """Resolves the string value or file path for a FieldNode from a record or static fallback."""
    if record is not None:
        mapped_val = ""
        if field.mapped_column and field.mapped_column in record:
            mapped_val = str(record[field.mapped_column]).strip()
        elif field.mapped_column:
            col_lower = field.mapped_column.lower()
            for k, v in record.items():
                if k.lower() == col_lower:
                    mapped_val = str(v).strip()
                    break

        if field.field_type == FieldType.TEXT:
            if mapped_val and field.static_value:
                return f"{field.static_value}{mapped_val}"
            return mapped_val if mapped_val else field.static_value
        if field.field_type == FieldType.IMAGE:
            return mapped_val if mapped_val else field.static_value
        if field.field_type == FieldType.QR:
            if mapped_val and field.static_value:
                return f"{field.static_value}{mapped_val}"
            return mapped_val if mapped_val else field.static_value

    if use_placeholder_when_no_record:
        if field.field_type == FieldType.TEXT:
            if field.mapped_column:
                prefix = field.static_value or ""
                return f"{prefix}{{{field.mapped_column}}}"
            if field.static_value:
                return field.static_value
            return f"{{{field.label}}}"
        if field.field_type == FieldType.IMAGE:
            return field.static_value
        if field.field_type == FieldType.QR:
            if field.static_value:
                return field.static_value
            if field.mapped_column:
                return f"QR:{field.mapped_column}"
            return f"QR:{field.label}"

    return field.static_value


def _stamp_text_field(page: fitz.Page, field: FieldNode, text_value: str) -> None:
    """Stamps a single text field inside its bounding box with vertical centering and horizontal alignment."""
    if not text_value:
        return

    pdf_font_name = resolve_pdf_font_name(field.font_family, field.bold, field.italic)
    fitted_size = calculate_fitted_font_size(
        text=text_value,
        font_name=pdf_font_name,
        max_font_size=field.font_size,
        min_font_size=field.min_font_size,
        box_width=field.width,
        box_height=field.height,
        auto_shrink=field.auto_shrink,
    )

    try:
        font_obj = fitz.Font(fontname=pdf_font_name)
    except Exception:
        pdf_font_name = "helv"
        font_obj = fitz.Font(fontname="helv")

    text_width = font_obj.text_length(text_value, fontsize=fitted_size)
    rgb = hex_to_rgb_float(field.color_hex)

    padding_x = 2.0
    if field.alignment == TextAlignment.LEFT:
        x_pos = field.x + padding_x
    elif field.alignment == TextAlignment.RIGHT:
        x_pos = max(field.x + padding_x, field.x + field.width - text_width - padding_x)
    else:
        x_pos = field.x + max(0.0, (field.width - text_width) / 2.0)

    # Vertically center baseline in the box
    baseline_y = field.y + (field.height / 2.0) + (fitted_size * 0.34)
    page.insert_text(
        fitz.Point(x_pos, baseline_y),
        text_value,
        fontname=pdf_font_name,
        fontsize=fitted_size,
        color=rgb,
    )


def _stamp_image_field(page: fitz.Page, field: FieldNode, image_path_str: str) -> None:
    """Loads an image from disk and inserts it into the field bounding rectangle preserving aspect ratio."""
    if not image_path_str:
        return
    img_path = Path(image_path_str)
    if not img_path.exists() or not img_path.is_file():
        return

    rect = fitz.Rect(field.x, field.y, field.x + field.width, field.y + field.height)
    with Image.open(img_path) as pil_img:
        rgba = pil_img.convert("RGBA")
        buf = io.BytesIO()
        rgba.save(buf, format="PNG")
        png_bytes = buf.getvalue()

    page.insert_image(rect, stream=png_bytes, keep_proportion=True)


def _stamp_qr_field(page: fitz.Page, field: FieldNode, payload: str) -> None:
    """Generates a QR code for payload and stamps it into the field bounding rectangle."""
    if not payload:
        return
    rect = fitz.Rect(field.x, field.y, field.x + field.width, field.y + field.height)
    qr_bytes = generate_qr_png_bytes(payload=payload, box_size=8, border=1)
    page.insert_image(rect, stream=qr_bytes, keep_proportion=True)


def render_record_to_doc(
    template_pdf_bytes: bytes,
    fields: list[FieldNode],
    record: dict[str, str],
) -> fitz.Document:
    """Clones the template PDF in memory and stamps all fields for the given record.

    Strictly performs zero encryption or permissions locking.
    """
    doc = fitz.open(stream=template_pdf_bytes, filetype="pdf")
    page_count = doc.page_count

    for field in fields:
        target_page_idx = max(0, min(field.page_index, page_count - 1))
        page = doc[target_page_idx]
        value = _resolve_field_value(field, record, use_placeholder_when_no_record=False)

        if field.field_type == FieldType.TEXT:
            _stamp_text_field(page, field, value)
        elif field.field_type == FieldType.IMAGE:
            _stamp_image_field(page, field, value)
        elif field.field_type == FieldType.QR:
            _stamp_qr_field(page, field, value)

    return doc


def render_canvas_preview(
    template_pdf_bytes: bytes,
    fields: list[FieldNode],
    record: Optional[dict[str, str]],
    page_index: int = 0,
    zoom: float = 1.0,
) -> Image.Image:
    """Renders the stamped page (or placeholder tags if record is None) to a PIL.Image for the GUI canvas."""
    doc = fitz.open(stream=template_pdf_bytes, filetype="pdf")
    try:
        safe_page_idx = max(0, min(int(page_index), doc.page_count - 1))
        page = doc[safe_page_idx]

        for field in fields:
            if field.page_index != safe_page_idx:
                continue
            value = _resolve_field_value(
                field,
                record,
                use_placeholder_when_no_record=(record is None),
            )
            if field.field_type == FieldType.TEXT:
                _stamp_text_field(page, field, value)
            elif field.field_type == FieldType.IMAGE:
                _stamp_image_field(page, field, value)
            elif field.field_type == FieldType.QR:
                _stamp_qr_field(page, field, value)

        safe_zoom = max(0.2, min(float(zoom), 4.0))
        mat = fitz.Matrix(safe_zoom, safe_zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        return img
    finally:
        doc.close()
