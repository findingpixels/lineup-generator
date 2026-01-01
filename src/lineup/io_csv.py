from __future__ import annotations

import csv
from io import StringIO
from typing import List, Dict, Optional

from .models import ScreenSpec, TileType

def _clean(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s2 = str(s).strip()
    return s2 if s2 != "" else None

def load_tiles_csv(text: str) -> Dict[str, TileType]:
    reader = csv.DictReader(StringIO(text))
    tiles: Dict[str, TileType] = {}
    for row in reader:
        tile_type_id = _clean(row.get("tile_type_id")) or _clean(row.get("tile_type")) or _clean(row.get("id"))
        if not tile_type_id:
            raise ValueError("tiles.csv is missing tile_type_id")
        w_px = int(row["w_px"])
        h_px = int(row["h_px"])
        tiles[tile_type_id] = TileType(tile_type_id=tile_type_id, w_px=w_px, h_px=h_px)
    return tiles

def load_screens_csv(text: str) -> List[ScreenSpec]:
    reader = csv.DictReader(StringIO(text))
    screens: List[ScreenSpec] = []
    for row in reader:
        screen_name = _clean(row.get("screen_name"))
        tile_label = _clean(row.get("tile_label")) or screen_name or ""
        rows = int(row["rows"])
        cols = int(row["cols"])
        default_tile_type_id = _clean(row.get("default_tile_type_id")) or ""
        secondary_tile_type_id = _clean(row.get("secondary_tile_type_id"))
        secondary_placement = _clean(row.get("secondary_placement"))
        secondary_rows_raw = _clean(row.get("secondary_rows"))
        secondary_rows = int(secondary_rows_raw) if secondary_rows_raw else 0

        base_color_name = _clean(row.get("base_color_name")) or "Blue"

        expected_w = _clean(row.get("expected_w_px"))
        expected_h = _clean(row.get("expected_h_px"))

        screens.append(
            ScreenSpec(
                screen_name=screen_name or "SCREEN",
                tile_label=tile_label,
                rows=rows,
                cols=cols,
                default_tile_type_id=default_tile_type_id,
                secondary_tile_type_id=secondary_tile_type_id,
                secondary_placement=secondary_placement,  # type: ignore[arg-type]
                secondary_rows=secondary_rows,
                base_color_name=base_color_name,
                expected_w_px=int(expected_w) if expected_w else None,
                expected_h_px=int(expected_h) if expected_h else None,
            )
        )
    return screens
