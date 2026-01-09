# Developer Guide

## Project architecture

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
  requirements.txt
  pyproject.toml
  .gitignore
```

The UI logic lives in `app.py`. Rendering is handled by `src/lineup/renderer.py`, with shared models in `src/lineup/models.py`. Google Sheets and screen notes CSV parsing live in `src/lineup/io_google.py`.

## VS Code + Codex workflow

1) Open the project folder in VS Code or VS Codium.
2) Select the Python interpreter from `.venv`.
3) Use the Codex plugin to inspect files, propose edits, and apply changes.
4) Run `streamlit run app.py` in the integrated terminal to test changes.

## Create and activate a virtual environment

Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Run the app:
```bash
streamlit run app.py
```

## Build Windows EXE (PyInstaller)

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

Output: `dist/LineupGenerator.exe`

## Build macOS app (PyInstaller)

```bash
pyinstaller --noconfirm LineupGenerator.macos.spec
```

Output: `dist/LineupGenerator.app`
