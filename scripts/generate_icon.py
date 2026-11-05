"""Programmatic multi-resolution Indigo & Gold document-badge icon generator."""

from pathlib import Path
from PIL import Image, ImageDraw


def draw_icon_frame(size: int) -> Image.Image:
    """Draws a crisp document-badge icon at the requested square pixel resolution."""
    scale = 4
    canvas_size = size * scale
    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer rounded badge background (Deep Slate-Indigo #1E1B4B)
    pad = int(canvas_size * 0.06)
    radius = int(canvas_size * 0.22)
    draw.rounded_rectangle(
        [pad, pad, canvas_size - pad, canvas_size - pad],
        radius=radius,
        fill=(30, 27, 75, 255),
        outline=(79, 70, 229, 255),
        width=max(2, int(canvas_size * 0.03)),
    )

    # Document sheet inside badge (Crisp Ivory/White #F8FAFC)
    doc_left = int(canvas_size * 0.23)
    doc_top = int(canvas_size * 0.17)
    doc_right = int(canvas_size * 0.77)
    doc_bottom = int(canvas_size * 0.83)
    doc_radius = int(canvas_size * 0.06)
    draw.rounded_rectangle(
        [doc_left, doc_top, doc_right, doc_bottom],
        radius=doc_radius,
        fill=(248, 250, 252, 255),
    )

    # Top header band on document (Vibrant Indigo #4F46E5)
    band_bottom = int(canvas_size * 0.31)
    draw.rounded_rectangle(
        [doc_left, doc_top, doc_right, band_bottom],
        radius=doc_radius,
        fill=(79, 70, 229, 255),
    )
    draw.rectangle(
        [doc_left, int((doc_top + band_bottom) / 2), doc_right, band_bottom],
        fill=(79, 70, 229, 255),
    )

    # Variable field lines on the document
    line_left = int(canvas_size * 0.30)
    line_right = int(canvas_size * 0.70)
    line_h = max(2, int(canvas_size * 0.045))

    for idx, y_frac in enumerate([0.40, 0.51, 0.62]):
        y0 = int(canvas_size * y_frac)
        y1 = y0 + line_h
        end_x = line_right if idx < 2 else int(canvas_size * 0.56)
        color = (51, 65, 85, 255) if idx != 0 else (79, 70, 229, 255)
        draw.rounded_rectangle(
            [line_left, y0, end_x, y1],
            radius=max(1, line_h // 2),
            fill=color,
        )

    # Gold seal / variable injection badge on bottom right (#F59E0B / #FBBF24)
    seal_cx = int(canvas_size * 0.68)
    seal_cy = int(canvas_size * 0.70)
    seal_r = int(canvas_size * 0.14)
    draw.ellipse(
        [seal_cx - seal_r, seal_cy - seal_r, seal_cx + seal_r, seal_cy + seal_r],
        fill=(245, 158, 11, 255),
        outline=(254, 243, 199, 255),
        width=max(2, int(canvas_size * 0.025)),
    )

    # Inner gold star / core dot
    inner_r = int(seal_r * 0.45)
    draw.ellipse(
        [seal_cx - inner_r, seal_cy - inner_r, seal_cx + inner_r, seal_cy + inner_r],
        fill=(254, 243, 199, 255),
    )

    return img.resize((size, size), Image.Resampling.LANCZOS)


def generate_app_icon(output_path: str | Path | None = None) -> Path:
    """Generates the multi-resolution Windows .ico file at assets/app_icon.ico."""
    root_dir = Path(__file__).resolve().parent.parent
    target = Path(output_path) if output_path else (root_dir / "assets" / "app_icon.ico")
    target.parent.mkdir(parents=True, exist_ok=True)

    sizes = [16, 32, 48, 256]
    frames = [draw_icon_frame(s) for s in sizes]
    # Save using the largest frame as primary and include all sizes
    frames[-1].save(
        target,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=frames[:-1],
    )
    return target


if __name__ == "__main__":
    icon_file = generate_app_icon()
    print(f"Generated multi-resolution icon at: {icon_file} ({icon_file.stat().st_size} bytes)")

