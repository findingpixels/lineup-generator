from __future__ import annotations

import glob
import os

from PyInstaller.utils.hooks import collect_all, get_package_paths

datas, binaries, hiddenimports = collect_all("PIL")

# Force-include compiled Pillow extensions (e.g., _imaging.pyd) for onefile builds.
pkg_dir = get_package_paths("PIL")[0]
for pattern in ("*.pyd", "*.dll"):
    for path in glob.glob(os.path.join(pkg_dir, pattern)):
        binaries.append((path, "PIL"))
