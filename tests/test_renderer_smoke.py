from src.lineup.io_csv import load_screens_csv, load_tiles_csv
from src.lineup.renderer import render_lineup_png, RenderOptions

def test_smoke_render():
    tiles = load_tiles_csv("tile_type_id,w_px,h_px\nFULL,216,216\nHALF,216,108\n")
    screens = load_screens_csv(
        "screen_name,tile_label,rows,cols,default_tile_type_id,secondary_tile_type_id,secondary_placement,secondary_rows,base_color_name,expected_w_px,expected_h_px\n"
        "SCA,SCA/E,6,13,FULL,HALF,bottom,1,Red,2808,1188\n"
    )
    img = render_lineup_png(screens[0], tiles, RenderOptions())
    assert img.width == 13 * 216
    assert img.height == (5 * 216) + (1 * 108)
