#  Lineup Guide Generator

Generate **lineup guide** PNGs for LED screens composed of LED tiles.

**Key requirements (MVP):**
- Output PNG **canvas size equals the exact computed screen resolution** (W×H px).
- Tiles laid out in a grid (rows/cols). Tile width is typically constant; tile height can vary (e.g., half-height rows).
- Per-tile label: **two lines** centered in each tile:
  - Line 1: `tile_label` (e.g., `SCA/E`)
  - Line 2: tile index `1..N` (left→right, top→bottom)
- Checkerboard fill based on tile index:
  - Odd tiles = darker shade
  - Even tiles = base shade
- Screen overlay text (drawn last, always on top), centered both horizontally and vertically:
  - Line 1: `screen_name` (e.g., `SCA`)
  - Line 2: `WIDTHxHEIGHT` (e.g., `2808x1296`)
- Colors selected from a **named palette** (no hex codes required).

## Project layout

```
led-lineup-generator/
  app.py                 # Streamlit UI (load CSVs, preview, export PNG)
  src/
    lineup/
      __init__.py
      models.py          # Dataclasses + validation helpers
      palette.py         # Named palette + darken utility
      renderer.py        # PNG renderer (Pillow)
      io_csv.py          # CSV loading
  data/
    tiles.sample.csv
    screens.sample.csv
  outputs/               # Generated PNGs (gitignored)
  tests/
    test_renderer_smoke.py
  requirements.txt
  pyproject.toml
  .gitignore
```

## Quick start

### 1) Create and activate a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Run the app
```bash
streamlit run app.py
```

The UI lets you:
- load `tiles.csv` and `screens.csv` (see `data/*.sample.csv`)
- select a screen
- preview rendering
- export PNG to `outputs/`

## Build Windows EXE (PyInstaller)

This uses the included `LineupGenerator.spec` (launcher + bundled data).

1) Create/activate a Python 3.12 venv and install dependencies:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pyinstaller
```

2) Build the exe:
```powershell
pyinstaller --noconfirm LineupGenerator.spec
```

3) Run it:
```powershell
.\dist\LineupGenerator.exe
```

Notes:
- The app opens in your default browser at `http://127.0.0.1:8501`.
- Close the console window to stop the app.
- If you run into missing-file errors, rebuild from a clean venv and ensure you are using Python 3.12.

## CSV formats

### `tiles.csv`
```csv
tile_type_id,w_px,h_px
FULL,216,216
HALF,216,108
```

### `screens.csv`
```csv
screen_name,tile_label,rows,cols,default_tile_type_id,secondary_tile_type_id,secondary_placement,secondary_rows,base_color_name,expected_w_px,expected_h_px
SCA,SCA/E,6,13,FULL,, ,0,Red,2808,1296
SCA_HALF,SCA/E,6,13,FULL,HALF,bottom,1,Red,2808,1188
```

Notes:
- `secondary_*` may be blank if unused.
- `secondary_placement` supports `top` or `bottom` in the MVP.
- `expected_*` are used for validation warnings in the UI (not printed on the PNG).

## VS Codium + Codex extension workflow

A good workflow is:
1. Open the project folder in VSCodium
2. Create/select the Python interpreter from `.venv`
3. Run `streamlit run app.py` in the built-in terminal
4. Use Codex to iterate:
   - “Add support for manual cell overrides via overrides.csv”
   - “Add serpentine indexing option”
   - “Match font sizing to tile size more closely”

## Next steps (easy extensions)
- Manual per-cell overrides via `overrides.csv`
- Add row labels or different numbering schemes
- Batch export all screens in a `screens.csv`
- Add manufacturer spec import helpers
