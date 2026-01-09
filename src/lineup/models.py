from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

Placement = Literal["top", "bottom"]

@dataclass(frozen=True)
class TileType:
    tile_type_id: str
    w_px: int
    h_px: int

@dataclass(frozen=True)
class ScreenSpec:
    screen_name: str
    tile_label: str
    rows: int
    cols: int
    default_tile_type_id: str
    secondary_tile_type_id: Optional[str] = None
    secondary_placement: Optional[Placement] = None
    secondary_rows: int = 0
    base_color_name: str = "Blue"
    expected_w_px: Optional[int] = None
    expected_h_px: Optional[int] = None

def compute_row_tile_type_id(screen: ScreenSpec, row_idx: int) -> str:
    """Return the tile_type_id used for a given row (0-index)."""
    if not screen.secondary_tile_type_id or screen.secondary_rows <= 0 or not screen.secondary_placement:
        return screen.default_tile_type_id

    if screen.secondary_placement == "top":
        return screen.secondary_tile_type_id if row_idx < screen.secondary_rows else screen.default_tile_type_id

    # bottom
    return (
        screen.secondary_tile_type_id
        if row_idx >= (screen.rows - screen.secondary_rows)
        else screen.default_tile_type_id
    )

def compute_screen_resolution(screen: ScreenSpec, tiles: dict[str, TileType]) -> tuple[int, int]:
    """Compute total (width, height) in pixels for the screen."""
    # width: assume each tile in a row has same width; use the default tile width for calculation
    default_tile = tiles[screen.default_tile_type_id]
    total_w = screen.cols * default_tile.w_px

    # height: sum row heights based on tile used in each row
    total_h = 0
    for r in range(screen.rows):
        t_id = compute_row_tile_type_id(screen, r)
        total_h += tiles[t_id].h_px
    return total_w, total_h

def validate_screen_against_tiles(screen: ScreenSpec, tiles: dict[str, TileType]) -> list[str]:
    warnings: list[str] = []

    # Check tile ids exist
    if screen.default_tile_type_id not in tiles:
        warnings.append(f"Default tile type '{screen.default_tile_type_id}' not found in tile definitions")
        return warnings

    if screen.secondary_tile_type_id and screen.secondary_tile_type_id not in tiles:
        warnings.append(f"Secondary tile type '{screen.secondary_tile_type_id}' not found in tile definitions")

    if screen.secondary_rows < 0:
        warnings.append("secondary_rows cannot be negative")

    if screen.secondary_rows > screen.rows:
        warnings.append("secondary_rows exceeds total rows")

    # width consistency: ensure secondary tile width matches default
    default_w = tiles[screen.default_tile_type_id].w_px
    if screen.secondary_tile_type_id and screen.secondary_tile_type_id in tiles:
        sec_w = tiles[screen.secondary_tile_type_id].w_px
        if sec_w != default_w:
            warnings.append(
                f"Tile widths differ: default={default_w}px secondary={sec_w}px. This may create row width mismatches."
            )

    # expected resolution check
    computed_w, computed_h = compute_screen_resolution(screen, tiles)
    if screen.expected_w_px is not None and screen.expected_w_px != computed_w:
        warnings.append(f"Expected width {screen.expected_w_px}px but computed {computed_w}px")
    if screen.expected_h_px is not None and screen.expected_h_px != computed_h:
        warnings.append(f"Expected height {screen.expected_h_px}px but computed {computed_h}px")

    return warnings
