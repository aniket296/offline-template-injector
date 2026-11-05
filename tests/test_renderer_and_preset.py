"""Unit tests for PDF/Image template rendering, .otvi preset IO, and batch/merged PDF export."""

from __future__ import annotations

from pathlib import Path
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore", FutureWarning)
    import fitz

from src.core.batch_worker import TemplateBatchWorker
from src.core.data_loader import load_spreadsheet
from src.core.project_io import load_project_preset, save_project_preset
from src.core.template_renderer import (
    open_template_as_pdf_bytes,
    render_canvas_preview,
    render_record_to_doc,
)
from src.models.field_node import FieldNode, FieldType, TextAlignment
from src.models.project_state import ExportMode, OutputSettings, TemplateProject


def test_stamp_text_signature_and_qr_onto_pdf_template(
    sample_pdf_template: Path,
    sample_signature_png: Path,
) -> None:
    """Verifies Text, Image, and QR fields stamp cleanly and text is extractable."""
    pdf_bytes = open_template_as_pdf_bytes(str(sample_pdf_template))
    fields = [
        FieldNode(
            field_id="fld_name",
            field_type=FieldType.TEXT,
            label="Student Name",
            mapped_column="Student_Name",
            x=120.0,
            y=220.0,
            width=350.0,
            height=40.0,
            font_family="helv",
            font_size=18,
            bold=True,
            alignment=TextAlignment.CENTER,
        ),
        FieldNode(
            field_id="fld_grade",
            field_type=FieldType.TEXT,
            label="Grade",
            mapped_column="Grade",
            static_value="Grade: ",
            x=200.0,
            y=300.0,
            width=180.0,
            height=32.0,
            alignment=TextAlignment.LEFT,
        ),
        FieldNode(
            field_id="fld_sig",
            field_type=FieldType.IMAGE,
            label="Principal Signature",
            mapped_column="",
            static_value=str(sample_signature_png),
            x=360.0,
            y=640.0,
            width=150.0,
            height=55.0,
        ),
        FieldNode(
            field_id="fld_qr",
            field_type=FieldType.QR,
            label="Verification QR",
            mapped_column="Verification_ID",
            x=80.0,
            y=620.0,
            width=90.0,
            height=90.0,
        ),
    ]
    record = {
        "Roll_No": "101",
        "Student_Name": "Aarav Sharma",
        "Grade": "A+",
        "Verification_ID": "VER-2026-101",
    }

    doc = render_record_to_doc(pdf_bytes, fields, record)
    try:
        assert not doc.is_encrypted
        extracted_text = doc[0].get_text()
        assert "Aarav Sharma" in extracted_text
        assert "Grade: A+" in extracted_text
        images_on_page = doc[0].get_images()
        assert len(images_on_page) >= 2  # Signature + QR code
    finally:
        doc.close()

    preview_img = render_canvas_preview(pdf_bytes, fields, record, page_index=0, zoom=1.0)
    assert preview_img.size == (595, 842)


def test_open_image_template_converts_to_pdf_bytes(sample_image_template: Path) -> None:
    """Verifies PNG template files are converted into single-page PDF documents matching dimensions."""
    pdf_bytes = open_template_as_pdf_bytes(str(sample_image_template))
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        assert doc.page_count == 1
        assert doc[0].rect.width == 800.0
        assert doc[0].rect.height == 600.0
    finally:
        doc.close()


def test_otvi_preset_round_trip_serialization(tmp_path: Path) -> None:
    """Verifies saving and loading a .otvi preset preserves all fields and output settings."""
    fields = [
        FieldNode(
            field_id="f_1",
            field_type=FieldType.TEXT,
            label="Roll Number",
            mapped_column="Roll_No",
            x=75.5,
            y=140.25,
            width=120.0,
            height=28.0,
            font_family="cour",
            font_size=12,
            min_font_size=7,
            auto_shrink=True,
            bold=True,
            italic=False,
            color_hex="#4F46E5",
            alignment=TextAlignment.RIGHT,
        )
    ]
    project = TemplateProject(
        template_path="templates/report_card.pdf",
        data_source_path="data/students.xlsx",
        fields=fields,
        output_settings=OutputSettings(
            output_dir="exports/term1",
            filename_pattern="{Roll_No}_{Student_Name}",
            export_mode=ExportMode.BOTH,
            merged_filename="Term1_All_Students.pdf",
        ),
    )

    preset_file = tmp_path / "report_card_layout.otvi"
    save_project_preset(project, str(preset_file))
    assert preset_file.exists()

    loaded = load_project_preset(str(preset_file))
    assert loaded == project


def test_batch_worker_generates_individual_and_merged_master_pdfs(
    tmp_path: Path,
    sample_pdf_template: Path,
    sample_xlsx_gradebook: Path,
    sample_signature_png: Path,
) -> None:
    """Verifies TemplateBatchWorker creates individual student PDFs and a multi-page merged master PDF."""
    spreadsheet = load_spreadsheet(str(sample_xlsx_gradebook))
    out_dir = tmp_path / "batch_output"

    fields = [
        FieldNode(
            field_id="f_name",
            field_type=FieldType.TEXT,
            label="Student Name",
            mapped_column="Student_Name",
            x=100.0,
            y=250.0,
            width=380.0,
            height=40.0,
        ),
        FieldNode(
            field_id="f_sig",
            field_type=FieldType.IMAGE,
            label="Signature",
            mapped_column="",
            static_value=str(sample_signature_png),
            x=350.0,
            y=600.0,
            width=140.0,
            height=50.0,
        ),
        FieldNode(
            field_id="f_qr",
            field_type=FieldType.QR,
            label="QR",
            mapped_column="Verification_ID",
            x=80.0,
            y=600.0,
            width=80.0,
            height=80.0,
        ),
    ]

    settings = OutputSettings(
        output_dir=str(out_dir),
        filename_pattern="{Roll_No}_{Student_Name}",
        export_mode=ExportMode.BOTH,
        merged_filename="Master_Batch_Output.pdf",
    )

    progress_events: list[tuple[int, int]] = []
    worker = TemplateBatchWorker(
        template_path=str(sample_pdf_template),
        spreadsheet=spreadsheet,
        fields=fields,
        output_settings=settings,
        max_workers=2,
        on_row_processed=lambda res, done, total: progress_events.append((done, total)),
    )

    summary = worker.run()
    assert summary.total_rows == 3
    assert summary.succeeded == 3
    assert summary.failed == 0
    assert len(progress_events) == 3

    for res in summary.results:
        assert res.output_file is not None
        assert Path(res.output_file).exists()

    assert summary.merged_pdf_path is not None
    merged_path = Path(summary.merged_pdf_path)
    assert merged_path.exists()

    merged_doc = fitz.open(str(merged_path))
    try:
        assert merged_doc.page_count == 3
        assert "Aarav Sharma" in merged_doc[0].get_text()
        assert "Diya Patel" in merged_doc[1].get_text()
    finally:
        merged_doc.close()
