"""Dynamic column filename parser and Windows path sanitizer."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

_ILLEGAL_WIN_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_PLACEHOLDER_PATTERN = re.compile(r"\{([^{}]+)\}")
_RESERVED_WIN_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}


def sanitize_filename_segment(text: str) -> str:
    """Scrubs illegal Windows characters and trims trailing/leading dots and spaces."""
    cleaned = _ILLEGAL_WIN_CHARS.sub("_", str(text))
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned


def _resolve_placeholder_token(
    key: str,
    record: dict[str, str],
    padded_index: str,
    first_col_val: str,
) -> str:
    """Resolves a single {Token} placeholder against built-in tags and record keys."""
    if key in ("Index", "Row_Index", "index", "row_index"):
        return padded_index
    if key in ("Column0", "First_Column", "column0", "first_column"):
        return sanitize_filename_segment(first_col_val) or f"Record_{padded_index}"
    if key in record:
        return sanitize_filename_segment(record[key]) or "NA"
    key_lower = key.lower()
    for col_name, col_val in record.items():
        if col_name.lower() == key_lower:
            return sanitize_filename_segment(col_val) or "NA"
    return sanitize_filename_segment(key)


def format_dynamic_filename(
    pattern: str,
    record: dict[str, str],
    row_index: int,
    target_dir: Optional[str | Path] = None,
) -> str:
    """Formats a dynamic filename using row values and ensures Windows filesystem safety.

    Supports:
    - {Column_Name}: Replaced with corresponding value from `record`.
    - {Index} or {Row_Index}: Replaced with 1-based zero-padded index (e.g. 001).
    - {Column0} or {First_Column}: Replaced with the first available column's value.
    """
    one_based_idx = max(1, int(row_index) + 1 if row_index >= 0 else 1)
    padded_index = f"{one_based_idx:03d}"

    first_col_val = ""
    if record:
        first_key = next(iter(record.keys()))
        first_col_val = str(record.get(first_key, "")).strip()

    effective_pattern = (pattern or "").strip() or "{Index}_{Column0}"

    rendered = _PLACEHOLDER_PATTERN.sub(
        lambda m: _resolve_placeholder_token(m.group(1).strip(), record, padded_index, first_col_val),
        effective_pattern,
    )
    # Remove any stray braces
    rendered = rendered.replace("{", "").replace("}", "")
    rendered = sanitize_filename_segment(rendered)

    # Strip existing .pdf suffix if present to normalize before collision check
    if rendered.lower().endswith(".pdf"):
        stem = rendered[:-4].strip(" .")
    else:
        stem = rendered

    if len(stem) > 180:
        stem = stem[:180].rstrip(" ._")

    if not stem or stem.upper() in _RESERVED_WIN_NAMES:
        stem = f"{padded_index}_Document"

    filename = f"{stem}.pdf"

    if target_dir is not None:
        dir_path = Path(target_dir)
        candidate = dir_path / filename
        counter = 1
        while candidate.exists():
            filename = f"{stem}_{counter}.pdf"
            candidate = dir_path / filename
            counter += 1

    return filename

