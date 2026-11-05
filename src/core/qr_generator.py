"""In-memory dynamic QR code PNG byte generator."""

from __future__ import annotations

import io
from PIL import Image
import qrcode
from qrcode.constants import ERROR_CORRECT_M


MAX_QR_PAYLOAD_CHARS = 1800


def generate_qr_png_bytes(payload: str, box_size: int = 8, border: int = 1) -> bytes:
    """Generates a crisp, high-contrast QR code PNG byte stream in memory."""
    effective_payload = str(payload).strip() if payload else "UNSPECIFIED"
    if len(effective_payload) > MAX_QR_PAYLOAD_CHARS:
        effective_payload = effective_payload[:MAX_QR_PAYLOAD_CHARS]

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=max(2, int(box_size)),
        border=max(0, int(border)),
    )
    qr.add_data(effective_payload)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white")
    if hasattr(qr_img, "get_image"):
        pil_img = qr_img.get_image().convert("RGBA")
    elif isinstance(qr_img, Image.Image):
        pil_img = qr_img.convert("RGBA")
    else:
        buf_tmp = io.BytesIO()
        qr_img.save(buf_tmp)
        buf_tmp.seek(0)
        pil_img = Image.open(buf_tmp).convert("RGBA")

    out_buf = io.BytesIO()
    pil_img.save(out_buf, format="PNG", optimize=True)
    return out_buf.getvalue()

