"""Interactive drag-and-drop template canvas editor with resizable field overlays."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
from PIL import Image, ImageTk

from src.core.template_renderer import render_canvas_preview
from src.gui.styles import (
    COLOR_ACCENT,
    COLOR_BG_CANVAS,
    COLOR_BG_PANEL,
    COLOR_BORDER,
    COLOR_PRIMARY_HEADER,
    COLOR_TEXT_SECONDARY,
    FONT_BODY,
    FONT_SMALL,
)
from src.models.field_node import FieldNode, FieldType


class TemplateCanvasEditor(ttk.Frame):
    """Scrollable, zoomable interactive canvas displaying the template and draggable FieldNodes."""

    HANDLE_SIZE = 9
    CANVAS_MARGIN = 28

    def __init__(
        self,
        parent: tk.Misc,
        on_field_selected: Optional[Callable[[Optional[FieldNode]], None]] = None,
        on_field_modified: Optional[Callable[[FieldNode], None]] = None,
        on_field_deleted: Optional[Callable[[FieldNode], None]] = None,
    ) -> None:
        super().__init__(parent, style="TFrame")
        self.on_field_selected = on_field_selected
        self.on_field_modified = on_field_modified
        self.on_field_deleted = on_field_deleted

        self.template_pdf_bytes: Optional[bytes] = None
        self.fields: list[FieldNode] = []
        self.selected_field_id: Optional[str] = None
        self.current_record: Optional[dict[str, str]] = None
        self.page_index: int = 0
        self.zoom: float = 1.0

        self._tk_image: Optional[ImageTk.PhotoImage] = None
        self._page_pixel_width: int = 595
        self._page_pixel_height: int = 842

        # Drag / Resize state
        self._drag_mode: Optional[str] = None  # "move" or "resize"
        self._drag_start_canvas_x: float = 0.0
        self._drag_start_canvas_y: float = 0.0
        self._orig_field_x: float = 0.0
        self._orig_field_y: float = 0.0
        self._orig_field_w: float = 0.0
        self._orig_field_h: float = 0.0

        self._build_ui()
        self._bind_events()
        self.refresh_canvas()

    def _build_ui(self) -> None:
        # Top Zoom & Canvas Info Strip
        top_strip = tk.Frame(self, bg=COLOR_BG_PANEL, padx=10, pady=4)
        top_strip.pack(side=tk.TOP, fill=tk.X)

        self.lbl_canvas_info = tk.Label(
            top_strip,
            text="Canvas Workspace  |  Load a PDF or Image template to begin placing variable fields",
            bg=COLOR_BG_PANEL,
            fg=COLOR_TEXT_SECONDARY,
            font=FONT_SMALL,
        )
        self.lbl_canvas_info.pack(side=tk.LEFT)

        zoom_frame = tk.Frame(top_strip, bg=COLOR_BG_PANEL)
        zoom_frame.pack(side=tk.RIGHT)

        ttk.Button(zoom_frame, text="Zoom -", width=7, command=self.zoom_out).pack(
            side=tk.LEFT, padx=2
        )
        self.lbl_zoom = tk.Label(
            zoom_frame,
            text="100%",
            bg=COLOR_BG_PANEL,
            fg=COLOR_PRIMARY_HEADER,
            font=FONT_BODY,
            width=6,
        )
        self.lbl_zoom.pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Zoom +", width=7, command=self.zoom_in).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(zoom_frame, text="100%", width=5, command=self.zoom_reset).pack(
            side=tk.LEFT, padx=(2, 0)
        )

        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(side=tk.TOP, fill=tk.X)

        # Scrollable Canvas Container
        canvas_container = ttk.Frame(self)
        canvas_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.v_scroll = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL)
        self.h_scroll = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL)

        self.canvas = tk.Canvas(
            canvas_container,
            bg=COLOR_BG_CANVAS,
            highlightthickness=0,
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set,
        )

        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _bind_events(self) -> None:
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)

        # Keyboard nudging and Delete key support when canvas has focus
        self.canvas.bind("<Up>", lambda e: self._nudge_selected(0, -1))
        self.canvas.bind("<Down>", lambda e: self._nudge_selected(0, 1))
        self.canvas.bind("<Left>", lambda e: self._nudge_selected(-1, 0))
        self.canvas.bind("<Right>", lambda e: self._nudge_selected(1, 0))
        self.canvas.bind("<Shift-Up>", lambda e: self._nudge_selected(0, -10))
        self.canvas.bind("<Shift-Down>", lambda e: self._nudge_selected(0, 10))
        self.canvas.bind("<Shift-Left>", lambda e: self._nudge_selected(-10, 0))
        self.canvas.bind("<Shift-Right>", lambda e: self._nudge_selected(10, 0))
        self.canvas.bind("<Delete>", self._on_delete_key)

    # --- Coordinate Conversion Helpers (PDF Points <-> Canvas Pixels) ---

    def pdf_to_canvas_coords(self, pdf_x: float, pdf_y: float) -> tuple[float, float]:
        """Converts PDF point coordinates (x, y) into canvas pixel coordinates."""
        cx = self.CANVAS_MARGIN + (pdf_x * self.zoom)
        cy = self.CANVAS_MARGIN + (pdf_y * self.zoom)
        return (cx, cy)

    def canvas_to_pdf_coords(self, canvas_x: float, canvas_y: float) -> tuple[float, float]:
        """Converts canvas pixel coordinates into PDF point coordinates (x, y)."""
        px = (canvas_x - self.CANVAS_MARGIN) / self.zoom
        py = (canvas_y - self.CANVAS_MARGIN) / self.zoom
        return (px, py)

    # --- Public State Setters ---

    def set_template_bytes(self, pdf_bytes: Optional[bytes]) -> None:
        """Sets the active template PDF byte stream and re-renders the canvas."""
        self.template_pdf_bytes = pdf_bytes
        self.refresh_canvas()

    def set_fields(self, fields: list[FieldNode]) -> None:
        """Sets the list of FieldNodes displayed on the canvas."""
        self.fields = fields
        if self.selected_field_id and not any(f.field_id == self.selected_field_id for f in fields):
            self.selected_field_id = fields[0].field_id if fields else None
        self.refresh_canvas()

    def set_preview_record(self, record: Optional[dict[str, str]]) -> None:
        """Sets the current spreadsheet row dict for live preview (or None for placeholders)."""
        self.current_record = record
        self.refresh_canvas()

    def get_selected_field(self) -> Optional[FieldNode]:
        """Returns the currently selected FieldNode or None."""
        for f in self.fields:
            if f.field_id == self.selected_field_id:
                return f
        return None

    def select_field(self, field_id: Optional[str], notify: bool = True) -> None:
        """Selects a field by ID and redraws bounding-box overlays."""
        self.selected_field_id = field_id
        self._draw_overlays()
        if notify and self.on_field_selected:
            self.on_field_selected(self.get_selected_field())

    # --- Zoom Controls ---

    def zoom_in(self) -> None:
        self.zoom = min(2.5, round(self.zoom + 0.15, 2))
        self.lbl_zoom.config(text=f"{int(self.zoom * 100)}%")
        self.refresh_canvas()

    def zoom_out(self) -> None:
        self.zoom = max(0.4, round(self.zoom - 0.15, 2))
        self.lbl_zoom.config(text=f"{int(self.zoom * 100)}%")
        self.refresh_canvas()

    def zoom_reset(self) -> None:
        self.zoom = 1.0
        self.lbl_zoom.config(text="100%")
        self.refresh_canvas()

    # --- Rendering ---

    def refresh_canvas(self) -> None:
        """Renders the PDF page preview image and draws interactive field bounding boxes."""
        self.canvas.delete("all")

        if self.template_pdf_bytes is None:
            self._draw_empty_placeholder()
            return

        pil_img = render_canvas_preview(
            template_pdf_bytes=self.template_pdf_bytes,
            fields=self.fields,
            record=self.current_record,
            page_index=self.page_index,
            zoom=self.zoom,
        )
        self._page_pixel_width, self._page_pixel_height = pil_img.size
        self._tk_image = ImageTk.PhotoImage(pil_img)

        m = self.CANVAS_MARGIN
        w = self._page_pixel_width
        h = self._page_pixel_height

        # Drop shadow behind template page
        self.canvas.create_rectangle(
            m + 4,
            m + 4,
            m + w + 4,
            m + h + 4,
            fill="#94A3B8",
            outline="",
            tags=("page_bg",),
        )
        # Rendered page image
        self.canvas.create_image(
            m,
            m,
            anchor=tk.NW,
            image=self._tk_image,
            tags=("page_img",),
        )
        # Crisp page border
        self.canvas.create_rectangle(
            m,
            m,
            m + w,
            m + h,
            outline="#64748B",
            width=1,
            tags=("page_border",),
        )

        total_w = w + (m * 2)
        total_h = h + (m * 2)
        self.canvas.config(scrollregion=(0, 0, total_w, total_h))

        pdf_w = round(w / self.zoom)
        pdf_h = round(h / self.zoom)
        self.lbl_canvas_info.config(
            text=f"Template Page 1 ({pdf_w} x {pdf_h} pt)  |  {len(self.fields)} field(s) placed  |  Drag boxes to move, drag bottom-right corner to resize, Arrow keys to nudge"
        )

        self._draw_overlays()

    def _draw_empty_placeholder(self) -> None:
        """Draws an informative empty state card when no template is loaded."""
        w, h = 595, 842
        m = self.CANVAS_MARGIN
        self.canvas.create_rectangle(
            m,
            m,
            m + w,
            m + h,
            fill="#FFFFFF",
            outline="#94A3B8",
            dash=(6, 4),
            width=2,
        )
        self.canvas.create_text(
            m + w / 2,
            m + h / 2 - 20,
            text="No Template Loaded",
            fill=COLOR_PRIMARY_HEADER,
            font=("Segoe UI", 15, "bold"),
        )
        self.canvas.create_text(
            m + w / 2,
            m + h / 2 + 15,
            text="Click 'Load Template (PDF/Image)' in the top toolbar\nto open a report card or certificate template.",
            fill=COLOR_TEXT_SECONDARY,
            font=FONT_BODY,
            justify=tk.CENTER,
        )
        self.canvas.config(scrollregion=(0, 0, w + m * 2, h + m * 2))
        self._draw_overlays()

    def _format_field_badge(self, field: FieldNode) -> str:
        if field.field_type == FieldType.TEXT:
            col = f"{{{field.mapped_column}}}" if field.mapped_column else field.label
            return f"[Text: {col}]"
        if field.field_type == FieldType.IMAGE:
            return f"[Image: {field.label}]"
        return f"[QR: {field.mapped_column or field.label}]"

    def _draw_overlays(self) -> None:
        """Draws selection borders, badges, and resize handles for all fields on the active page."""
        self.canvas.delete("field_overlay")

        for field in self.fields:
            if field.page_index != self.page_index:
                continue

            x0, y0 = self.pdf_to_canvas_coords(field.x, field.y)
            x1, y1 = self.pdf_to_canvas_coords(field.x + field.width, field.y + field.height)
            is_selected = field.field_id == self.selected_field_id

            if field.field_type == FieldType.TEXT:
                base_color = COLOR_ACCENT
            elif field.field_type == FieldType.IMAGE:
                base_color = "#059669"
            else:
                base_color = "#D97706"

            border_color = "#DC2626" if is_selected else base_color
            border_width = 2 if is_selected else 1
            dash_pattern = (5, 3) if is_selected else (3, 3)

            # Bounding box rectangle
            self.canvas.create_rectangle(
                x0,
                y0,
                x1,
                y1,
                outline=border_color,
                width=border_width,
                dash=dash_pattern,
                tags=("field_overlay", f"box_{field.field_id}"),
            )

            # Top badge tag
            badge_text = self._format_field_badge(field)
            badge_h = 16
            badge_w = min(max(68, len(badge_text) * 6 + 10), max(80, int(x1 - x0)))
            self.canvas.create_rectangle(
                x0,
                max(2, y0 - badge_h),
                x0 + badge_w,
                y0,
                fill=border_color,
                outline=border_color,
                tags=("field_overlay", f"badge_{field.field_id}"),
            )
            self.canvas.create_text(
                x0 + 4,
                max(2, y0 - badge_h) + badge_h / 2,
                anchor=tk.W,
                text=badge_text,
                fill="#FFFFFF",
                font=("Segoe UI", 7, "bold"),
                tags=("field_overlay", f"badgetext_{field.field_id}"),
            )

            # Corner resize handle (bottom-right grip)
            hs = self.HANDLE_SIZE
            self.canvas.create_rectangle(
                x1 - hs,
                y1 - hs,
                x1,
                y1,
                fill=border_color,
                outline="#FFFFFF",
                width=1,
                tags=("field_overlay", f"handle_{field.field_id}"),
            )

    # --- Mouse & Keyboard Interaction Handlers ---

    def _hit_test_handle(self, cx: float, cy: float) -> Optional[FieldNode]:
        """Checks if (cx, cy) is inside any field's bottom-right resize handle."""
        hs = self.HANDLE_SIZE + 3
        for field in reversed(self.fields):
            if field.page_index != self.page_index:
                continue
            _, _ = self.pdf_to_canvas_coords(field.x, field.y)
            x1, y1 = self.pdf_to_canvas_coords(field.x + field.width, field.y + field.height)
            if (x1 - hs) <= cx <= (x1 + 3) and (y1 - hs) <= cy <= (y1 + 3):
                return field
        return None

    def _hit_test_field(self, cx: float, cy: float) -> Optional[FieldNode]:
        """Checks if (cx, cy) is inside any field's bounding box or badge."""
        for field in reversed(self.fields):
            if field.page_index != self.page_index:
                continue
            x0, y0 = self.pdf_to_canvas_coords(field.x, field.y)
            x1, y1 = self.pdf_to_canvas_coords(field.x + field.width, field.y + field.height)
            if x0 <= cx <= x1 and (y0 - 16) <= cy <= y1:
                return field
        return None

    def _on_mouse_down(self, event: tk.Event) -> None:
        self.canvas.focus_set()
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        # 1. Check resize grip first
        handle_field = self._hit_test_handle(cx, cy)
        if handle_field is not None:
            self.select_field(handle_field.field_id, notify=True)
            self._drag_mode = "resize"
            self._drag_start_canvas_x = cx
            self._drag_start_canvas_y = cy
            self._orig_field_w = handle_field.width
            self._orig_field_h = handle_field.height
            return

        # 2. Check field body / badge
        hit_field = self._hit_test_field(cx, cy)
        if hit_field is not None:
            self.select_field(hit_field.field_id, notify=True)
            self._drag_mode = "move"
            self._drag_start_canvas_x = cx
            self._drag_start_canvas_y = cy
            self._orig_field_x = hit_field.x
            self._orig_field_y = hit_field.y
            return

        # 3. Clicked empty canvas space
        self._drag_mode = None
        self.select_field(None, notify=True)

    def _on_mouse_drag(self, event: tk.Event) -> None:
        field = self.get_selected_field()
        if field is None or self._drag_mode is None:
            return

        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        dx_pdf = (cx - self._drag_start_canvas_x) / self.zoom
        dy_pdf = (cy - self._drag_start_canvas_y) / self.zoom

        max_pdf_w = self._page_pixel_width / self.zoom
        max_pdf_h = self._page_pixel_height / self.zoom

        if self._drag_mode == "move":
            new_x = max(0.0, min(self._orig_field_x + dx_pdf, max_pdf_w - field.width))
            new_y = max(0.0, min(self._orig_field_y + dy_pdf, max_pdf_h - field.height))
            field.x = round(new_x, 1)
            field.y = round(new_y, 1)
        elif self._drag_mode == "resize":
            new_w = max(24.0, min(self._orig_field_w + dx_pdf, max_pdf_w - field.x))
            new_h = max(14.0, min(self._orig_field_h + dy_pdf, max_pdf_h - field.y))
            field.width = round(new_w, 1)
            field.height = round(new_h, 1)

        self._draw_overlays()
        if self.on_field_modified:
            self.on_field_modified(field)

    def _on_mouse_up(self, _event: tk.Event) -> None:
        if self._drag_mode is not None:
            self._drag_mode = None
            self.refresh_canvas()
            field = self.get_selected_field()
            if field and self.on_field_modified:
                self.on_field_modified(field)

    def _nudge_selected(self, dx_pt: float, dy_pt: float) -> None:
        field = self.get_selected_field()
        if field is None:
            return
        max_pdf_w = self._page_pixel_width / self.zoom
        max_pdf_h = self._page_pixel_height / self.zoom

        field.x = round(max(0.0, min(field.x + dx_pt, max_pdf_w - field.width)), 1)
        field.y = round(max(0.0, min(field.y + dy_pt, max_pdf_h - field.height)), 1)
        self.refresh_canvas()
        if self.on_field_modified:
            self.on_field_modified(field)

    def _on_delete_key(self, _event: tk.Event) -> None:
        field = self.get_selected_field()
        if field is not None and self.on_field_deleted is not None:
            self.on_field_deleted(field)

    def _on_mouse_wheel(self, event: tk.Event) -> None:
        delta = -1 * int(event.delta / 120)
        self.canvas.yview_scroll(delta, "units")
