from __future__ import annotations

from dataclasses import dataclass

PaletteRGB = tuple[int, int, int]

PALETTE: dict[str, PaletteRGB] = {
    "Red": (255, 40, 40),
    "Green": (40, 200, 40),
    "Blue": (40, 80, 255),
    "Cyan": (0, 200, 200),
    "Magenta": (200, 0, 200),
    "Yellow": (220, 200, 40),
    "Orange": (255, 140, 0),
    "Teal": (0, 150, 150),
    "Gray": (150, 150, 150),
}

def darken(rgb: PaletteRGB, factor: float = 0.75) -> PaletteRGB:
    """Return a darker shade of `rgb` by multiplying channels by `factor`."""
    r, g, b = rgb
    return (max(0, min(255, int(r * factor))),
            max(0, min(255, int(g * factor))),
            max(0, min(255, int(b * factor))))
