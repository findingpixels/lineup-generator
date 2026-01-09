import io
import sys
from pathlib import Path

import streamlit as st
from PIL import Image

from src.lineup.io_csv import load_screens_csv, load_tiles_csv
from src.lineup.io_google import (
    fetch_google_sheet_csv,
    fetch_google_sheet_names,
    load_screens_from_google_csv,
)
from src.lineup.renderer import RenderOptions, render_lineup_png
from src.lineup.models import validate_screen_against_tiles

st.set_page_config(page_title="Lineup Guide Generator", layout="wide")

st.title("Lineup Guide Generator")

st.markdown(
    "Load a **screen notes CSV** (or connect a Google Sheet), select a screen, preview it, then export a PNG."
)
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

data_source = st.radio("Data source", ["Google Sheets", "Upload CSV"], horizontal=True)

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
else:
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

screen_names = [s.screen_name for s in screens]
selected = st.selectbox("Select a screen", screen_names)
screen = next(s for s in screens if s.screen_name == selected)

warnings = validate_screen_against_tiles(screen, tiles)

if warnings:
    st.warning("\n".join(f"- {w}" for w in warnings))

lineup_type = st.radio(
    "Lineup type",
    ["RGB", "Greyscale (coming soon)", "Circle X (coming soon)", "Circle X Grid (coming soon)"],
    horizontal=True,
)
lineup_type_map = {
    "RGB": "RGB",
    "Greyscale (coming soon)": "Grey",
    "Circle X (coming soon)": "CircleX",
    "Circle X Grid (coming soon)": "CircleXGrid",
}
lineup_type_label = lineup_type_map[lineup_type]
if lineup_type != "RGB":
    st.info("Only RGB lineups are available right now.")
    st.stop()

st.subheader("Preview")

# Overlay toggle (defaults on)
show_overlay = st.toggle("Overlay (screen name + resolution)", value=True)

# Render preview in-memory
opts = RenderOptions(show_overlay=show_overlay)
img = render_lineup_png(screen, tiles, opts)

st.image(img, caption=f"{screen.screen_name} ({img.width}x{img.height})", use_container_width=True)

st.subheader("Export")

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
default_out_name = f"{lineup_type_label}{overlay_suffix}_{screen.tile_label}_{version}.png"
out_name = st.text_input("Output filename", value=default_out_name)
out_dir = st.text_input("Output folder", value=str(default_out_dir))
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
    total = len(screens)
    for idx, scr in enumerate(screens, start=1):
        out_path = out_path_dir / f"{lineup_type_label}{overlay_suffix}_{scr.tile_label}_{version}.png"
        render_lineup_png(scr, tiles, opts).save(out_path, format="PNG")
        progress.progress(idx / total)
    st.success(f"Saved {total} files to: {out_path_dir.resolve()}")
