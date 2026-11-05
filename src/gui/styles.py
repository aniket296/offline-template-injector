"""Modern corporate Slate-Indigo theme and typography configuration for Tkinter/ttk."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

# Color Palette Constants
COLOR_PRIMARY_HEADER = "#1E1B4B"    # Deep Slate-Indigo
COLOR_ACCENT = "#4F46E5"            # Vibrant Indigo
COLOR_ACCENT_HOVER = "#4338CA"      # Darker Indigo hover
COLOR_BG_MAIN = "#F8FAFC"           # Crisp Alabaster / Slate 50
COLOR_BG_PANEL = "#FFFFFF"          # Pure White card surface
COLOR_BG_CANVAS = "#CBD5E1"         # Neutral workspace backdrop
COLOR_BORDER = "#E2E8F0"            # Subtle Slate 200 divider
COLOR_TEXT_PRIMARY = "#0F172A"      # Slate 900
COLOR_TEXT_SECONDARY = "#475569"    # Slate 600
COLOR_SUCCESS = "#10B981"           # Emerald 500
COLOR_SUCCESS_HOVER = "#059669"     # Emerald 600
COLOR_DANGER = "#EF4444"            # Red 500
COLOR_DANGER_HOVER = "#DC2626"      # Red 600
COLOR_WARNING = "#F59E0B"           # Amber 500

FONT_FAMILY_UI = "Segoe UI"
FONT_HEADER = (FONT_FAMILY_UI, 12, "bold")
FONT_SECTION = (FONT_FAMILY_UI, 10, "bold")
FONT_BODY = (FONT_FAMILY_UI, 9)
FONT_BODY_BOLD = (FONT_FAMILY_UI, 9, "bold")
FONT_SMALL = (FONT_FAMILY_UI, 8)
FONT_MONO = ("Consolas", 9)


def apply_slate_indigo_theme(root: tk.Misc) -> ttk.Style:
    """Applies the Slate-Indigo corporate theme using ttk.Style('clam')."""
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    style.configure(
        ".",
        background=COLOR_BG_MAIN,
        foreground=COLOR_TEXT_PRIMARY,
        font=FONT_BODY,
        bordercolor=COLOR_BORDER,
        focuscolor=COLOR_ACCENT,
    )

    style.configure("TFrame", background=COLOR_BG_MAIN)
    style.configure("Card.TFrame", background=COLOR_BG_PANEL, relief="flat")
    style.configure("Header.TFrame", background=COLOR_PRIMARY_HEADER)

    style.configure(
        "TLabel",
        background=COLOR_BG_MAIN,
        foreground=COLOR_TEXT_PRIMARY,
        font=FONT_BODY,
    )
    style.configure(
        "Card.TLabel",
        background=COLOR_BG_PANEL,
        foreground=COLOR_TEXT_PRIMARY,
        font=FONT_BODY,
    )
    style.configure(
        "Muted.TLabel",
        background=COLOR_BG_PANEL,
        foreground=COLOR_TEXT_SECONDARY,
        font=FONT_SMALL,
    )
    style.configure(
        "Section.TLabel",
        background=COLOR_BG_PANEL,
        foreground=COLOR_PRIMARY_HEADER,
        font=FONT_SECTION,
    )
    style.configure(
        "HeaderTitle.TLabel",
        background=COLOR_PRIMARY_HEADER,
        foreground="#FFFFFF",
        font=FONT_HEADER,
    )
    style.configure(
        "HeaderSub.TLabel",
        background=COLOR_PRIMARY_HEADER,
        foreground="#C7D2FE",
        font=FONT_SMALL,
    )

    # Standard Secondary Button
    style.configure(
        "TButton",
        background="#FFFFFF",
        foreground=COLOR_TEXT_PRIMARY,
        bordercolor=COLOR_BORDER,
        lightcolor="#FFFFFF",
        darkcolor=COLOR_BORDER,
        padding=(10, 5),
        font=FONT_BODY,
    )
    style.map(
        "TButton",
        background=[("active", "#F1F5F9"), ("disabled", "#F8FAFC")],
        foreground=[("disabled", "#94A3B8")],
    )

    # Accent Indigo Button
    style.configure(
        "Accent.TButton",
        background=COLOR_ACCENT,
        foreground="#FFFFFF",
        bordercolor=COLOR_ACCENT,
        lightcolor=COLOR_ACCENT,
        darkcolor=COLOR_ACCENT,
        padding=(11, 5),
        font=FONT_BODY_BOLD,
    )
    style.map(
        "Accent.TButton",
        background=[("active", COLOR_ACCENT_HOVER), ("disabled", "#94A3B8")],
        foreground=[("disabled", "#E2E8F0")],
    )

    # Emerald Success Button (Batch Export)
    style.configure(
        "Success.TButton",
        background=COLOR_SUCCESS,
        foreground="#FFFFFF",
        bordercolor=COLOR_SUCCESS,
        lightcolor=COLOR_SUCCESS,
        darkcolor=COLOR_SUCCESS,
        padding=(12, 6),
        font=FONT_BODY_BOLD,
    )
    style.map(
        "Success.TButton",
        background=[("active", COLOR_SUCCESS_HOVER), ("disabled", "#94A3B8")],
        foreground=[("disabled", "#E2E8F0")],
    )

    # Danger Button (Delete / Cancel)
    style.configure(
        "Danger.TButton",
        background=COLOR_DANGER,
        foreground="#FFFFFF",
        bordercolor=COLOR_DANGER,
        lightcolor=COLOR_DANGER,
        darkcolor=COLOR_DANGER,
        padding=(10, 5),
        font=FONT_BODY_BOLD,
    )
    style.map(
        "Danger.TButton",
        background=[("active", COLOR_DANGER_HOVER), ("disabled", "#FCA5A5")],
        foreground=[("disabled", "#FFFFFF")],
    )

    # Chip Button (for inserting {Column} tags)
    style.configure(
        "Chip.TButton",
        background="#EEF2FF",
        foreground=COLOR_ACCENT,
        bordercolor="#C7D2FE",
        padding=(6, 2),
        font=FONT_SMALL,
    )
    style.map(
        "Chip.TButton",
        background=[("active", "#E0E7FF")],
    )

    # Entries, Comboboxes, Spinboxes
    style.configure(
        "TEntry",
        fieldbackground="#FFFFFF",
        foreground=COLOR_TEXT_PRIMARY,
        bordercolor=COLOR_BORDER,
        padding=4,
    )
    style.configure(
        "TCombobox",
        fieldbackground="#FFFFFF",
        background="#FFFFFF",
        foreground=COLOR_TEXT_PRIMARY,
        padding=4,
    )
    style.configure(
        "TSpinbox",
        fieldbackground="#FFFFFF",
        foreground=COLOR_TEXT_PRIMARY,
        padding=3,
    )

    # Checkbuttons & Radiobuttons
    style.configure("Card.TCheckbutton", background=COLOR_BG_PANEL, foreground=COLOR_TEXT_PRIMARY, font=FONT_BODY)
    style.configure("Card.TRadiobutton", background=COLOR_BG_PANEL, foreground=COLOR_TEXT_PRIMARY, font=FONT_BODY)

    # Labelframes
    style.configure(
        "Card.TLabelframe",
        background=COLOR_BG_PANEL,
        foreground=COLOR_PRIMARY_HEADER,
        bordercolor=COLOR_BORDER,
    )
    style.configure(
        "Card.TLabelframe.Label",
        background=COLOR_BG_PANEL,
        foreground=COLOR_PRIMARY_HEADER,
        font=FONT_SECTION,
    )

    # Progressbar
    style.configure(
        "Emerald.Horizontal.TProgressbar",
        troughcolor="#E2E8F0",
        background=COLOR_SUCCESS,
        bordercolor="#E2E8F0",
        lightcolor=COLOR_SUCCESS,
        darkcolor=COLOR_SUCCESS,
        thickness=14,
    )

    return style
