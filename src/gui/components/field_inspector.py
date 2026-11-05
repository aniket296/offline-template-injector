"""Right-hand sidebar property inspector for configuring the selected FieldNode."""

from __future__ import annotations

import tkinter as tk
from tkinter import colorchooser, filedialog, ttk
from typing import Callable, Optional

from src.gui.styles import (
    COLOR_BG_PANEL,
    COLOR_BORDER,
    COLOR_PRIMARY_HEADER,
    COLOR_TEXT_SECONDARY,
    FONT_BODY,
    FONT_SECTION,
    FONT_SMALL,
)
from src.models.field_node import FieldNode, FieldType, TextAlignment


_FONT_DISPLAY_TO_CODE = {
    "Helvetica": "helv",
    "Times Roman": "tiro",
    "Courier": "cour",
}
_FONT_CODE_TO_DISPLAY = {v: k for k, v in _FONT_DISPLAY_TO_CODE.items()}


class FieldPropertyInspector(ttk.Frame):
    """Right-hand sidebar panel for editing data binding, typography, and geometry of a FieldNode."""

    def __init__(
        self,
        parent: tk.Misc,
        on_property_changed: Optional[Callable[[FieldNode], None]] = None,
    ) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(12, 10))
        self.on_property_changed = on_property_changed
        self.current_field: Optional[FieldNode] = None
        self.available_columns: list[str] = []
        self._updating_ui = False

        # Tkinter variables
        self.var_label = tk.StringVar()
        self.var_mapped_col = tk.StringVar()
        self.var_static_val = tk.StringVar()
        self.var_font_family = tk.StringVar(value="Helvetica")
        self.var_font_size = tk.IntVar(value=14)
        self.var_min_font_size = tk.IntVar(value=6)
        self.var_auto_shrink = tk.BooleanVar(value=True)
        self.var_bold = tk.BooleanVar(value=False)
        self.var_italic = tk.BooleanVar(value=False)
        self.var_alignment = tk.StringVar(value=TextAlignment.CENTER.value)
        self.var_color_hex = tk.StringVar(value="#1E293B")

        self.var_x = tk.DoubleVar(value=100.0)
        self.var_y = tk.DoubleVar(value=100.0)
        self.var_width = tk.DoubleVar(value=180.0)
        self.var_height = tk.DoubleVar(value=36.0)

        self._build_ui()
        self.load_field(None)

    def _build_ui(self) -> None:
        header = tk.Frame(self, bg=COLOR_BG_PANEL)
        header.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))

        tk.Label(
            header,
            text="Field Property Inspector",
            bg=COLOR_BG_PANEL,
            fg=COLOR_PRIMARY_HEADER,
            font=FONT_SECTION,
        ).pack(side=tk.LEFT)

        self.lbl_field_type_badge = tk.Label(
            header,
            text="NONE SELECTED",
            bg="#E2E8F0",
            fg=COLOR_TEXT_SECONDARY,
            font=FONT_SMALL,
            padx=6,
            pady=2,
        )
        self.lbl_field_type_badge.pack(side=tk.RIGHT)

        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(side=tk.TOP, fill=tk.X, pady=(0, 8))

        # --- Section 1: Identity & Data Binding ---
        bind_frame = ttk.LabelFrame(
            self, text="Data Binding & Source", style="Card.TLabelframe", padding=(10, 8)
        )
        bind_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 8))

        ttk.Label(bind_frame, text="Field Label:", style="Card.TLabel").pack(
            side=tk.TOP, anchor="w"
        )
        self.ent_label = ttk.Entry(bind_frame, textvariable=self.var_label)
        self.ent_label.pack(side=tk.TOP, fill=tk.X, pady=(2, 6))
        self.ent_label.bind("<KeyRelease>", self._on_ui_edited)

        ttk.Label(
            bind_frame,
            text="Spreadsheet Column Mapping:",
            style="Card.TLabel",
        ).pack(side=tk.TOP, anchor="w")
        self.cmb_column = ttk.Combobox(
            bind_frame,
            textvariable=self.var_mapped_col,
            state="readonly",
            values=["(Unmapped / Static Only)"],
        )
        self.cmb_column.pack(side=tk.TOP, fill=tk.X, pady=(2, 6))
        self.cmb_column.bind("<<ComboboxSelected>>", self._on_ui_edited)

        self.lbl_static_caption = ttk.Label(
            bind_frame,
            text="Static Prefix / Fallback Image Path:",
            style="Card.TLabel",
        )
        self.lbl_static_caption.pack(side=tk.TOP, anchor="w")

        static_row = tk.Frame(bind_frame, bg=COLOR_BG_PANEL)
        static_row.pack(side=tk.TOP, fill=tk.X, pady=(2, 2))

        self.ent_static = ttk.Entry(static_row, textvariable=self.var_static_val)
        self.ent_static.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.ent_static.bind("<KeyRelease>", self._on_ui_edited)

        self.btn_browse_img = ttk.Button(
            static_row,
            text="Browse PNG...",
            command=self._browse_static_image,
        )
        self.btn_browse_img.pack(side=tk.LEFT, padx=(5, 0))

        # --- Section 2: Typography Controls ---
        self.typo_frame = ttk.LabelFrame(
            self, text="Typography & Auto-Fit", style="Card.TLabelframe", padding=(10, 8)
        )
        self.typo_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 8))

        font_row = tk.Frame(self.typo_frame, bg=COLOR_BG_PANEL)
        font_row.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))

        ttk.Label(font_row, text="Font Family:", style="Card.TLabel").pack(
            side=tk.LEFT
        )
        self.cmb_font = ttk.Combobox(
            font_row,
            textvariable=self.var_font_family,
            state="readonly",
            values=list(_FONT_DISPLAY_TO_CODE.keys()),
            width=15,
        )
        self.cmb_font.pack(side=tk.RIGHT)
        self.cmb_font.bind("<<ComboboxSelected>>", self._on_ui_edited)

        size_row = tk.Frame(self.typo_frame, bg=COLOR_BG_PANEL)
        size_row.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))

        ttk.Label(size_row, text="Max Size (pt):", style="Card.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.spn_font_size = ttk.Spinbox(
            size_row,
            from_=6,
            to=96,
            textvariable=self.var_font_size,
            width=6,
            command=self._on_ui_edited,
        )
        self.spn_font_size.grid(row=0, column=1, padx=(4, 12), sticky="w")
        self.spn_font_size.bind("<KeyRelease>", self._on_ui_edited)

        ttk.Label(size_row, text="Min Size (pt):", style="Card.TLabel").grid(
            row=0, column=2, sticky="w"
        )
        self.spn_min_font_size = ttk.Spinbox(
            size_row,
            from_=4,
            to=72,
            textvariable=self.var_min_font_size,
            width=6,
            command=self._on_ui_edited,
        )
        self.spn_min_font_size.grid(row=0, column=3, padx=(4, 0), sticky="w")
        self.spn_min_font_size.bind("<KeyRelease>", self._on_ui_edited)

        self.chk_auto_shrink = ttk.Checkbutton(
            self.typo_frame,
            text="Auto-Shrink to Box (Prevent Name Overflow)",
            variable=self.var_auto_shrink,
            style="Card.TCheckbutton",
            command=self._on_ui_edited,
        )
        self.chk_auto_shrink.pack(side=tk.TOP, anchor="w", pady=(0, 6))

        style_row = tk.Frame(self.typo_frame, bg=COLOR_BG_PANEL)
        style_row.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))

        self.chk_bold = ttk.Checkbutton(
            style_row,
            text="Bold",
            variable=self.var_bold,
            style="Card.TCheckbutton",
            command=self._on_ui_edited,
        )
        self.chk_bold.pack(side=tk.LEFT, padx=(0, 14))

        self.chk_italic = ttk.Checkbutton(
            style_row,
            text="Italic",
            variable=self.var_italic,
            style="Card.TCheckbutton",
            command=self._on_ui_edited,
        )
        self.chk_italic.pack(side=tk.LEFT)

        # Color picker button + swatch
        color_row = tk.Frame(self.typo_frame, bg=COLOR_BG_PANEL)
        color_row.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))
        ttk.Label(color_row, text="Text Color:", style="Card.TLabel").pack(side=tk.LEFT)

        self.color_swatch = tk.Label(
            color_row,
            text="   ",
            bg="#1E293B",
            relief=tk.SOLID,
            borderwidth=1,
            width=3,
        )
        self.color_swatch.pack(side=tk.LEFT, padx=(8, 6))

        self.btn_pick_color = ttk.Button(
            color_row,
            text="Pick Color...",
            command=self._pick_color,
        )
        self.btn_pick_color.pack(side=tk.LEFT)

        self.lbl_color_hex = ttk.Label(
            color_row, textvariable=self.var_color_hex, style="Muted.TLabel"
        )
        self.lbl_color_hex.pack(side=tk.RIGHT)

        # Alignment radio buttons
        align_row = tk.Frame(self.typo_frame, bg=COLOR_BG_PANEL)
        align_row.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(align_row, text="Align:", style="Card.TLabel").pack(
            side=tk.LEFT, padx=(0, 6)
        )
        for label_txt, align_enum in [
            ("Left", TextAlignment.LEFT),
            ("Center", TextAlignment.CENTER),
            ("Right", TextAlignment.RIGHT),
        ]:
            rb = ttk.Radiobutton(
                align_row,
                text=label_txt,
                value=align_enum.value,
                variable=self.var_alignment,
                style="Card.TRadiobutton",
                command=self._on_ui_edited,
            )
            rb.pack(side=tk.LEFT, padx=(0, 8))

        # --- Section 3: Exact Geometry Spinners ---
        geom_frame = ttk.LabelFrame(
            self, text="Exact Geometry (PDF Points)", style="Card.TLabelframe", padding=(10, 8)
        )
        geom_frame.pack(side=tk.TOP, fill=tk.X)

        grid = tk.Frame(geom_frame, bg=COLOR_BG_PANEL)
        grid.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(grid, text="X (pt):", style="Card.TLabel").grid(
            row=0, column=0, sticky="w", pady=2
        )
        self.spn_x = ttk.Spinbox(
            grid,
            from_=0.0,
            to=2500.0,
            increment=1.0,
            textvariable=self.var_x,
            width=8,
            command=self._on_ui_edited,
        )
        self.spn_x.grid(row=0, column=1, padx=(4, 12), pady=2, sticky="w")
        self.spn_x.bind("<Return>", self._on_ui_edited)
        self.spn_x.bind("<FocusOut>", self._on_ui_edited)

        ttk.Label(grid, text="Y (pt):", style="Card.TLabel").grid(
            row=0, column=2, sticky="w", pady=2
        )
        self.spn_y = ttk.Spinbox(
            grid,
            from_=0.0,
            to=2500.0,
            increment=1.0,
            textvariable=self.var_y,
            width=8,
            command=self._on_ui_edited,
        )
        self.spn_y.grid(row=0, column=3, padx=(4, 0), pady=2, sticky="w")
        self.spn_y.bind("<Return>", self._on_ui_edited)
        self.spn_y.bind("<FocusOut>", self._on_ui_edited)

        ttk.Label(grid, text="Width:", style="Card.TLabel").grid(
            row=1, column=0, sticky="w", pady=2
        )
        self.spn_width = ttk.Spinbox(
            grid,
            from_=20.0,
            to=2500.0,
            increment=2.0,
            textvariable=self.var_width,
            width=8,
            command=self._on_ui_edited,
        )
        self.spn_width.grid(row=1, column=1, padx=(4, 12), pady=2, sticky="w")
        self.spn_width.bind("<Return>", self._on_ui_edited)
        self.spn_width.bind("<FocusOut>", self._on_ui_edited)

        ttk.Label(grid, text="Height:", style="Card.TLabel").grid(
            row=1, column=2, sticky="w", pady=2
        )
        self.spn_height = ttk.Spinbox(
            grid,
            from_=12.0,
            to=2500.0,
            increment=2.0,
            textvariable=self.var_height,
            width=8,
            command=self._on_ui_edited,
        )
        self.spn_height.grid(row=1, column=3, padx=(4, 0), pady=2, sticky="w")
        self.spn_height.bind("<Return>", self._on_ui_edited)
        self.spn_height.bind("<FocusOut>", self._on_ui_edited)

    def set_available_columns(self, columns: list[str]) -> None:
        """Populates the data binding combobox with spreadsheet column headers."""
        self.available_columns = list(columns)
        values = ["(Unmapped / Static Only)"] + self.available_columns
        self.cmb_column.config(values=values)
        if self.current_field is not None:
            self.load_field(self.current_field)

    def load_field(self, field: Optional[FieldNode]) -> None:
        """Loads a FieldNode into the inspector controls (or disables controls if None)."""
        self._updating_ui = True
        self.current_field = field
        try:
            if field is None:
                self.lbl_field_type_badge.config(
                    text="NONE SELECTED", bg="#E2E8F0", fg=COLOR_TEXT_SECONDARY
                )
                self._set_controls_state("disabled")
                return

            self._set_controls_state("normal")
            self.lbl_field_type_badge.config(
                text=f"TYPE: {field.field_type.value}",
                bg="#EEF2FF",
                fg=COLOR_PRIMARY_HEADER,
            )

            self.var_label.set(field.label)
            if field.mapped_column and field.mapped_column in self.available_columns:
                self.var_mapped_col.set(field.mapped_column)
            elif field.mapped_column:
                vals = ["(Unmapped / Static Only)"] + self.available_columns
                if field.mapped_column not in vals:
                    vals.append(field.mapped_column)
                    self.cmb_column.config(values=vals)
                self.var_mapped_col.set(field.mapped_column)
            else:
                self.var_mapped_col.set("(Unmapped / Static Only)")

            self.var_static_val.set(field.static_value)
            display_font = _FONT_CODE_TO_DISPLAY.get(field.font_family, "Helvetica")
            self.var_font_family.set(display_font)
            self.var_font_size.set(field.font_size)
            self.var_min_font_size.set(field.min_font_size)
            self.var_auto_shrink.set(field.auto_shrink)
            self.var_bold.set(field.bold)
            self.var_italic.set(field.italic)
            self.var_alignment.set(field.alignment.value)
            self.var_color_hex.set(field.color_hex)
            self.color_swatch.config(bg=field.color_hex)

            self.var_x.set(round(field.x, 1))
            self.var_y.set(round(field.y, 1))
            self.var_width.set(round(field.width, 1))
            self.var_height.set(round(field.height, 1))
        finally:
            self._updating_ui = False

    def sync_geometry_from_canvas(self, field: FieldNode) -> None:
        """Updates only the numeric geometry spinners during live canvas dragging/resizing."""
        if self.current_field is None or self.current_field.field_id != field.field_id:
            self.load_field(field)
            return
        self._updating_ui = True
        try:
            self.var_x.set(round(field.x, 1))
            self.var_y.set(round(field.y, 1))
            self.var_width.set(round(field.width, 1))
            self.var_height.set(round(field.height, 1))
        finally:
            self._updating_ui = False

    def _set_controls_state(self, state: str) -> None:
        combo_state = "readonly" if state == "normal" else "disabled"
        self.ent_label.config(state=state)
        self.cmb_column.config(state=combo_state)
        self.ent_static.config(state=state)
        self.btn_browse_img.config(state=state)
        self.cmb_font.config(state=combo_state)
        self.spn_font_size.config(state=state)
        self.spn_min_font_size.config(state=state)
        self.chk_auto_shrink.config(state=state)
        self.chk_bold.config(state=state)
        self.chk_italic.config(state=state)
        self.btn_pick_color.config(state=state)
        self.spn_x.config(state=state)
        self.spn_y.config(state=state)
        self.spn_width.config(state=state)
        self.spn_height.config(state=state)

    def _browse_static_image(self) -> None:
        if self.current_field is None:
            return
        file_path = filedialog.askopenfilename(
            title="Select Static Signature or Seal Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp"), ("All Files", "*.*")],
        )
        if file_path:
            self.var_static_val.set(file_path)
            self._on_ui_edited()

    def _pick_color(self) -> None:
        if self.current_field is None:
            return
        initial = self.var_color_hex.get() or "#1E293B"
        _, hex_color = colorchooser.askcolor(color=initial, title="Choose Field Text Color")
        if hex_color:
            hex_upper = hex_color.upper()
            self.var_color_hex.set(hex_upper)
            self.color_swatch.config(bg=hex_upper)
            self._on_ui_edited()

    def _on_ui_edited(self, _event: Optional[tk.Event] = None) -> None:
        if self._updating_ui or self.current_field is None:
            return

        f = self.current_field
        f.label = self.var_label.get().strip() or "Field"
        col_sel = self.var_mapped_col.get()
        f.mapped_column = "" if col_sel == "(Unmapped / Static Only)" else col_sel
        f.static_value = self.var_static_val.get()
        f.font_family = _FONT_DISPLAY_TO_CODE.get(self.var_font_family.get(), "helv")

        try:
            f.font_size = max(4, min(120, int(self.var_font_size.get())))
        except ( tk.TclError, ValueError):
            pass

        try:
            f.min_font_size = max(4, min(f.font_size, int(self.var_min_font_size.get())))
        except (tk.TclError, ValueError):
            pass

        f.auto_shrink = bool(self.var_auto_shrink.get())
        f.bold = bool(self.var_bold.get())
        f.italic = bool(self.var_italic.get())
        f.alignment = TextAlignment(self.var_alignment.get())
        f.color_hex = self.var_color_hex.get()

        try:
            f.x = max(0.0, float(self.var_x.get()))
            f.y = max(0.0, float(self.var_y.get()))
            f.width = max(20.0, float(self.var_width.get()))
            f.height = max(12.0, float(self.var_height.get()))
        except (tk.TclError, ValueError):
            pass

        if self.on_property_changed:
            self.on_property_changed(f)
