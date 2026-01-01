from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from PIL import Image, ImageDraw, ImageFont

from .models import ScreenSpec, TileType, compute_row_tile_type_id, compute_screen_resolution
from .palette import PALETTE, darken

@dataclass
class RenderOptions:
    # Text colors
    tile_text_rgb: Tuple[int, int, int] = (255, 255, 255)
    overlay_text_rgb: Tuple[int, int, int] = (255, 255, 255)
    outline_rgb: Tuple[int, int, int] = (0, 0, 0)

    # Outline thickness scales with min dimension
    outline_frac: float = 0.0035  # ~0.35% of min(W,H)

    # Font sizing
    tile_label_width_frac: float = 0.70  # relative to tile width
    overlay_title_frac: float = 0.18  # relative to min(W,H)
    overlay_sub_frac: float = 0.085   # relative to min(W,H)

    # Prefer system font; fallback to default
    font_name: str = "arial.ttf"

def _load_font(font_name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        font_name,
        "arial.ttf",
        "Arial.ttf",
        "calibri.ttf",
        "Calibri.ttf",
        "DejaVuSans.ttf",
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            continue
    return ImageFont.load_default()

def _fit_font_size_to_width(font_name: str, text: str, max_width: float, max_size: int, min_size: int = 10) -> int:
    """Return the largest font size that fits within max_width."""
    lo = min_size
    hi = max(min_size, max_size)
    best = min_size
    while lo <= hi:
        mid = (lo + hi) // 2
        font = _load_font(font_name, mid)
        bbox = font.getbbox(text)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return best

def _draw_centered_multiline(draw: ImageDraw.ImageDraw, xy, lines, fonts, fill, stroke_fill, stroke_width, line_spacing=0.2):
    """Draw multiple lines centered at xy (x,y) with per-line fonts."""
    x, y = xy
    # measure total height
    metrics = []
    total_h = 0
    max_w = 0
    for line, font in zip(lines, fonts):
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        metrics.append((w, h))
        total_h += h
        max_w = max(max_w, w)
    # add spacing
    total_h += int((len(lines) - 1) * metrics[0][1] * line_spacing) if len(lines) > 1 else 0

    # top-left start
    cur_y = y - total_h / 2
    for (line, font), (w, h) in zip(zip(lines, fonts), metrics):
        draw.text(
            (x - w / 2, cur_y),
            line,
            font=font,
            fill=fill,
            stroke_fill=stroke_fill,
            stroke_width=stroke_width,
        )
        cur_y += h + int(h * line_spacing)

def render_lineup_png(screen: ScreenSpec, tiles: Dict[str, TileType], opts: RenderOptions) -> Image.Image:
    total_w, total_h = compute_screen_resolution(screen, tiles)
    img = Image.new("RGB", (total_w, total_h), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    base_rgb = PALETTE.get(screen.base_color_name, PALETTE["Blue"])

    # Determine outline thickness
    stroke = max(1, int(min(total_w, total_h) * opts.outline_frac))

    # Draw tiles + per-tile text
    tile_index = 1
    y = 0
    for r in range(screen.rows):
        tile_type_id = compute_row_tile_type_id(screen, r)
        tile = tiles[tile_type_id]
        x = 0

        # Fonts scale to fit label width; number uses same size as label.
        max_label_w = tile.w_px * opts.tile_label_width_frac
        label_size = _fit_font_size_to_width(
            opts.font_name,
            screen.tile_label,
            max_label_w,
            max_size=int(tile.w_px),
        )
        label_font = _load_font(opts.font_name, label_size)
        num_font = label_font

        for c in range(screen.cols):
            # checkerboard by row/col so rows alternate (prevents full-row stripes)
            fill_rgb = darken(base_rgb, 0.75) if ((r + c) % 2 == 0) else base_rgb
            draw.rectangle([x, y, x + tile.w_px, y + tile.h_px], fill=fill_rgb)

            # Tile label + number (two lines centered)
            cx = x + tile.w_px / 2
            # Place label near top-ish and number near bottom-ish like examples
            label_y = y + tile.h_px * 0.22
            num_y = y + tile.h_px * 0.62

            # Centered text with no stroke for tile text (matches samples)
            # (You can add stroke here if desired.)
            lb = screen.tile_label
            nb = f"{tile_index:02d}"

            bbox_l = draw.textbbox((0, 0), lb, font=label_font)
            lw = bbox_l[2] - bbox_l[0]
            lh = bbox_l[3] - bbox_l[1]
            draw.text((cx - lw / 2, label_y - lh / 2), lb, font=label_font, fill=opts.tile_text_rgb)

            bbox_n = draw.textbbox((0, 0), nb, font=num_font)
            nw = bbox_n[2] - bbox_n[0]
            nh = bbox_n[3] - bbox_n[1]
            draw.text((cx - nw / 2, num_y - nh / 2), nb, font=num_font, fill=opts.tile_text_rgb)

            tile_index += 1
            x += tile.w_px
        y += tile.h_px

    # Center overlay (draw last, always)
    title = screen.screen_name
    subtitle = f"{total_w}x{total_h}"

    overlay_title_font = _load_font(opts.font_name, max(20, int(min(total_w, total_h) * opts.overlay_title_frac)))
    overlay_sub_font = _load_font(opts.font_name, max(16, int(min(total_w, total_h) * opts.overlay_sub_frac)))

    _draw_centered_multiline(
        draw,
        (total_w / 2, total_h / 2),
        [title, subtitle],
        [overlay_title_font, overlay_sub_font],
        fill=opts.overlay_text_rgb,
        stroke_fill=opts.outline_rgb,
        stroke_width=stroke,
        line_spacing=0.25,
    )

    return img
