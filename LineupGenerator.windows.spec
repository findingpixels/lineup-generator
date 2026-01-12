# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_submodules,
    copy_metadata,
    collect_data_files,
    collect_dynamic_libs,
    collect_all,
)

block_cipher = None

pil_datas, pil_binaries, pil_hidden = collect_all("PIL")
hiddenimports = collect_submodules("streamlit") + collect_submodules("PIL") + pil_hidden
hiddenimports += ["PIL._imaging", "PIL._imagingft", "PIL._imagingcms", "PIL._imagingmath"]
datas = [
    ("data", "data"),
    ("app.py", "."),
    ("src", "src"),
] + copy_metadata("streamlit") + collect_data_files("streamlit") + pil_datas
binaries = collect_dynamic_libs("PIL") + pil_binaries
try:
    import PIL
    import PIL._imaging
    import PIL._imagingcms
    import PIL._imagingft
    import PIL._imagingmath
    import PIL._imagingmorph
    import PIL._imagingtk

    pil_dir = Path(PIL.__file__).parent
    binaries.extend((str(p), "PIL") for p in pil_dir.glob("*.pyd"))
    binaries.extend((str(p), "PIL") for p in pil_dir.glob("*.dll"))
    binaries.extend(
        (str(mod.__file__), "PIL")
        for mod in (
            PIL._imaging,
            PIL._imagingcms,
            PIL._imagingft,
            PIL._imagingmath,
            PIL._imagingmorph,
            PIL._imagingtk,
        )
    )
except Exception:
    pass

a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=["hooks"],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="LineupGenerator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
