"""Unit tests for bounding-box auto-shrink font calculation and QR PNG byte generation."""

from __future__ import annotations

import io
from PIL import Image

from src.core.qr_generator import generate_qr_png_bytes
from src.core.text_fitter import (
    calculate_fitted_font_size,
    hex_to_rgb_float,
    resolve_pdf_font_name,
)


def test_calculate_fitted_font_size_shrinks_long_names() -> None:
    """Verifies extra-long student names shrink smoothly to fit within the bounding box width."""
    short_name = "Diya Patel"
    long_name = "Alexandria Maximiliana Montgomery-Featherstonehaugh III"

    size_short = calculate_fitted_font_size(
        text=short_name,
        font_name="helv",
        max_font_size=18,
        min_font_size=6,
        box_width=160.0,
        box_height=36.0,
        auto_shrink=True,
    )
    size_long = calculate_fitted_font_size(
        text=long_name,
        font_name="helv",
        max_font_size=18,
        min_font_size=6,
        box_width=160.0,
        box_height=36.0,
        auto_shrink=True,
    )

    assert size_short == 18.0
    assert 6.0 <= size_long < size_short


def test_calculate_fitted_font_size_respects_auto_shrink_disabled() -> None:
    """Verifies max_font_size is returned unchanged when auto_shrink is False."""
    size = calculate_fitted_font_size(
        text="An Extremely Long String That Exceeds Box Width Easily",
        font_name="helv",
        max_font_size=22,
        min_font_size=8,
        box_width=80.0,
        box_height=30.0,
        auto_shrink=False,
    )
    assert size == 22.0


def test_hex_to_rgb_float_and_font_resolution() -> None:
    """Verifies hex color parsing and Base-14 PDF font style mapping."""
    r, g, b = hex_to_rgb_float("#1E293B")
    assert 0.11 <= r <= 0.13
    assert 0.15 <= g <= 0.17
    assert 0.22 <= b <= 0.24

    assert resolve_pdf_font_name("helv", bold=True, italic=False) == "hebo"
    assert resolve_pdf_font_name("tiro", bold=True, italic=True) == "tibi"
    assert resolve_pdf_font_name("cour", bold=False, italic=True) == "coit"


def test_generate_qr_png_bytes_produces_valid_png_image() -> None:
    """Verifies QR generator returns non-empty valid PNG bytes decodable by Pillow."""
    png_bytes = generate_qr_png_bytes("https://school.example.edu/verify/VER-2026-101")
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")

    with Image.open(io.BytesIO(png_bytes)) as img:
        assert img.width > 32
        assert img.height > 32
        assert img.width == img.height


def test_generate_qr_png_bytes_truncates_oversized_payload_gracefully() -> None:
    """Regression test (DEF-03): payloads exceeding QR v40 capacity (>2953 bytes) are truncated cleanly."""
    oversized = "VERIFY-" + ("X" * 5000)
    png_bytes = generate_qr_png_bytes(oversized)
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")


