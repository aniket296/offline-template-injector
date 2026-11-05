"""Project state and output configuration models for .otvi presets."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.models.field_node import FieldNode


class ExportMode(str, Enum):
    """Supported batch PDF export modes."""

    INDIVIDUAL_PDFS = "INDIVIDUAL_PDFS"
    MERGED_MASTER_PDF = "MERGED_MASTER_PDF"
    BOTH = "BOTH"


@dataclass
class OutputSettings:
    """Configuration for batch export paths, naming patterns, and output modes."""

    output_dir: str = ""
    filename_pattern: str = "{Index}_{Column0}"
    export_mode: ExportMode = ExportMode.BOTH
    merged_filename: str = "Master_Batch_Output.pdf"

    def to_dict(self) -> dict[str, Any]:
        """Serializes OutputSettings to a JSON-compatible dictionary."""
        return {
            "output_dir": self.output_dir,
            "filename_pattern": self.filename_pattern,
            "export_mode": self.export_mode.value if isinstance(self.export_mode, ExportMode) else str(self.export_mode),
            "merged_filename": self.merged_filename,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OutputSettings:
        """Deserializes OutputSettings from a dictionary."""
        raw_mode = data.get("export_mode", ExportMode.BOTH.value)
        mode = ExportMode(raw_mode) if not isinstance(raw_mode, ExportMode) else raw_mode
        return cls(
            output_dir=str(data.get("output_dir", "")),
            filename_pattern=str(data.get("filename_pattern", "{Index}_{Column0}")),
            export_mode=mode,
            merged_filename=str(data.get("merged_filename", "Master_Batch_Output.pdf")),
        )


@dataclass
class TemplateProject:
    """Complete serializable state of a template layout project (.otvi)."""

    template_path: str = ""
    data_source_path: str = ""
    fields: list[FieldNode] = field(default_factory=list)
    output_settings: OutputSettings = field(default_factory=OutputSettings)

    def to_dict(self) -> dict[str, Any]:
        """Serializes the TemplateProject to a JSON-compatible dictionary."""
        return {
            "version": "1.0",
            "template_path": self.template_path,
            "data_source_path": self.data_source_path,
            "fields": [f.to_dict() for f in self.fields],
            "output_settings": self.output_settings.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TemplateProject:
        """Deserializes a TemplateProject from a dictionary."""
        raw_fields = data.get("fields", [])
        raw_settings = data.get("output_settings", {})
        return cls(
            template_path=str(data.get("template_path", "")),
            data_source_path=str(data.get("data_source_path", "")),
            fields=[FieldNode.from_dict(item) for item in raw_fields],
            output_settings=OutputSettings.from_dict(raw_settings),
        )

