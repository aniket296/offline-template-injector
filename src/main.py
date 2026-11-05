"""Application entry point for Offline Template & Variable Field Injector."""

from __future__ import annotations

import tkinter as tk

from src.gui.app import OfflineTemplateInjectorApp, enable_windows_high_dpi
from src.utils.logger import setup_logger


def main() -> None:
    """Initializes High-DPI mode, logger, and launches the desktop GUI."""
    setup_logger()
    enable_windows_high_dpi()
    root = tk.Tk()
    _app = OfflineTemplateInjectorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
