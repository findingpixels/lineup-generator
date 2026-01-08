from __future__ import annotations

import csv
import json
import re
from html import unescape
from io import StringIO
from urllib.parse import quote, urlparse
from urllib.request import urlopen

from .models import ScreenSpec, TileType

COL_SCREEN_NAME = 2   # C (PROD LABEL)
COL_TILE_LABEL = 3    # D (DELIVERY LABEL)
COL_BASE_COLOR = 4    # E (Lineup Color)
COL_EXPECTED_W = 5    # F (PIXELS W)
COL_EXPECTED_H = 6    # G (PIXELS H)
COL_COLS = 13         # N (TILE LAYOUT W)
COL_ROWS = 14         # O (TILE LAYOUT H)
COL_SECONDARY_PLACEMENT = 16  # Q (half/alt tile position)
COL_TILE_W = 36       # AK (Single Tile Pixel Width)
COL_TILE_H = 37       # AL (Single Tile Pixel Height)
COL_LED_FLAG = 1      # B (SCREEN COUNT)


def _extract_sheet_id(sheet_url: str) -> str:
    parts = urlparse(sheet_url)
    path = parts.path or ""
    marker = "/spreadsheets/d/"
    if marker not in path:
        raise ValueError("Google Sheet URL is missing the spreadsheet ID.")
    sheet_id = path.split(marker, 1)[1].split("/", 1)[0]
    if not sheet_id:
        raise ValueError("Google Sheet URL is missing the spreadsheet ID.")
    return sheet_id


def fetch_google_sheet_csv(sheet_url: str, sheet_name: str | None = None) -> str:
    sheet_id = _extract_sheet_id(sheet_url)
    if sheet_name:
        sheet_param = quote(sheet_name)
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_param}"
    else:
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

    with urlopen(csv_url) as resp:
        data = resp.read()
    return data.decode("utf-8")


def fetch_google_sheet_names(sheet_url: str) -> list[str]:
    sheet_id = _extract_sheet_id(sheet_url)
    edit_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"

    with urlopen(edit_url) as resp:
        html_text = resp.read().decode("utf-8", errors="replace")

    patterns = (
        r'"sheetId"\s*:\s*\d+\s*,\s*"name"\s*:\s*"([^"]+)"',
        r'"sheetId"\s*:\s*\d+\s*,\s*"title"\s*:\s*"([^"]+)"',
    )
    names: list[str] = []
    for pattern in patterns:
        for match in re.findall(pattern, html_text):
            try:
                decoded = json.loads(f'"{match}"')
            except json.JSONDecodeError:
                decoded = unescape(match)
            if decoded not in names:
                names.append(decoded)

    if names:
        return names

    feed_url = f"https://spreadsheets.google.com/feeds/worksheets/{sheet_id}/public/full?alt=json"
    try:
        with urlopen(feed_url) as resp:
            feed_text = resp.read().decode("utf-8", errors="replace")
        feed = json.loads(feed_text)
        entries = feed.get("feed", {}).get("entry", [])
        for entry in entries:
            title = entry.get("title", {}).get("$t")
            if title and title not in names:
                names.append(title)
    except Exception:
        return names

    return names


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value if value != "" else None


def _get_cell(row: list[str], idx: int) -> str | None:
    if idx >= len(row):
        return None
    return _clean(row[idx])


def _parse_int(value: str, label: str, row_num: int) -> int:
    try:
        return int(float(value))
    except ValueError as exc:
        raise ValueError(f"Row {row_num}: invalid {label} '{value}'") from exc


def _parse_float(value: str, label: str, row_num: int) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Row {row_num}: invalid {label} '{value}'") from exc


def _normalize_placement(value: str | None) -> str | None:
    if not value:
        return None
    val = value.strip().lower()
    if val in {"top", "bottom"}:
        return val
    return None


def _is_number(value: str | None) -> bool:
    if value is None:
        return False
    try:
        float(value)
    except ValueError:
        return False
    return True


def load_screens_from_google_csv(text: str) -> tuple[dict[str, TileType], list[ScreenSpec]]:
    reader = csv.reader(StringIO(text))
    tiles: dict[str, TileType] = {}
    screens: list[ScreenSpec] = []

    for row_num, row in enumerate(reader, start=1):
        if not _get_cell(row, COL_TILE_LABEL):
            continue

        cols_raw = _get_cell(row, COL_COLS)
        rows_raw = _get_cell(row, COL_ROWS)
        if not _is_number(cols_raw) or not _is_number(rows_raw):
            continue

        w_raw = _get_cell(row, COL_TILE_W)
        h_raw = _get_cell(row, COL_TILE_H)
        if not _is_number(w_raw) or not _is_number(h_raw):
            continue

        cols = _parse_int(cols_raw, "cols", row_num)
        rows_float = _parse_float(rows_raw, "rows", row_num)
        w_px = _parse_int(w_raw, "tile w_px", row_num)
        h_px = _parse_int(h_raw, "tile h_px", row_num)

        screen_name = _get_cell(row, COL_SCREEN_NAME) or "SCREEN"
        tile_label = _get_cell(row, COL_TILE_LABEL) or screen_name
        base_color_name = _get_cell(row, COL_BASE_COLOR) or "Blue"
        expected_w = _get_cell(row, COL_EXPECTED_W)
        expected_h = _get_cell(row, COL_EXPECTED_H)

        default_tile_type_id = f"{w_px}x{h_px}"
        if default_tile_type_id not in tiles:
            tiles[default_tile_type_id] = TileType(
                tile_type_id=default_tile_type_id,
                w_px=w_px,
                h_px=h_px,
            )

        secondary_tile_type_id = None
        secondary_rows = 0
        secondary_placement = None

        full_rows = int(rows_float)
        has_half_row = rows_float != full_rows
        total_rows = full_rows
        if has_half_row:
            total_rows = full_rows + 1
            secondary_rows = 1
            secondary_placement = _normalize_placement(_get_cell(row, COL_SECONDARY_PLACEMENT)) or "bottom"
            half_h = h_px // 2
            if half_h <= 0:
                raise ValueError(f"Row {row_num}: invalid half-height for tile h_px {h_px}")
            secondary_tile_type_id = f"{w_px}x{half_h}"
            if secondary_tile_type_id not in tiles:
                tiles[secondary_tile_type_id] = TileType(
                    tile_type_id=secondary_tile_type_id,
                    w_px=w_px,
                    h_px=half_h,
                )

        screens.append(
            ScreenSpec(
                screen_name=screen_name,
                tile_label=tile_label,
                rows=total_rows,
                cols=cols,
                default_tile_type_id=default_tile_type_id,
                secondary_tile_type_id=secondary_tile_type_id,
                secondary_placement=secondary_placement,  # type: ignore[arg-type]
                secondary_rows=secondary_rows,
                base_color_name=base_color_name,
                expected_w_px=_parse_int(expected_w, "expected_w_px", row_num) if expected_w else None,
                expected_h_px=_parse_int(expected_h, "expected_h_px", row_num) if expected_h else None,
            )
        )

    if not screens:
        raise ValueError("No LED screens found in the sheet data.")

    return tiles, screens
