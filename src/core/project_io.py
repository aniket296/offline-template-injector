"""Project layout preset (.otvi) JSON serialization and validation."""

from __future__ import annotations

import json
from pathlib import Path

from src.models.project_state import TemplateProject


class PresetIOError(ValueError):
    """Raised when a .otvi preset file cannot be parsed or fails validation."""


def save_project_preset(project: TemplateProject, file_path: str) -> None:
    """Writes a formatted .otvi JSON layout preset file to disk."""
    target = Path(file_path)
    if target.suffix.lower() != ".otvi":
        target = target.with_suffix(".otvi")
    target.parent.mkdir(parents=True, exist_ok=True)

    payload = project.to_dict()
    formatted_json = json.dumps(payload, indent=2, ensure_ascii=False)
    target.write_text(formatted_json, encoding="utf-8")


def load_project_preset(file_path: str) -> TemplateProject:
    """Loads and validates a .otvi JSON layout preset file from disk."""
    target = Path(file_path)
    if not target.exists() or not target.is_file():
        raise FileNotFoundError(f"Preset file not found: {file_path}")

    try:
        raw_text = target.read_text(encoding="utf-8")
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise PresetIOError(f"Invalid JSON in preset file '{target.name}': {exc}") from exc

    if not isinstance(data, dict):
        raise PresetIOError(f"Preset file '{target.name}' root must be a JSON object.")

    if "fields" not in data or not isinstance(data["fields"], list):
        raise PresetIOError(f"Preset file '{target.name}' is missing a valid 'fields' list.")

    try:
        return TemplateProject.from_dict(data)
    except (KeyError, ValueError, TypeError) as exc:
        raise PresetIOError(f"Preset schema validation failed for '{target.name}': {exc}") from exc
