"""Unit tests for Excel/CSV spreadsheet loading and dynamic filename sanitization."""

from __future__ import annotations

from pathlib import Path
import pytest

from src.core.data_loader import SpreadsheetLoadError, load_spreadsheet
from src.utils.filename_parser import format_dynamic_filename, sanitize_filename_segment


def test_load_xlsx_gradebook_normalizes_types(sample_xlsx_gradebook: Path) -> None:
    """Verifies .xlsx loading strips .0 from integer floats and preserves decimals."""
    data = load_spreadsheet(str(sample_xlsx_gradebook))
    assert data.headers == ["Roll_No", "Student_Name", "Grade", "Total_Marks", "Verification_ID"]
    assert len(data.rows) == 3
    assert data.rows[0]["Roll_No"] == "101"
    assert data.rows[0]["Student_Name"] == "Aarav Sharma"
    assert data.rows[0]["Total_Marks"] == "98"
    assert data.rows[1]["Total_Marks"] == "92.5"


def test_load_csv_gradebook_handles_bom_and_whitespace(sample_csv_gradebook: Path) -> None:
    """Verifies .csv loading handles UTF-8-SIG BOM and extracts all rows."""
    data = load_spreadsheet(str(sample_csv_gradebook))
    assert data.headers == ["Roll_No", "Student_Name", "Grade", "Total_Marks", "Verification_ID"]
    assert len(data.rows) == 3
    assert data.rows[0]["Roll_No"] == "201"
    assert data.rows[1]["Student_Name"] == "Meera Krishnan"


def test_load_empty_csv_raises_descriptive_error(tmp_path: Path) -> None:
    """Verifies empty or header-only CSV files raise SpreadsheetLoadError."""
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("", encoding="utf-8")
    with pytest.raises(SpreadsheetLoadError):
        load_spreadsheet(str(empty_csv))

    header_only = tmp_path / "headers_only.csv"
    header_only.write_text("Roll_No,Student_Name\n", encoding="utf-8")
    with pytest.raises(SpreadsheetLoadError):
        load_spreadsheet(str(header_only))


def test_format_dynamic_filename_replaces_columns_and_scrubs_illegal_chars(tmp_path: Path) -> None:
    """Verifies dynamic placeholder substitution, illegal character scrubbing, and collision resolution."""
    record = {
        "Roll_No": "203",
        "Student_Name": 'Kabir: Singh/Gill*?<>|"',
        "Grade": "A+",
    }
    filename = format_dynamic_filename("{Roll_No}_{Student_Name}", record, row_index=2)
    assert filename.endswith(".pdf")
    for ch in '<>:"/\\|?*':
        assert ch not in filename
    assert filename.startswith("203_Kabir_")

    # Verify {Index} and collision avoidance in target_dir
    first_file = tmp_path / "001_203.pdf"
    first_file.write_bytes(b"%PDF-1.4")
    collided = format_dynamic_filename("{Index}_{Roll_No}", record, row_index=0, target_dir=tmp_path)
    assert collided == "001_203_1.pdf"


def test_sanitize_filename_segment_trims_dots_and_spaces() -> None:
    """Verifies trailing dots and spaces are stripped for Windows safety."""
    assert sanitize_filename_segment("  Report Card... ") == "Report Card"


def test_corrupt_xlsx_raises_spreadsheet_load_error(tmp_path: Path) -> None:
    """Regression test (DEF-04): corrupt non-ZIP .xlsx files raise SpreadsheetLoadError."""
    bad_xlsx = tmp_path / "corrupt.xlsx"
    bad_xlsx.write_bytes(b"PK\x03\x04corrupted_payload_bytes")
    with pytest.raises(SpreadsheetLoadError, match="Invalid or corrupted Excel"):
        load_spreadsheet(str(bad_xlsx))


def test_format_dynamic_filename_caps_excessive_length_and_reserved_names() -> None:
    """Regression test (DEF-05): filenames > 180 chars are capped and Windows reserved names are guarded."""
    huge_record = {"Name": "A" * 350}
    fn = format_dynamic_filename("{Index}_{Name}", huge_record, row_index=0)
    assert len(fn) <= 185
    assert fn.endswith(".pdf")

    reserved_fn = format_dynamic_filename("CON", {}, row_index=0)
    assert reserved_fn == "001_Document.pdf"


def test_format_dynamic_filename_tokens_and_case_insensitivity(tmp_path: Path) -> None:
    """Verifies {Column0}, {First_Column}, case-insensitivity, and sequential collisions."""
    rec = {"Student_ID": "S-999", "score": "100"}

    # Test Column0 / First_Column
    fn1 = format_dynamic_filename("{Index}_{Column0}", rec, row_index=4)
    assert fn1 == "005_S-999.pdf"

    fn2 = format_dynamic_filename("{First_Column}_{SCORE}", rec, row_index=0)
    assert fn2 == "S-999_100.pdf"

    # Test sequential collision resolution (_1, _2)
    (tmp_path / "Cert_1.pdf").write_bytes(b"%PDF")
    (tmp_path / "Cert_1_1.pdf").write_bytes(b"%PDF")
    fn_collision = format_dynamic_filename("Cert_1", rec, row_index=0, target_dir=tmp_path)
    assert fn_collision == "Cert_1_2.pdf"



