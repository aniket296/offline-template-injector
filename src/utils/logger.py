"""Thread-safe rotating file logger and GUI queue listener."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import queue
from typing import Optional

from src.utils.config import get_app_log_level

_LOG_QUEUE: queue.Queue[str] = queue.Queue(maxsize=2000)
_LOGGER_INITIALIZED = False


class QueueLogHandler(logging.Handler):
    """Pushes formatted log records into a thread-safe queue for live GUI display."""

    def __init__(self, log_queue: queue.Queue[str]) -> None:
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            try:
                self.log_queue.put_nowait(msg)
            except queue.Full:
                try:
                    self.log_queue.get_nowait()
                except queue.Empty:
                    pass
                self.log_queue.put_nowait(msg)
        except Exception:
            self.handleError(record)


def get_log_file_path() -> Path:
    """Returns the path to ~/.offline_template_injector/app.log."""
    log_dir = Path.home() / ".offline_template_injector"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return log_dir / "app.log"


def get_log_queue() -> queue.Queue[str]:
    """Returns the shared thread-safe queue containing formatted log messages."""
    return _LOG_QUEUE


def setup_logger(name: str = "offline_template_injector") -> logging.Logger:
    """Configures and returns the application logger with file and queue handlers."""
    global _LOGGER_INITIALIZED
    logger = logging.getLogger(name)

    if not _LOGGER_INITIALIZED:
        level_name = get_app_log_level()
        level = getattr(logging, level_name, logging.INFO)
        logger.setLevel(level)
        logger.propagate = False

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        try:
            log_file = get_log_file_path()
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=5 * 1024 * 1024,
                backupCount=3,
                encoding="utf-8",
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError:
            # Fallback if home directory is not writable
            pass

        queue_handler = QueueLogHandler(_LOG_QUEUE)
        queue_handler.setLevel(level)
        queue_handler.setFormatter(formatter)
        logger.addHandler(queue_handler)

        _LOGGER_INITIALIZED = True

    return logger


def get_logger(module_name: Optional[str] = None) -> logging.Logger:
    """Returns a child logger attached to the configured root application logger."""
    base = setup_logger()
    if module_name:
        return base.getChild(module_name)
    return base

