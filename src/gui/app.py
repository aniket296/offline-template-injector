"""Main Tkinter application shell for Offline Template & Variable Field Injector."""

from __future__ import annotations

import ctypes
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk

from src.gui.components.toolbar import TopActionToolbar
from src.gui.styles import COLOR_BG_MAIN, apply_slate_indigo_theme
from src.utils.logger import get_logger

logger = get_logger("gui.app")


def enable_windows_high_dpi() -> None:
    """Enables per-monitor High-DPI awareness on Windows."""
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def resolve_asset_path(relative_path: str) -> Path:
    """Resolves asset paths both in local source checkouts and PyInstaller bundles."""
    if hasattr(sys, "_MEIPASS"):
        base_dir = Path(getattr(sys, "_MEIPASS"))
    else:
        base_dir = Path(__file__).resolve().parent.parent.parent
    return base_dir / relative_path


class OfflineTemplateInjectorApp:
    """Top-level desktop application controller and window shell."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Offline Template & Variable Field Injector v1.0.0")
        self.root.geometry("1360x860")
        self.root.minsize(1100, 720)
        self.root.configure(bg=COLOR_BG_MAIN)

        self._load_window_icon()
        self.style = apply_slate_indigo_theme(self.root)

        self.toolbar = TopActionToolbar(self.root)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.main_workspace = ttk.Frame(self.root, style="TFrame")
        self.main_workspace.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def _load_window_icon(self) -> None:
        """Sets the window icon from assets/app_icon.ico if available."""
        icon_path = resolve_asset_path("assets/app_icon.ico")
        if icon_path.exists():
            try:
                self.root.iconbitmap(default=str(icon_path))
            except Exception as exc:
                logger.debug("Could not load window icon: %s", exc)
