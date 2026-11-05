"""Domain models for template variable field nodes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class FieldType(str, Enum):
    """Supported variable field types on a document template."""

    TEXT = "TEXT"
    IMAGE = "IMAGE"
    QR = "QR"


class TextAlignment(str, Enum):
    """Horizontal text alignment inside a field bounding box."""

    LEFT = "LEFT"
    CENTER = "CENTER"
    RIGHT = "RIGHT"


@dataclass
class FieldNode:
    """Represents a placed variable field box on a document template page."""

    field_id: str
    field_type: FieldType
    label: str
    mapped_column: str
    x: float
    y: float
    static_value: str = ""
    width: float = 180.0
    height: float = 36.0
    font_family: str = "helv"
    font_size: int = 14
    min_font_size: int = 6
    auto_shrink: bool = True
    bold: bool = False
    italic: bool = False
    color_hex: str = "#1E293B"
    alignment: TextAlignment = TextAlignment.CENTER
    page_index: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serializes the FieldNode into a JSON-compatible dictionary."""
        return {
            "field_id": self.field_id,
            "field_type": self.field_type.value if isinstance(self.field_type, FieldType) else str(self.field_type),
            "label": self.label,
            "mapped_column": self.mapped_column,
            "static_value": self.static_value,
            "x": float(self.x),
            "y": float(self.y),
            "width": float(self.width),
            "height": float(self.height),
            "font_family": self.font_family,
            "font_size": int(self.font_size),
            "min_font_size": int(self.min_font_size),
            "auto_shrink": bool(self.auto_shrink),
            "bold": bool(self.bold),
            "italic": bool(self.italic),
            "color_hex": self.color_hex,
            "alignment": self.alignment.value if isinstance(self.alignment, TextAlignment) else str(self.alignment),
            "page_index": int(self.page_index),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FieldNode:
        """Deserializes a FieldNode from a dictionary."""
        raw_type = data.get("field_type", FieldType.TEXT.value)
        field_type = FieldType(raw_type) if not isinstance(raw_type, FieldType) else raw_type

        raw_align = data.get("alignment", TextAlignment.CENTER.value)
        alignment = TextAlignment(raw_align) if not isinstance(raw_align, TextAlignment) else raw_align

        return cls(
            field_id=str(data["field_id"]),
            field_type=field_type,
            label=str(data.get("label", "Field")),
            mapped_column=str(data.get("mapped_column", "")),
            static_value=str(data.get("static_value", "")),
            x=float(data.get("x", 0.0)),
            y=float(data.get("y", 0.0)),
            width=float(data.get("width", 180.0)),
            height=float(data.get("height", 36.0)),
            font_family=str(data.get("font_family", "helv")),
            font_size=int(data.get("font_size", 14)),
            min_font_size=int(data.get("min_font_size", 6)),
            auto_shrink=bool(data.get("auto_shrink", True)),
            bold=bool(data.get("bold", False)),
            italic=bool(data.get("italic", False)),
            color_hex=str(data.get("color_hex", "#1E293B")),
            alignment=alignment,
            page_index=int(data.get("page_index", 0)),
        )

