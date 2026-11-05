"""Top action toolbar component with grouped File, Field Insertion, and Preset actions."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from src.gui.styles import (
    COLOR_BG_PANEL,
    COLOR_BORDER,
    COLOR_PRIMARY_HEADER,
    FONT_SMALL,
)
from src.models.field_node import FieldType


class TopActionToolbar(ttk.Frame):
    """Top bar providing grouped buttons for loading files, adding fields, and managing presets."""

    def __init__(
        self,
        parent: tk.Misc,
        on_load_template: Optional[Callable[[], None]] = None,
        on_load_data: Optional[Callable[[], None]] = None,
        on_add_field: Optional[Callable[[FieldType], None]] = None,
        on_delete_field: Optional[Callable[[], None]] = None,
        on_save_preset: Optional[Callable[[], None]] = None,
        on_load_preset: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent, style="Card.TFrame")
        self.on_load_template = on_load_template
        self.on_load_data = on_load_data
        self.on_add_field = on_add_field
        self.on_delete_field = on_delete_field
        self.on_save_preset = on_save_preset
        self.on_load_preset = on_load_preset

        self._build_ui()

    def _build_ui(self) -> None:
        # Top Indigo Brand Banner
        banner = ttk.Frame(self, style="Header.TFrame", padding=(14, 8))
        banner.pack(side=tk.TOP, fill=tk.X)

        title_lbl = ttk.Label(
            banner,
            text="Offline Template & Variable Field Injector",
            style="HeaderTitle.TLabel",
        )
        title_lbl.pack(side=tk.LEFT)

        sub_lbl = ttk.Label(
            banner,
            text="100% Local Report Card & Certificate Batch Generator",
            style="HeaderSub.TLabel",
        )
        sub_lbl.pack(side=tk.RIGHT, padx=(8, 0))

        # Action Button Strip
        bar = tk.Frame(self, bg=COLOR_BG_PANEL, padx=10, pady=7)
        bar.pack(side=tk.TOP, fill=tk.X)

        # --- Group 1: Files ---
        files_grp = tk.Frame(bar, bg=COLOR_BG_PANEL)
        files_grp.pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(
            files_grp,
            text="FILES",
            bg=COLOR_BG_PANEL,
            fg=COLOR_PRIMARY_HEADER,
            font=FONT_SMALL,
        ).pack(side=tk.TOP, anchor="w")

        files_btns = tk.Frame(files_grp, bg=COLOR_BG_PANEL)
        files_btns.pack(side=tk.TOP)

        self.btn_load_template = ttk.Button(
            files_btns,
            text="Load Template (PDF/Image)",
            style="Accent.TButton",
            command=self._handle_load_template,
        )
        self.btn_load_template.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_load_data = ttk.Button(
            files_btns,
            text="Load Data (.xlsx/.csv)",
            style="Accent.TButton",
            command=self._handle_load_data,
        )
        self.btn_load_data.pack(side=tk.LEFT)

        self._add_vertical_divider(bar)

        # --- Group 2: Insert Fields ---
        fields_grp = tk.Frame(bar, bg=COLOR_BG_PANEL)
        fields_grp.pack(side=tk.LEFT, padx=8)
        tk.Label(
            fields_grp,
            text="INSERT FIELDS",
            bg=COLOR_BG_PANEL,
            fg=COLOR_PRIMARY_HEADER,
            font=FONT_SMALL,
        ).pack(side=tk.TOP, anchor="w")

        fields_btns = tk.Frame(fields_grp, bg=COLOR_BG_PANEL)
        fields_btns.pack(side=tk.TOP)

        self.btn_add_text = ttk.Button(
            fields_btns,
            text="+ Add Text Field",
            command=lambda: self._handle_add_field(FieldType.TEXT),
        )
        self.btn_add_text.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_add_image = ttk.Button(
            fields_btns,
            text="+ Add Signature/Image Box",
            command=lambda: self._handle_add_field(FieldType.IMAGE),
        )
        self.btn_add_image.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_add_qr = ttk.Button(
            fields_btns,
            text="+ Add QR Code Box",
            command=lambda: self._handle_add_field(FieldType.QR),
        )
        self.btn_add_qr.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_delete_field = ttk.Button(
            fields_btns,
            text="Delete Selected Field",
            style="Danger.TButton",
            command=self._handle_delete_field,
        )
        self.btn_delete_field.pack(side=tk.LEFT)

        self._add_vertical_divider(bar)

        # --- Group 3: Presets ---
        presets_grp = tk.Frame(bar, bg=COLOR_BG_PANEL)
        presets_grp.pack(side=tk.LEFT, padx=(8, 0))
        tk.Label(
            presets_grp,
            text="PRESETS (.otvi)",
            bg=COLOR_BG_PANEL,
            fg=COLOR_PRIMARY_HEADER,
            font=FONT_SMALL,
        ).pack(side=tk.TOP, anchor="w")

        presets_btns = tk.Frame(presets_grp, bg=COLOR_BG_PANEL)
        presets_btns.pack(side=tk.TOP)

        self.btn_save_preset = ttk.Button(
            presets_btns,
            text="Save Layout (.otvi)",
            command=self._handle_save_preset,
        )
        self.btn_save_preset.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_load_preset = ttk.Button(
            presets_btns,
            text="Load Layout (.otvi)",
            command=self._handle_load_preset,
        )
        self.btn_load_preset.pack(side=tk.LEFT)

        # Bottom hairline border
        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(side=tk.BOTTOM, fill=tk.X)

    def _add_vertical_divider(self, parent: tk.Misc) -> None:
        div = tk.Frame(parent, bg=COLOR_BORDER, width=1, height=38)
        div.pack(side=tk.LEFT, padx=6, pady=2)

    def _handle_load_template(self) -> None:
        if self.on_load_template:
            self.on_load_template()

    def _handle_load_data(self) -> None:
        if self.on_load_data:
            self.on_load_data()

    def _handle_add_field(self, field_type: FieldType) -> None:
        if self.on_add_field:
            self.on_add_field(field_type)

    def _handle_delete_field(self) -> None:
        if self.on_delete_field:
            self.on_delete_field()

    def _handle_save_preset(self) -> None:
        if self.on_save_preset:
            self.on_save_preset()

    def _handle_load_preset(self) -> None:
        if self.on_load_preset:
            self.on_load_preset()
