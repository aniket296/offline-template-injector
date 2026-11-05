"""Environment configuration loader with safe defaults."""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Attempt to load .env from project root if present
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"
if _ENV_FILE.exists():
    load_dotenv(dotenv_path=_ENV_FILE, override=False)
else:
    load_dotenv(override=False)


def get_app_log_level() -> str:
    """Returns the configured logging level (defaults to INFO)."""
    level = os.getenv("APP_LOG_LEVEL", "INFO").strip().upper()
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    return level if level in valid_levels else "INFO"


def get_default_output_pattern() -> str:
    """Returns the default dynamic filename pattern."""
    pattern = os.getenv("DEFAULT_OUTPUT_PATTERN", "{Index}_{Column0}").strip()
    return pattern if pattern else "{Index}_{Column0}"


def get_max_worker_threads() -> int:
    """Returns the maximum worker threads for batch execution (defaults to 4)."""
    raw = os.getenv("MAX_WORKER_THREADS", "4").strip()
    try:
        val = int(raw)
        return max(1, min(val, 32))
    except ValueError:
        return 4
