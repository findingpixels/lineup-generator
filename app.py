import io
import sys
import string
from pathlib import Path

import streamlit as st
from PIL import Image

from src.lineup.io_google import (
    fetch_google_sheet_csv,
    fetch_google_sheet_names,
    load_screens_from_google_csv,
)
from src.lineup.renderer import RenderOptions, render_lineup_png
from src.lineup.models import ScreenSpec, TileType, validate_screen_against_tiles
from src.lineup.palette import PALETTE

st.set_page_config(page_title="Lineup Guide Generator", layout="wide")

st.title("Lineup Guide Generator")

st.markdown(
    "Load a **screen notes CSV**, connect a Google Sheet, or enter details manually. "
    "Then select a screen, preview it, and export a PNG."
)

def _normalize_hex_color(value: str) -> str | None:
    raw = value.strip()
    if not raw:
        return None
    if raw.startswith("#"):
        raw = raw[1:]
    if len(raw) != 6 or any(ch not in string.hexdigits for ch in raw):
        return None
    return f"#{raw.upper()}"
st.markdown(
    """
    <style>
    button[aria-label="Refresh"] {
        height: 3.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.subheader("Data Source")
data_source = st.radio("Data source", ["Google Sheets", "Upload CSV", "Manual Entry"], horizontal=True, label_visibility="hidden")


tiles = None
screens = None

if data_source == "Upload CSV":
    sheet_file = st.file_uploader("Screen notes CSV", type=["csv"], key="screen_notes")

    if not sheet_file:
        st.info("Upload the screen notes CSV to begin.")
        st.stop()

    sheet_text = sheet_file.getvalue().decode("utf-8")
    try:
        tiles, screens = load_screens_from_google_csv(sheet_text)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
elif data_source == "Google Sheets":
    st.caption("Sheets must be shared as 'Anyone with the link' or public.")
    url_col, refresh_col = st.columns([6, 1], vertical_alignment="bottom")
    with url_col:
        sheet_url = st.text_input("Google Sheet URL")
    with refresh_col:
        refresh_clicked = st.button("Refresh", use_container_width=True)
    sheet_name = None

    @st.cache_data(show_spinner=False)
    def _get_sheet_names(url: str) -> list[str]:
        return fetch_google_sheet_names(url)

    if refresh_clicked:
        st.cache_data.clear()
        st.rerun()

    if not sheet_url:
        st.info("Paste the Google Sheet URL to begin.")
        st.stop()

    sheet_name = st.text_input(
        "To use a different sheet besides the first sheet, enter the sheet name here.",
        value="",
    ).strip() or None

    try:
        sheet_text = fetch_google_sheet_csv(sheet_url, sheet_name=sheet_name)
        tiles, screens = load_screens_from_google_csv(sheet_text)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
    except OSError as exc:
        st.error(f"Failed to load Google Sheet: {exc}")
        st.stop()
else:
    st.header("Manual Entry")
    st.caption("Enter screen details directly (no sheet or CSV required).")

    st.markdown("### Screen")
    screen_col1, screen_col2 = st.columns(2)
    with screen_col1:
        screen_name = st.text_input("Screen name", value="SCREEN").strip() or "SCREEN"
        tile_label = st.text_input("Delivery label", value=screen_name).strip() or screen_name
        palette_names = list(PALETTE.keys())
        color_col, hex_col = st.columns([2, 1])
        with color_col:
            base_color_name = st.selectbox(
                "Lineup Color",
                options=palette_names,
                index=palette_names.index("Blue") if "Blue" in palette_names else 0,
                help="Pick a palette color.",
            )
        with hex_col:
            hex_color_input = st.text_input("Hex color", value="", placeholder="#RRGGBB").strip()
        base_color_hex = _normalize_hex_color(hex_color_input)
        if base_color_hex:
            base_color_name = base_color_hex

    with screen_col2:
        expected_w_px = st.number_input("Screen Width (px)", min_value=0, value=0, step=1)
        expected_h_px = st.number_input("Screen Height (px)", min_value=0, value=0, step=1)

    st.markdown("### LED")
    led_col1, led_col2 = st.columns(2)
    with led_col1:
        cols = st.number_input("Tile columns", min_value=0.0, value=0.0, step=0.5, format="%.1f")
        rows = st.number_input("Tile rows", min_value=0.0, value=0.0, step=0.5, format="%.1f")
    with led_col2:
        tile_w_px = st.number_input("Tile width pixels", min_value=0, value=0, step=1)
        tile_h_px = st.number_input("Tile height pixels", min_value=0, value=0, step=1)

    tiles = {}
    rows_float = float(rows)
    cols_float = float(cols)
    full_rows = int(rows_float)
    has_half_row = abs(rows_float - (full_rows + 0.5)) < 1e-6
    total_rows = full_rows + 1 if has_half_row else full_rows
    cols_int = int(round(cols_float))
    if cols_float > 0 and abs(cols_float - cols_int) > 1e-6:
        st.warning("Tile columns must be a whole number. Rounding to the nearest column count.")

    default_tile_type_id = f"{tile_w_px}x{tile_h_px}" if tile_w_px > 0 and tile_h_px > 0 else "Manual"
    if tile_w_px > 0 and tile_h_px > 0:
        tiles[default_tile_type_id] = TileType(
            tile_type_id=default_tile_type_id,
            w_px=int(tile_w_px),
            h_px=int(tile_h_px),
        )

    secondary_tile_type_id = None
    secondary_placement = None
    secondary_rows = 0
    if has_half_row and tile_w_px > 0 and tile_h_px > 0:
        half_h = int(tile_h_px // 2)
        if half_h > 0:
            secondary_tile_type_id = f"{default_tile_type_id}_HALF"
            secondary_placement = "bottom"
            secondary_rows = 1
            tiles[secondary_tile_type_id] = TileType(
                tile_type_id=secondary_tile_type_id,
                w_px=int(tile_w_px),
                h_px=half_h,
            )

    screens = [
        ScreenSpec(
            screen_name=screen_name,
            tile_label=tile_label,
            rows=max(1, int(total_rows)),
            cols=max(1, int(cols_int)),
            default_tile_type_id=default_tile_type_id,
            secondary_tile_type_id=secondary_tile_type_id,
            secondary_placement=secondary_placement,  # type: ignore[arg-type]
            secondary_rows=int(secondary_rows),
            base_color_name=base_color_name,
            expected_w_px=int(expected_w_px) if expected_w_px else None,
            expected_h_px=int(expected_h_px) if expected_h_px else None,
        )
    ]


st.subheader("Lineup Type")
lineup_type = st.radio(
    "Lineup Type",
    ["RGB LED Tiles", "Greyscale Steps", "Circle X Grid"],
    horizontal=True,
    label_visibility="hidden",
)
lineup_type_map = {
    "RGB LED Tiles": "RGB",
    "Greyscale Steps": "GreyscaleSteps",
    "Circle X Grid": "CircleXGrid",
}
lineup_type_label = lineup_type_map[lineup_type]

def _has_tile_specs(spec) -> bool:
    return spec.default_tile_type_id in tiles

def _has_expected_size(spec) -> bool:
    return (spec.expected_w_px or 0) > 0 and (spec.expected_h_px or 0) > 0

def _has_delivery_label(spec) -> bool:
    return bool(spec.tile_label)

if lineup_type_label == "CircleXGrid":
    eligible_screens = [s for s in screens if _has_expected_size(s) and _has_delivery_label(s)]
    if not eligible_screens:
        st.error("No screens with delivery label + pixel width/height (columns D/F/G).")
        st.stop()
elif lineup_type_label == "GreyscaleSteps":
    eligible_screens = [
        s for s in screens if _has_delivery_label(s) and (_has_tile_specs(s) or _has_expected_size(s))
    ]
    if not eligible_screens:
        st.error("No screens with delivery label + either tile specs or pixel width/height.")
        st.stop()
else:
    eligible_screens = [s for s in screens if _has_tile_specs(s)]
    if not eligible_screens:
        st.error("No screens with LED tile specs (cols/rows + tile pixel size).")
        st.stop()

screen_names = [s.screen_name for s in eligible_screens]
selected = st.selectbox("Select a screen", screen_names)
screen = next(s for s in eligible_screens if s.screen_name == selected)

if lineup_type_label == "CircleXGrid":
    warnings = []
    if not _has_delivery_label(screen):
        warnings.append("Delivery label (column D) is required.")
    if not _has_expected_size(screen):
        warnings.append("Pixels width/height (columns F/G) are required for Circle X Grid.")
elif lineup_type_label == "GreyscaleSteps":
    warnings = []
    if not _has_delivery_label(screen):
        warnings.append("Delivery label (column D) is required.")
    if not (_has_tile_specs(screen) or _has_expected_size(screen)):
        warnings.append("Greyscale needs either tile specs or pixels width/height.")
else:
    warnings = validate_screen_against_tiles(screen, tiles)

if warnings:
    st.warning("\n".join(f"- {w}" for w in warnings))

if lineup_type_label == "RGB" and screen.default_tile_type_id not in tiles:
    st.error("RGB requires LED tile specs (cols/rows + tile pixel size).")
    st.stop()
if lineup_type_label == "GreyscaleSteps" and not (_has_tile_specs(screen) or _has_expected_size(screen)):
    st.error("Greyscale requires tile specs or pixel width/height.")
    st.stop()

if lineup_type_label in {"CircleXGrid", "GreyscaleSteps"} and warnings:
    st.stop()

st.header("Preview")

# Overlay toggle (defaults on)
show_overlay = st.toggle("Overlay (screen name + resolution)", value=True)
circlex_black_bg = False
if lineup_type_label == "CircleXGrid":
    circlex_black_bg = st.toggle("Circle X Grid: Override black background", value=False)
branding_file = st.file_uploader("Branding PNG (optional)", type=["png"], key="branding_png")
branding_image = None
if branding_file:
    try:
        branding_image = Image.open(branding_file).convert("RGBA")
    except OSError:
        st.error("Failed to load branding PNG.")
        st.stop()
    if branding_image.size != (1000, 1000):
        st.caption("Branding PNG is not 1000x1000; it will be used at its native size (scaled to fit if needed).")

# Render preview in-memory
opts = RenderOptions(
    show_overlay=show_overlay,
    lineup_type=lineup_type_label,
    branding_image=branding_image,
    circlex_grid_black_bg=circlex_black_bg,
)
img = render_lineup_png(screen, tiles, opts)

st.image(img, caption=f"{screen.screen_name} ({img.width}x{img.height})", use_container_width=True)

st.header("Export")

def _get_default_output_dir() -> Path:
    if getattr(sys, "frozen", False):
        exe_path = Path(sys.executable).resolve()
        if sys.platform == "darwin" and "Contents" in exe_path.parts:
            # Move outside the .app bundle.
            try:
                app_bundle = exe_path.parents[2]
                return app_bundle.parent / "outputs"
            except IndexError:
                pass
        return exe_path.parent / "outputs"
    return Path.cwd() / "outputs"

default_out_dir = _get_default_output_dir()
version = st.text_input("Version", value="v001").strip() or "v001"
overlay_suffix = "_OV" if show_overlay else ""
if lineup_type_label == "GreyscaleSteps":
    file_prefix = "GREY"
elif lineup_type_label == "CircleXGrid":
    file_prefix = "CircleX"
else:
    file_prefix = lineup_type_label
default_out_name = f"{file_prefix}{overlay_suffix}_{screen.tile_label}_{version}.png"
out_name = st.text_input("Output Filename", value=default_out_name)
out_dir = st.text_input("Output Folder", value=str(default_out_dir))
out_path_dir = Path(out_dir)
if not out_path_dir.is_absolute():
    out_path_dir = default_out_dir.parent / out_path_dir
out_path_dir.mkdir(parents=True, exist_ok=True)

btn_col1, btn_col2, _btn_spacer = st.columns([1, 1, 8])

if btn_col1.button("Export PNG"):
    out_path = out_path_dir / out_name
    img.save(out_path, format="PNG")
    st.success(f"Saved: {out_path.resolve()}")

    # Offer download in browser too
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    st.download_button(
        label="Download PNG",
        data=buf.getvalue(),
        file_name=out_name,
        mime="image/png",
    )

if btn_col2.button("Export ALL PNGs"):
    progress = st.progress(0)
    total = len(eligible_screens)
    for idx, scr in enumerate(eligible_screens, start=1):
        out_path = out_path_dir / f"{file_prefix}{overlay_suffix}_{scr.tile_label}_{version}.png"
        render_lineup_png(scr, tiles, opts).save(out_path, format="PNG")
        progress.progress(idx / total)
    st.success(f"Saved {total} files to: {out_path_dir.resolve()}")
