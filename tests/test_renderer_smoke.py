from src.lineup.models import ScreenSpec, TileType
from src.lineup.renderer import RenderOptions, render_lineup_png

def test_smoke_render():
    tiles = {
        "FULL": TileType(tile_type_id="FULL", w_px=216, h_px=216),
        "HALF": TileType(tile_type_id="HALF", w_px=216, h_px=108),
    }
    screen = ScreenSpec(
        screen_name="SCA",
        tile_label="SCA/E",
        rows=6,
        cols=13,
        default_tile_type_id="FULL",
        secondary_tile_type_id="HALF",
        secondary_placement="bottom",
        secondary_rows=1,
        base_color_name="Red",
        expected_w_px=2808,
        expected_h_px=1188,
    )
    img = render_lineup_png(screen, tiles, RenderOptions())
    assert img.width == 13 * 216
    assert img.height == (5 * 216) + (1 * 108)
