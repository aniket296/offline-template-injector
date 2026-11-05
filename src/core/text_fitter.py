"""Bounding-box auto-shrink text fitting math and hex color conversion utilities."""

from __future__ import annotations

import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore", FutureWarning)
    import fitz


_FONT_MAP = {
    ("helv", False, False): "helv",
    ("helv", True, False): "hebo",
    ("helv", False, True): "heit",
    ("helv", True, True): "hebi",
    ("tiro", False, False): "tiro",
    ("tiro", True, False): "tibo",
    ("tiro", False, True): "tiit",
    ("tiro", True, True): "tibi",
    ("cour", False, False): "cour",
    ("cour", True, False): "cobo",
    ("cour", False, True): "coit",
    ("cour", True, True): "cobi",
}


def resolve_pdf_font_name(font_family: str, bold: bool = False, italic: bool = False) -> str:
    """Resolves a base font family ('helv', 'tiro', 'cour') and style flags to a Base-14 PDF font code."""
    family = (font_family or "helv").strip().lower()
    if family not in ("helv", "tiro", "cour"):
        if "times" in family or "ti" in family:
            family = "tiro"
        elif "cour" in family or "mono" in family:
            family = "cour"
        else:
            family = "helv"
    return _FONT_MAP.get((family, bool(bold), bool(italic)), family)


def calculate_fitted_font_size(
    text: str,
    font_name: str,
    max_font_size: int,
    min_font_size: int,
    box_width: float,
    box_height: float,
    auto_shrink: bool = True,
) -> float:
    """Calculates the largest font size in [min_font_size, max_font_size] that fits inside box_width x box_height."""
    max_sz = max(1.0, float(max_font_size))
    min_sz = max(1.0, min(float(min_font_size), max_sz))

    if not text or not auto_shrink:
        return max_sz

    try:
        font = fitz.Font(fontname=font_name)
    except Exception:
        font = fitz.Font(fontname="helv")

    usable_width = max(1.0, float(box_width) - 4.0)
    usable_height = max(1.0, float(box_height) - 2.0)

    current_size = max_sz
    step = 0.5
    while current_size > min_sz:
        text_w = font.text_length(text, fontsize=current_size)
        text_h = current_size * 1.15
        if text_w <= usable_width and text_h <= usable_height:
            return round(current_size, 2)
        current_size -= step

    return round(min_sz, 2)


def hex_to_rgb_float(hex_str: str) -> tuple[float, float, float]:
    """Converts a hex color string (e.g. '#1E293B') to PyMuPDF RGB floats in 0.0 - 1.0."""
    cleaned = (hex_str or "#000000").strip().lstrip("#")
    if len(cleaned) == 3:
        cleaned = "".join(ch * 2 for ch in cleaned)
    if len(cleaned) != 6:
        return (0.0, 0.0, 0.0)
    try:
        r = int(cleaned[0:2], 16) / 255.0
        g = int(cleaned[2:4], 16) / 255.0
        b = int(cleaned[4:6], 16) / 255.0
        return (round(r, 4), round(g, 4), round(b, 4))
    except ValueError:
        return (0.0, 0.0, 0.0)
