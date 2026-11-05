"""Excel (.xlsx) and CSV data loader engine with formula value extraction and normalization."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
import openpyxl


@dataclass
class SpreadsheetData:
    """Normalized tabular dataset loaded from an Excel or CSV file."""

    file_path: str
    headers: list[str]
    rows: list[dict[str, str]]


class SpreadsheetLoadError(ValueError):
    """Raised when a spreadsheet file is missing headers, empty, or malformed."""


def _normalize_cell_value(val: Any) -> str:
    """Converts a raw spreadsheet cell value into a clean string without float artifacts."""
    if val is None:
        return ""
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, int):
        return str(val)
    if isinstance(val, float):
        if val.is_integer():
            return str(int(val))
        return f"{val:.6f}".rstrip("0").rstrip(".")
    if isinstance(val, datetime):
        if val.hour == 0 and val.minute == 0 and val.second == 0:
            return val.strftime("%Y-%m-%d")
        return val.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(val, date):
        return val.strftime("%Y-%m-%d")

    text = str(val).strip()
    # Handle string representations of integer floats if any
    return text


def _deduplicate_headers(raw_headers: list[str]) -> list[str]:
    """Ensures non-empty unique column headers while preserving original names."""
    headers: list[str] = []
    seen: dict[str, int] = {}
    for idx, h in enumerate(raw_headers):
        clean_h = h.strip()
        if not clean_h:
            clean_h = f"Column_{idx + 1}"
        if clean_h in seen:
            seen[clean_h] += 1
            headers.append(f"{clean_h}_{seen[clean_h]}")
        else:
            seen[clean_h] = 1
            headers.append(clean_h)
    return headers


def _load_xlsx(path: Path) -> SpreadsheetData:
    """Loads an Excel .xlsx file using openpyxl with data_only=True."""
    wb = openpyxl.load_workbook(filename=str(path), read_only=True, data_only=True)
    try:
        sheet = wb.active
        if sheet is None:
            raise SpreadsheetLoadError(f"Workbook '{path.name}' contains no active worksheet.")

        row_iter = sheet.iter_rows(values_only=True)
        raw_header_row = None
        for candidate in row_iter:
            if candidate and any(cell is not None and str(cell).strip() != "" for cell in candidate):
                raw_header_row = candidate
                break

        if raw_header_row is None:
            raise SpreadsheetLoadError(f"Spreadsheet '{path.name}' has no header row.")

        str_headers = [_normalize_cell_value(c) for c in raw_header_row]
        # Trim trailing completely blank header columns
        while str_headers and str_headers[-1] == "":
            str_headers.pop()

        if not str_headers:
            raise SpreadsheetLoadError(f"Spreadsheet '{path.name}' has no valid column headers.")

        headers = _deduplicate_headers(str_headers)
        num_cols = len(headers)

        rows: list[dict[str, str]] = []
        for raw_row in row_iter:
            if raw_row is None:
                continue
            normalized_vals = [
                _normalize_cell_value(raw_row[i]) if i < len(raw_row) else ""
                for i in range(num_cols)
            ]
            if not any(v != "" for v in normalized_vals):
                continue
            row_dict = {headers[i]: normalized_vals[i] for i in range(num_cols)}
            rows.append(row_dict)

        if not rows:
            raise SpreadsheetLoadError(
                f"Spreadsheet '{path.name}' contains headers {headers} but zero data rows."
            )

        return SpreadsheetData(file_path=str(path), headers=headers, rows=rows)
    finally:
        wb.close()


def _load_csv(path: Path) -> SpreadsheetData:
    """Loads a CSV file trying UTF-8-SIG, UTF-8, and CP1252 encodings automatically."""
    encodings = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
    content: str | None = None
    for enc in encodings:
        try:
            content = path.read_text(encoding=enc)
            break
        except UnicodeDecodeError:
            continue

    if content is None:
        raise SpreadsheetLoadError(f"Unable to decode CSV file '{path.name}' with standard encodings.")

    lines = [line for line in content.splitlines() if line.strip() != ""]
    if not lines:
        raise SpreadsheetLoadError(f"CSV file '{path.name}' is empty and has no header row.")

    reader = csv.reader(lines)
    try:
        raw_header = next(reader)
    except StopIteration as exc:
        raise SpreadsheetLoadError(f"CSV file '{path.name}' has no header row.") from exc

    str_headers = [_normalize_cell_value(c) for c in raw_header]
    while str_headers and str_headers[-1] == "":
        str_headers.pop()

    if not str_headers:
        raise SpreadsheetLoadError(f"CSV file '{path.name}' has no valid column headers.")

    headers = _deduplicate_headers(str_headers)
    num_cols = len(headers)

    rows: list[dict[str, str]] = []
    for raw_row in reader:
        normalized_vals = [
            _normalize_cell_value(raw_row[i]) if i < len(raw_row) else ""
            for i in range(num_cols)
        ]
        if not any(v != "" for v in normalized_vals):
            continue
        row_dict = {headers[i]: normalized_vals[i] for i in range(num_cols)}
        rows.append(row_dict)

    if not rows:
        raise SpreadsheetLoadError(
            f"CSV file '{path.name}' contains headers {headers} but zero data rows."
        )

    return SpreadsheetData(file_path=str(path), headers=headers, rows=rows)


def load_spreadsheet(file_path: str) -> SpreadsheetData:
    """Loads an Excel (.xlsx) or CSV (.csv) file into a normalized SpreadsheetData object."""
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Data source file not found: {file_path}")

    ext = path.suffix.lower()
    if ext == ".xlsx":
        return _load_xlsx(path)
    if ext == ".csv":
        return _load_csv(path)

    raise SpreadsheetLoadError(
        f"Unsupported spreadsheet extension '{ext}'. Please provide an .xlsx or .csv file."
    )
