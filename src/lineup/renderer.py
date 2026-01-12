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

    # Overlay options
    show_overlay: bool = True
    circlex_grid_black_bg: bool = False

    # Optional branding overlay (PNG with alpha)
    branding_image: Image.Image | None = None

    lineup_type: str = "RGB"

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

def _fit_image_to_canvas(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
    if img.width <= max_w and img.height <= max_h:
        return img
    scale = min(max_w / img.width, max_h / img.height)
    new_w = max(1, int(round(img.width * scale)))
    new_h = max(1, int(round(img.height * scale)))
    return img.resize((new_w, new_h), Image.LANCZOS)

def _compute_step_heights(total_h: int, steps: int) -> list[int]:
    base = total_h // steps
    remainder = total_h % steps
    return [base + (1 if i < remainder else 0) for i in range(steps)]

def _greyscale_value(step_idx: int, steps: int) -> int:
    if steps <= 1:
        return 0
    return int(round(255 * step_idx / (steps - 1)))


def render_lineup_png(screen: ScreenSpec, tiles: Dict[str, TileType], opts: RenderOptions) -> Image.Image:
    if opts.lineup_type == "CircleXGrid":
        if screen.expected_w_px is None or screen.expected_h_px is None:
            raise ValueError("Circle X Grid requires expected pixel width/height.")
        total_w, total_h = screen.expected_w_px, screen.expected_h_px
    elif opts.lineup_type == "GreyscaleSteps" and (
        screen.expected_w_px is not None and screen.expected_h_px is not None
    ):
        total_w, total_h = screen.expected_w_px, screen.expected_h_px
    else:
        total_w, total_h = compute_screen_resolution(screen, tiles)
    img = Image.new("RGB", (total_w, total_h), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Determine outline thickness
    stroke = max(1, int(min(total_w, total_h) * opts.outline_frac))

    if opts.lineup_type == "CircleXGrid":
        if opts.circlex_grid_black_bg:
            base_rgb = (0, 0, 0)
        else:
            base_rgb = _resolve_color(screen.base_color_name)
        draw.rectangle([0, 0, total_w, total_h], fill=base_rgb)

        grid_spacing = 100
        _draw_grid(
            draw,
            total_w,
            total_h,
            grid_spacing,
            color=(255, 255, 255),
            line_width=2,
        )
        draw.rectangle([0, 0, total_w - 1, total_h - 1], outline=(255, 255, 255), width=2)
        _draw_circle_x(
            draw,
            total_w,
            total_h,
            color=(255, 255, 255),
            line_width=10,
        )
    elif opts.lineup_type == "GreyscaleSteps":
        steps = 11
        heights = _compute_step_heights(total_h, steps)
        y = 0
        for i, h in enumerate(heights):
            v = _greyscale_value(i, steps)
            draw.rectangle([0, y, total_w, y + h], fill=(v, v, v))
            y += h
    else:
        dual_colors = _parse_dual_colors(screen.base_color_name)
        base_rgb = _resolve_color(screen.base_color_name)

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
            label_size = max(10, int(label_size * 0.8))
            label_font = _load_font(opts.font_name, label_size)
            num_font = label_font

            for c in range(screen.cols):
                # checkerboard by row/col so rows alternate (prevents full-row stripes)
                if dual_colors:
                    fill_rgb = dual_colors[0] if ((r + c) % 2 == 0) else dual_colors[1]
                else:
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

    if opts.branding_image is not None:
        branding = opts.branding_image
        if branding.mode != "RGBA":
            branding = branding.convert("RGBA")
        branding = _fit_image_to_canvas(branding, total_w, total_h)
        img.paste(branding, (0, total_h - branding.height), branding)

    if opts.show_overlay:
        # Center overlay (draw last)
        title = screen.screen_name
        subtitle = f"{total_w}x{total_h}"

        overlay_max_w = total_w * 0.85
        overlay_title_size = _fit_font_size_to_width(
            opts.font_name,
            title,
            overlay_max_w,
            max_size=max(20, int(min(total_w, total_h) * opts.overlay_title_frac)),
            min_size=20,
        )
        overlay_sub_size = _fit_font_size_to_width(
            opts.font_name,
            subtitle,
            overlay_max_w,
            max_size=max(16, int(min(total_w, total_h) * opts.overlay_sub_frac)),
            min_size=16,
        )
        overlay_title_font = _load_font(opts.font_name, overlay_title_size)
        overlay_sub_font = _load_font(opts.font_name, overlay_sub_size)

        if opts.lineup_type == "CircleXGrid":
            _draw_centered_split_lines(
                draw,
                (total_w / 2, total_h / 2),
                title,
                subtitle,
                overlay_title_font,
                overlay_sub_font,
                fill=opts.overlay_text_rgb,
                stroke_fill=opts.outline_rgb,
                stroke_width=stroke,
                gap=max(int(min(total_w, total_h) * 0.08), int(overlay_title_size * 1.2)),
            )
        else:
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

def _parse_dual_colors(name: str) -> tuple[tuple[int, int, int], tuple[int, int, int]] | None:
    if "," not in name:
        return None
    parts = [part.strip() for part in name.split(",")]
    if len(parts) != 2:
        return None
    if parts[0] not in PALETTE or parts[1] not in PALETTE:
        return None
    return (PALETTE[parts[0]], PALETTE[parts[1]])

def _parse_hex_color(value: str) -> tuple[int, int, int] | None:
    raw = value.strip()
    if raw.startswith("#"):
        raw = raw[1:]
    if len(raw) != 6:
        return None
    try:
        r = int(raw[0:2], 16)
        g = int(raw[2:4], 16)
        b = int(raw[4:6], 16)
    except ValueError:
        return None
    return (r, g, b)

def _resolve_color(name: str) -> Tuple[int, int, int]:
    hex_rgb = _parse_hex_color(name)
    if hex_rgb:
        return hex_rgb
    return PALETTE.get(name, PALETTE["Blue"])

def _draw_centered_split_lines(
    draw: ImageDraw.ImageDraw,
    xy,
    top_line: str,
    bottom_line: str,
    top_font: ImageFont.ImageFont,
    bottom_font: ImageFont.ImageFont,
    fill,
    stroke_fill,
    stroke_width,
    gap: int,
) -> None:
    x, y = xy
    top_bbox = draw.textbbox((0, 0), top_line, font=top_font, stroke_width=stroke_width)
    top_w = top_bbox[2] - top_bbox[0]
    top_h = top_bbox[3] - top_bbox[1]

    bottom_bbox = draw.textbbox((0, 0), bottom_line, font=bottom_font, stroke_width=stroke_width)
    bottom_w = bottom_bbox[2] - bottom_bbox[0]
    bottom_h = bottom_bbox[3] - bottom_bbox[1]

    top_y = y - gap / 2 - top_h
    bottom_y = y + gap / 2

    draw.text(
        (x - top_w / 2, top_y),
        top_line,
        font=top_font,
        fill=fill,
        stroke_fill=stroke_fill,
        stroke_width=stroke_width,
    )
    draw.text(
        (x - bottom_w / 2, bottom_y),
        bottom_line,
        font=bottom_font,
        fill=fill,
        stroke_fill=stroke_fill,
        stroke_width=stroke_width,
    )

def _draw_grid(
    draw: ImageDraw.ImageDraw,
    total_w: int,
    total_h: int,
    spacing: int,
    color: Tuple[int, int, int],
    line_width: int,
) -> None:
    if spacing <= 0:
        return

    remainder = total_h % spacing
    y_offset = remainder // 2

    x = 0
    while x <= total_w:
        draw.line((x, 0, x, total_h), fill=color, width=line_width)
        x += spacing

    y = -y_offset
    while y <= total_h:
        draw.line((0, y, total_w, y), fill=color, width=line_width)
        y += spacing

def _draw_circle_x(
    draw: ImageDraw.ImageDraw,
    total_w: int,
    total_h: int,
    color: Tuple[int, int, int],
    line_width: int,
) -> None:
    cx = total_w / 2
    cy = total_h / 2
    radius = int(round(min(total_w, total_h) * 0.45))
    bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
    draw.ellipse(bbox, outline=color, width=line_width)
    draw.line((0, 0, total_w, total_h), fill=color, width=line_width)
    draw.line((0, total_h, total_w, 0), fill=color, width=line_width)
