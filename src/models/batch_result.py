"""Batch processing result and summary models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class RowStatus(str, Enum):
    """Execution status of a single spreadsheet row during batch rendering."""

    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


@dataclass
class RowTaskResult:
    """Result record for a single processed row in a batch."""

    row_index: int
    output_file: Optional[str]
    status: RowStatus
    error_message: Optional[str] = None
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serializes RowTaskResult into a dictionary."""
        return {
            "row_index": self.row_index,
            "output_file": self.output_file,
            "status": self.status.value if isinstance(self.status, RowStatus) else str(self.status),
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
        }


@dataclass
class BatchSummary:
    """Aggregated outcome of a complete batch export run."""

    total_rows: int
    succeeded: int
    failed: int
    merged_pdf_path: Optional[str] = None
    results: list[RowTaskResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serializes BatchSummary into a dictionary."""
        return {
            "total_rows": self.total_rows,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "merged_pdf_path": self.merged_pdf_path,
            "results": [r.to_dict() for r in self.results],
        }

