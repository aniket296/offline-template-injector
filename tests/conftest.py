"""Pytest fixtures for synthetic PDF templates, Excel/CSV gradebooks, and signature images."""

from __future__ import annotations

from pathlib import Path
import warnings
import openpyxl
from PIL import Image, ImageDraw
import pytest

with warnings.catch_warnings():
    warnings.simplefilter("ignore", FutureWarning)
    import fitz


@pytest.fixture()
def sample_pdf_template(tmp_path: Path) -> Path:
    """Generates a synthetic A4 report card / certificate PDF template."""
    pdf_path = tmp_path / "certificate_template.pdf"
    doc = fitz.open()
    try:
        page = doc.new_page(width=595.0, height=842.0)  # A4 portrait in PDF points
        page.draw_rect(fitz.Rect(24, 24, 571, 818), color=(0.12, 0.11, 0.29), width=2.5)
        page.insert_text(
            fitz.Point(160, 80),
            "CERTIFICATE OF ACADEMIC EXCELLENCE",
            fontname="hebo",
            fontsize=14,
            color=(0.12, 0.11, 0.29),
        )
        doc.save(str(pdf_path))
    finally:
        doc.close()
    return pdf_path


@pytest.fixture()
def sample_image_template(tmp_path: Path) -> Path:
    """Generates a synthetic PNG certificate template."""
    img_path = tmp_path / "certificate_template.png"
    img = Image.new("RGB", (800, 600), (248, 250, 252))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 780, 580], outline=(30, 27, 75), width=4)
    img.save(img_path, format="PNG")
    return img_path


@pytest.fixture()
def sample_signature_png(tmp_path: Path) -> Path:
    """Generates a transparent PNG signature image for stamping tests."""
    sig_path = tmp_path / "principal_signature.png"
    img = Image.new("RGBA", (220, 70), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.line([(15, 50), (80, 20), (140, 48), (205, 18)], fill=(30, 58, 138, 255), width=4)
    img.save(sig_path, format="PNG")
    return sig_path


@pytest.fixture()
def sample_xlsx_gradebook(tmp_path: Path) -> Path:
    """Generates a multi-row .xlsx student gradebook with pre-evaluated values."""
    xlsx_path = tmp_path / "gradebook.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Students"
    ws.append(["Roll_No", "Student_Name", "Grade", "Total_Marks", "Verification_ID"])
    ws.append([101.0, "Aarav Sharma", "A+", 98.0, "VER-2026-101"])
    ws.append([102.0, "Diya Patel", "A", 92.5, "VER-2026-102"])
    ws.append([103.0, "Alexandria Maximiliana Montgomery-Featherstonehaugh", "A+", 99.0, "VER-2026-103"])
    wb.save(str(xlsx_path))
    wb.close()
    return xlsx_path


@pytest.fixture()
def sample_csv_gradebook(tmp_path: Path) -> Path:
    """Generates a UTF-8-SIG .csv student gradebook."""
    csv_path = tmp_path / "gradebook.csv"
    content = (
        "Roll_No,Student_Name,Grade,Total_Marks,Verification_ID\n"
        "201,Rohan Verma,A,91,VER-2026-201\n"
        "202,Meera Krishnan,A+,97.5,VER-2026-202\n"
        "203,Kabir: Singh/Gill*?,B+,84,VER-2026-203\n"
    )
    csv_path.write_text(content, encoding="utf-8-sig")
    return csv_path
