# Lineup Guide Generator

Generate **lineup guide** PNGs for LED screens composed of LED tiles.

Supports multiple lineup styles, Google Sheet or screen notes CSV inputs, and optional branding overlays.

**Key features:**
- Output PNG **canvas size equals the computed screen resolution** (or expected pixel size for special layouts).
- RGB tile grid with two-line tile labels and checkerboard coloring.
- Greyscale steps layout (11 bands).
- Circle X Grid layout (solid fill, grid, circle + X overlay).
- Screen overlay text (name + resolution) drawn last; toggle on/off.
- Optional branding PNG stamped along the bottom edge.
- Colors selected from a **named palette** (supports dual colors like `Red,Blue`).

## Project layout

```
lineup-generator/
  app.py                 # Streamlit UI (load screen notes, preview, export PNG)
  src/
    lineup/
      __init__.py
      models.py          # Dataclasses + validation helpers
      palette.py         # Named palette + darken utility
      renderer.py        # PNG renderer (Pillow)
      io_google.py       # Google Sheets + screen notes CSV parsing
  outputs/               # Generated PNGs (gitignored)
  tests/
    test_renderer_smoke.py
    _Screen_Notes - V1.csv
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
- load a screen notes CSV or connect a Google Sheet
- manually enter a one-off screen
- select a lineup type (RGB, Greyscale Steps, Circle X Grid)
- preview rendering
- export a single PNG or all screens to `outputs/`

## Build Windows EXE (PyInstaller)

This uses the included `LineupGenerator.windows.spec` (launcher + bundled data).

1) Create/activate a Python 3.12 venv and install dependencies:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pyinstaller
```

2) Build the exe:
```powershell
pyinstaller --noconfirm LineupGenerator.windows.spec
```

3) Run it:
```powershell
.\dist\LineupGenerator.exe
```

Notes:
- The app opens in your default browser at `http://127.0.0.1:8501`.
- Close the console window to stop the app.
- If you run into missing-file errors, rebuild from a clean venv and ensure you are using Python 3.12.

## Build macOS app (PyInstaller)

This uses `LineupGenerator.macos.spec`.

```bash
pyinstaller --noconfirm LineupGenerator.macos.spec
```

The app bundle is created in `dist/LineupGenerator.app`.

## Data sources

### Screen notes CSV / Google Sheets
This is the format exported from the "Screen Notes" sheet. Only a subset of columns is used:

- C: Screen name (PROD LABEL)
- D: Delivery label (required)
- E: Lineup color name (from the palette)
- F/G: Expected pixel width/height (required for Circle X Grid)
- N/O: Tile layout cols/rows
- Q: Half/alt tile placement (`top` or `bottom`)
- AK/AL: Single tile pixel width/height

Rows without a delivery label are ignored. If tile specs are missing, the screen is still loaded for Circle X Grid (and Greyscale if expected size is provided).

To use Google Sheets, share the sheet as "Anyone with the link" (or public) and paste the URL into the app.

## Lineup types

### RGB
- Tile grid with two-line labels: delivery label + 2-digit index.
- Checkerboard shading by row/col.
- Requires tile specs (cols/rows + tile pixel size).

### Greyscale Steps
- 11 horizontal greyscale bands.
- Uses expected pixel size when provided; otherwise uses tile specs.
- Requires either tile specs or expected pixel size.

### Circle X Grid
- Solid color background, white grid, centered circle, and X overlay.
- Requires expected pixel width/height.

## Branding overlay
- Optional PNG overlay, stamped along the bottom edge.
- Recommended 1000x1000; other sizes are scaled to fit the canvas.

## VS Codium + Codex extension workflow

A good workflow is:
1. Open the project folder in VSCodium
2. Create/select the Python interpreter from `.venv`
3. Run `streamlit run app.py` in the built-in terminal
4. Use Codex to iterate:
   - Add support for manual cell overrides via overrides.csv
   - Add serpentine indexing option
   - Match font sizing to tile size more closely

## Next steps (easy extensions)
- Manual per-cell overrides via `overrides.csv`
- Add row labels or different numbering schemes
- Add manufacturer spec import helpers
